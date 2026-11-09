"""Run the legacy and extended paper scorers against an example abstract."""

from pathlib import Path
import tempfile

import pymupdf

from NLP.academic_readability import profile_academic_readability
from NLP.mem1 import extract_basic_features
from NLP.mem2 import extract_reproducibility_signals
from NLP.mem3 import calculate_reproducibility_score
from NLP.methodology_reproducibility import extract_methodology_reproducibility_signals


SAMPLE_TEXT = """
We evaluate a transformer model using PyTorch 2.2 and Python 3.11. The learning
rate is 3e-5, batch size is 32, and training used 8 epochs with the AdamW
optimizer. Experiments used one NVIDIA A100 GPU with 40 GB memory, and the
random seed was 42. The repository is available at
https://github.com/example/reproducible-paper, and the dataset is archived at
https://zenodo.org/records/1234567 (DOI: 10.5281/zenodo.1234567). Results are
reported in Table 1. The model was trained on the same fixed data split, which
allows the results to be compared across repeated runs.
""".strip()


def _create_sample_pdf(path):
    document = pymupdf.open()
    try:
        page = document.new_page()
        bounds = page.rect + (36, 36, -36, -36)
        page.insert_textbox(bounds, SAMPLE_TEXT, fontsize=10)
        document.save(path)
    finally:
        document.close()


def main():
    with tempfile.TemporaryDirectory(prefix="paper-scorer-") as temp_dir:
        sample_pdf = Path(temp_dir) / "sample_paper.pdf"
        _create_sample_pdf(sample_pdf)
        basic_features = extract_basic_features(str(sample_pdf))

    paper_text = basic_features["full_text"].strip()
    if not paper_text:
        raise RuntimeError("The PDF text extractor returned no sample text.")

    legacy_signals = extract_reproducibility_signals(paper_text)
    legacy_score, _ = calculate_reproducibility_score(basic_features, legacy_signals)
    reproducibility = extract_methodology_reproducibility_signals(paper_text)
    readability = profile_academic_readability(paper_text)
    metrics = readability["metrics"]

    print("=" * 68)
    print("PAPER READABILITY & REPRODUCIBILITY SCORER")
    print("=" * 68)
    print(f"PDF extraction: {basic_features['pages']} page(s), "
          f"{basic_features['tables_count']} table reference(s)")
    print(f"Legacy reproducibility score: {legacy_score}/100")
    print(f"Methodology & reproducibility confidence: {reproducibility['score']}/100")
    print(f"Academic readability score: {readability['score']}/100")
    print("\nReproducibility checklist:")
    for name, item in reproducibility["checklist"].items():
        status = "present" if item["present"] else "not found"
        print(f"  - {name.replace('_', ' ').title()}: {status}")
    print("\nReadability diagnostics:")
    print(f"  - Flesch-Kincaid grade level: {metrics['flesch_kincaid_grade_level']}")
    print(f"  - Gunning Fog index: {metrics['gunning_fog_index']}")
    print(f"  - Coleman-Liau index: {metrics['coleman_liau_index']}")
    print(f"  - Average sentence length: {metrics['average_sentence_length']} words")
    print(f"  - Technical jargon density: {metrics['technical_jargon_density']:.1%}")
    print(f"  - Clause entropy: {metrics['clause_entropy_bits']} bits")
    print(f"  - Passive voice frequency: {metrics['passive_voice_frequency']:.1%}")
    for diagnostic in readability["diagnostics"]:
        print(f"  - {diagnostic}")
    print("\nScores are heuristic indicators, not guarantees of reproducibility or quality.")


if __name__ == "__main__":
    main()
