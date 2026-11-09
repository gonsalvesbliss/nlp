"""Dependency-free readability and structural-complexity profiling."""

import math
import re


_WORD_RE = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*", re.UNICODE)
_SENTENCE_RE = re.compile(r"[^.!?]+(?:[.!?]+|$)")
_CLAUSE_MARKER_RE = re.compile(
    r"\b(?:and|but|or|because|although|though|whereas|while|if|when|"
    r"since|which|that|who|whom|whose)\b",
    re.IGNORECASE,
)
_PASSIVE_RE = re.compile(
    r"\b(?:am|is|are|was|were|be|been|being)\s+"
    r"(?:\w+ed|known|given|shown|seen|made|found|built|written|taken|done)\b",
    re.IGNORECASE,
)
_JARGON_TERMS = {
    "ablation", "autoregressive", "backpropagation", "benchmark", "convolutional",
    "embedding", "encoder", "fine-tuning", "generalization", "gradient",
    "hyperparameter", "inference", "latent", "logits", "loss", "multimodal",
    "neural", "optimization", "parameterization", "regularization", "tokenization",
    "transformer", "variational",
}


def _syllable_count(word):
    """Estimate English syllables without downloading a pronunciation corpus."""
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    groups = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e") and not word.endswith(("le", "ye")) and groups > 1:
        groups -= 1
    if word.endswith("es") and not word.endswith(("ses", "xes", "zes")) and groups > 1:
        groups -= 1
    return max(1, groups)


def _bounded_score(value):
    return max(0.0, min(100.0, value))


def _grade_accessibility(grade):
    return _bounded_score(100.0 * (1.0 - max(0.0, min(20.0, grade)) / 20.0))


def profile_academic_readability(text):
    """Calculate classic readability formulas and academic clarity diagnostics.

    All values are heuristics. The returned academic score is normalized so
    that higher values indicate more accessible prose.
    """
    text = text or ""
    words = _WORD_RE.findall(text)
    sentences = [part.strip() for part in _SENTENCE_RE.findall(text) if _WORD_RE.search(part)]
    if words and not sentences:
        sentences = [text]

    word_count = len(words)
    sentence_count = len(sentences)
    syllables = sum(_syllable_count(word) for word in words)
    complex_words = sum(_syllable_count(word) >= 3 for word in words)
    average_sentence_length = word_count / sentence_count if sentence_count else 0.0
    average_syllables_per_word = syllables / word_count if word_count else 0.0
    letters = sum(len(re.sub(r"[^\w]", "", word)) for word in words)
    words_per_hundred = word_count / 100.0
    letters_per_hundred_words = letters / words_per_hundred if words_per_hundred else 0.0
    sentences_per_hundred_words = sentence_count / words_per_hundred if words_per_hundred else 0.0

    flesch_kincaid = (
        0.39 * average_sentence_length
        + 11.8 * average_syllables_per_word
        - 15.59
        if word_count
        else 0.0
    )
    gunning_fog = (
        0.4 * (average_sentence_length + 100.0 * complex_words / word_count)
        if word_count
        else 0.0
    )
    coleman_liau = (
        0.0588 * letters_per_hundred_words
        - 0.296 * sentences_per_hundred_words
        - 15.8
        if word_count
        else 0.0
    )

    jargon_count = sum(
        1 for word in words
        if word.lower().replace("’", "'") in _JARGON_TERMS
    )
    long_word_count = sum(len(re.sub(r"[^\w]", "", word)) >= 8 for word in words)
    jargon_density = jargon_count / word_count if word_count else 0.0
    long_word_density = long_word_count / word_count if word_count else 0.0

    clause_counts = [1 + len(_CLAUSE_MARKER_RE.findall(sentence)) for sentence in sentences]
    clause_distribution = {}
    for count in clause_counts:
        clause_distribution[count] = clause_distribution.get(count, 0) + 1
    clause_entropy = 0.0
    if sentence_count:
        for count in clause_distribution.values():
            probability = count / sentence_count
            clause_entropy -= probability * math.log2(probability)
    average_clauses = sum(clause_counts) / sentence_count if sentence_count else 0.0

    passive_sentences = sum(bool(_PASSIVE_RE.search(sentence)) for sentence in sentences)
    passive_frequency = passive_sentences / sentence_count if sentence_count else 0.0

    classic_scores = {
        "flesch_kincaid_accessibility": _grade_accessibility(flesch_kincaid) if word_count else 0.0,
        "gunning_fog_accessibility": _grade_accessibility(gunning_fog) if word_count else 0.0,
        "coleman_liau_accessibility": _grade_accessibility(coleman_liau) if word_count else 0.0,
    }
    classic_accessibility = sum(classic_scores.values()) / len(classic_scores)
    sentence_length_clarity = _bounded_score(100.0 - abs(average_sentence_length - 18.0) * 3.0)
    lexical_clarity = _bounded_score(
        100.0 - jargon_density * 350.0 - long_word_density * 80.0
    )
    clause_clarity = _bounded_score(100.0 - abs(average_clauses - 1.5) * 35.0)
    entropy_clarity = _bounded_score(100.0 - abs(clause_entropy - 1.0) * 35.0)
    passive_clarity = _bounded_score(100.0 - passive_frequency * 100.0)
    clarity_components = {
        "sentence_length": sentence_length_clarity,
        "lexical_complexity": lexical_clarity,
        "clause_complexity": clause_clarity,
        "clause_entropy": entropy_clarity,
        "passive_voice": passive_clarity,
    }
    if not word_count:
        clarity_components = {name: 0.0 for name in clarity_components}
    structural_clarity = sum(clarity_components.values()) / len(clarity_components)
    academic_score = (
        _bounded_score(0.55 * classic_accessibility + 0.45 * structural_clarity)
        if word_count
        else 0.0
    )

    if not word_count:
        diagnostics = ["No prose detected; readability metrics are unavailable."]
    else:
        diagnostics = []
        if average_sentence_length > 30:
            diagnostics.append("Long sentences may hinder clarity.")
        if jargon_density > 0.08:
            diagnostics.append("Technical terminology is dense.")
        if passive_frequency > 0.3:
            diagnostics.append("Passive constructions are frequent.")
        if not diagnostics:
            diagnostics.append("No major readability warning detected by these heuristics.")

    return {
        "score": round(academic_score, 2),
        "metrics": {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "average_sentence_length": round(average_sentence_length, 2),
            "average_syllables_per_word": round(average_syllables_per_word, 2),
            "flesch_kincaid_grade_level": round(flesch_kincaid, 2),
            "gunning_fog_index": round(gunning_fog, 2),
            "coleman_liau_index": round(coleman_liau, 2),
            "technical_jargon_count": jargon_count,
            "technical_jargon_density": round(jargon_density, 4),
            "long_word_density": round(long_word_density, 4),
            "average_clauses_per_sentence": round(average_clauses, 2),
            "clause_entropy_bits": round(clause_entropy, 3),
            "passive_sentence_count": passive_sentences,
            "passive_voice_frequency": round(passive_frequency, 4),
        },
        "formula_accessibility_scores": {
            name: round(value, 2) for name, value in classic_scores.items()
        },
        "clarity_components": {
            name: round(value, 2) for name, value in clarity_components.items()
        },
        "diagnostics": diagnostics,
    }


def calculate_academic_readability(text):
    """Alias for callers that prefer a calculation-oriented function name."""
    return profile_academic_readability(text)
