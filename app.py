"""Streamlit dashboard for academic-paper readability and reproducibility."""

from pathlib import Path

import streamlit as st

from NLP.academic_readability import profile_academic_readability
from NLP.methodology_reproducibility import extract_methodology_reproducibility_signals


st.set_page_config(
    page_title="Automated Paper Scorer",
    page_icon="📚",
    layout="wide",
)

st.title("Automated Paper Readability & Reproducibility Scorer")
st.caption(
    "Analyze academic text for reproducibility evidence and readability "
    "indicators. Scores are heuristic and do not guarantee reproducibility."
)

uploaded_file = st.file_uploader(
    "Upload academic text",
    type=("txt", "pdf", "md", "markdown"),
    help="Supported formats: plain text, Markdown, and text-based PDFs.",
)
typed_text = st.text_area(
    "Paste academic text or an abstract",
    height=240,
    placeholder="Paste an abstract, methods section, or full paper text here...",
)


def _read_uploaded_text(upload):
    extension = Path(upload.name).suffix.lower()
    if extension == ".pdf":
        try:
            import pymupdf
        except ImportError as exc:
            raise RuntimeError(
                "PDF support requires PyMuPDF. Install project dependencies "
                "with `python -m pip install -r requirements.txt`."
            ) from exc

        document = pymupdf.open(stream=upload.getvalue(), filetype="pdf")
        try:
            return "\n".join(page.get_text() for page in document)
        finally:
            document.close()
    return upload.getvalue().decode("utf-8-sig", errors="replace")


text = typed_text.strip()
if uploaded_file is not None:
    try:
        uploaded_text = _read_uploaded_text(uploaded_file).strip()
    except Exception as exc:
        st.error(f"Could not read the uploaded file: {exc}")
        uploaded_text = ""
    if uploaded_text:
        text = uploaded_text
        st.caption(f"Analyzing uploaded file: {uploaded_file.name}")

if not text:
    st.info("Paste text or upload a file to see the scoring dashboard.")
else:
    reproducibility = extract_methodology_reproducibility_signals(text)
    readability = profile_academic_readability(text)

    score_col1, score_col2 = st.columns(2)
    score_col1.metric(
        "Reproducibility Confidence",
        f"{reproducibility['score']} / 100",
        help="Evidence-based heuristic score; presence does not validate the experiment.",
    )
    score_col2.metric(
        "Academic Readability",
        f"{readability['score']:.2f} / 100",
        help="Higher values indicate more accessible prose.",
    )

    checklist = reproducibility["checklist"]
    with st.expander("Detected artifact links and identifiers", expanded=True):
        artifacts = checklist["artifacts"]["items"]
        if artifacts:
            for artifact in artifacts:
                st.markdown(f"- **{artifact['type']}:** {artifact['identifier']}")
        else:
            st.write("No supported repository or artifact links detected.")
        st.caption(
            f"Artifact evidence: {reproducibility['score_breakdown']['artifacts']['points']}"
            " / 25 points"
        )

    with st.expander("Hyperparameter signals", expanded=True):
        parameters = checklist["hyperparameters"]
        if parameters["items"]:
            for name, value in parameters["items"].items():
                st.markdown(f"- **{name.replace('_', ' ').title()}:** {value}")
        else:
            st.write("No supported hyperparameter values detected.")
        if parameters["missing"]:
            st.caption("Not detected: " + ", ".join(parameters["missing"]))
        st.caption(
            f"Hyperparameter evidence: "
            f"{reproducibility['score_breakdown']['hyperparameters']['points']} / 30 points"
        )

    with st.expander("Compute and environment indicators", expanded=True):
        compute = checklist["compute_resources"]
        environment = checklist["environment_dependencies"]
        st.markdown("**Compute resources**")
        st.write(
            "Hardware: " + (", ".join(compute["hardware"]) or "not detected")
        )
        st.write(
            "Memory: " + (", ".join(compute["memory"]) or "not detected")
        )
        st.markdown("**Environment dependencies**")
        if environment["items"]:
            for name, version in environment["items"].items():
                st.markdown(f"- **{name.title()}:** {version}")
        else:
            st.write("No Python, PyTorch, or TensorFlow version detected.")
        seed_items = checklist["random_seed"]["items"]
        st.write("Random seed: " + (", ".join(seed_items) or "not detected"))
        with st.expander("Reproducibility score breakdown"):
            for name, details in reproducibility["score_breakdown"].items():
                st.write(
                    f"{name.replace('_', ' ').title()}: "
                    f"{details['points']} / {details['possible']}"
                )

    with st.expander("Readability diagnostics", expanded=True):
        metrics = readability["metrics"]
        metric_columns = st.columns(3)
        for column, label, key in zip(
            metric_columns,
            ("Flesch-Kincaid Grade Level", "Gunning Fog Index", "Coleman-Liau Index"),
            ("flesch_kincaid_grade_level", "gunning_fog_index", "coleman_liau_index"),
        ):
            column.metric(label, f"{metrics[key]:.2f}")

        st.markdown("**Structural and lexical metrics**")
        st.write(f"Word count: {metrics['word_count']}")
        st.write(f"Sentence count: {metrics['sentence_count']}")
        st.write(f"Average sentence length: {metrics['average_sentence_length']:.2f} words")
        st.write(
            f"Technical jargon density: {metrics['technical_jargon_density']:.1%} "
            f"({metrics['technical_jargon_count']} terms)"
        )
        st.write(f"Clause entropy: {metrics['clause_entropy_bits']:.3f} bits")
        st.write(
            f"Passive voice frequency: {metrics['passive_voice_frequency']:.1%} "
            f"({metrics['passive_sentence_count']} sentences)"
        )
        st.markdown("**Clarity diagnostics**")
        for diagnostic in readability["diagnostics"]:
            st.write(f"- {diagnostic}")

        with st.expander("Formula accessibility and clarity components"):
            st.write("Formula-based accessibility (0–100):")
            st.json(readability["formula_accessibility_scores"])
            st.write("Structural clarity (0–100):")
            st.json(readability["clarity_components"])
