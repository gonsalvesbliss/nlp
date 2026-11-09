# Paper Readability & Reproducibility Scorer

The project extracts basic PDF features and scores research-paper text for
reproducibility evidence and academic readability.

## Run the demo

Install the project dependencies and run the standalone sample report:

```powershell
python -m pip install -r requirements.txt
python run_scorer_demo.py
```

The demo exercises the existing PDF extraction and baseline scoring modules,
then reports results from the new scorers. It creates and removes a temporary
sample PDF automatically.

## Scoring modules

- `NLP/methodology_reproducibility.py` detects repository and artifact links,
  DOI identifiers, hyperparameters, compute details, random seeds, and common
  runtime dependencies. `extract_methodology_reproducibility_signals(text)`
  returns a 0–100 evidence score, score breakdown, and presence checklist.
  The evidence weights are artifacts (25), hyperparameters (30), compute
  resources (15), random seed (10), and environment dependencies (20).
- `NLP/academic_readability.py` reports Flesch-Kincaid, Gunning Fog, and
  Coleman-Liau grade estimates, as well as jargon density, sentence length,
  clause entropy, and passive-voice frequency. The profile's 0–100 score is
  oriented so higher means more accessible prose, combining classic-formula
  accessibility (55%) and structural/lexical clarity (45%).
- `NLP/mem1.py`, `NLP/mem2.py`, and `NLP/mem3.py` retain the existing PDF,
  signal-extraction, and baseline scoring interfaces.

The new scorers use Python's standard library and require no downloaded NLP
corpora. Their lexical, syllable, clause, and passive-voice measurements are
heuristics; they assess evidence and textual patterns rather than validating
experimental results.

The existing Streamlit application can still be started from the `NLP`
directory with `streamlit run mem4.py`.
