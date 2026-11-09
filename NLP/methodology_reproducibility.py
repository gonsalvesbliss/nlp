"""Heuristic extraction of methodology and reproducibility evidence."""

import re
from urllib.parse import urlparse


_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s<>\"']+", re.IGNORECASE)
_TRAILING_PUNCTUATION = ".,;:!?)]}"
_ARTIFACT_HOSTS = {
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "huggingface.co": "Hugging Face",
    "hf.co": "Hugging Face",
    "openreview.net": "OpenReview",
    "zenodo.org": "Zenodo",
    "doi.org": "DOI",
    "dx.doi.org": "DOI",
}
_NUMBER_PATTERN = r"(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?"

_HYPERPARAMETER_PATTERNS = {
    "learning_rate": re.compile(
        r"\b(?:learning[\s_-]*rate|lr)\b\s*(?:(?:of|is)\s*)?"
        r"(?:[:=]\s*)?" + _NUMBER_PATTERN,
        re.IGNORECASE,
    ),
    "batch_size": re.compile(
        r"\b(?:batch[\s_-]*size|mini[\s_-]*batch(?:[\s_-]*size)?)\b"
        r"\s*(?:(?:of|is)\s*)?(?:[:=]\s*)?\d+",
        re.IGNORECASE,
    ),
    "epochs": re.compile(
        r"(?:\b(?:epochs?|training[\s_-]*epochs?)\b"
        r"\s*(?:(?:of|is)\s*)?(?:[:=]\s*)?\d+\b|\b\d+\s+epochs?\b)",
        re.IGNORECASE,
    ),
    "optimizer": re.compile(
        r"\b(?:optimizer|optimiser)\b\s*(?:(?:was|is|of)\s*)?[:=]?\s*"
        r"(?:adamw?|sgd|rmsprop|adagrad|adafactor|lion|lamb)\b",
        re.IGNORECASE,
    ),
}
_OPTIMIZER_NAMES = re.compile(
    r"\b(?:AdamW?|SGD|RMSprop|Adagrad|Adafactor|Lion|LAMB)\b",
    re.IGNORECASE,
)
_HARDWARE_RE = re.compile(
    r"\b(?:GPU|TPU|CPU|NVIDIA|V100|A100|H100|RTX\s?\d{3,4}|"
    r"MI\d{2,3}|TPU\s?v?\d+|cores?)\b",
    re.IGNORECASE,
)
_MEMORY_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:GB|GiB|MB|MiB)\s*"
    r"(?:of\s*)?(?:GPU\s*)?(?:VRAM|memory|RAM)?\b",
    re.IGNORECASE,
)
_SEED_RE = re.compile(
    r"\b(?:random[\s_-]*)?seed(?:s)?\b\s*(?:(?:was|is|of)\s*)?[:=]?\s*\d+\b",
    re.IGNORECASE,
)
_PYTHON_RE = re.compile(r"\bPython\s*(?:version\s*)?([0-9]+(?:\.[0-9]+){1,2})\b", re.IGNORECASE)
_TORCH_RE = re.compile(
    r"\b(?:PyTorch|torch)(?:\s*(?:version\s*)?([0-9]+(?:\.[0-9]+){0,2}))?\b",
    re.IGNORECASE,
)
_TENSORFLOW_RE = re.compile(
    r"\bTensorFlow(?:\s*(?:version\s*)?([0-9]+(?:\.[0-9]+){0,2}))?\b",
    re.IGNORECASE,
)


def _unique(values):
    return list(dict.fromkeys(values))


def _clean_match(value):
    return value.rstrip(_TRAILING_PUNCTUATION)


def _find_artifacts(text):
    artifacts = []
    seen = set()

    for raw_url in _URL_RE.findall(text):
        url = _clean_match(raw_url)
        hostname = (urlparse(url).hostname or "").lower()
        category = _ARTIFACT_HOSTS.get(hostname)
        if category and url not in seen:
            artifacts.append({"type": category, "identifier": url})
            seen.add(url)

    for raw_doi in _DOI_RE.findall(text):
        doi = _clean_match(raw_doi)
        normalized = doi.lower()
        already_in_url = any(
            item["type"] == "DOI"
            and item["identifier"].lower().endswith(normalized)
            for item in artifacts
        )
        if normalized not in seen and not already_in_url:
            artifacts.append({"type": "DOI", "identifier": doi})
            seen.add(normalized)

    return artifacts


def extract_methodology_reproducibility_signals(text):
    """Return artifact references, evidence checklist, and a 0-100 score.

    This is a rule-based evidence score: it measures whether signals are
    mentioned, not whether an experiment is independently reproducible.
    """
    text = text or ""
    artifacts = _find_artifacts(text)

    hyperparameters = {}
    for name, pattern in _HYPERPARAMETER_PATTERNS.items():
        match = pattern.search(text)
        if match:
            hyperparameters[name] = match.group(0).strip()
    if "optimizer" not in hyperparameters:
        optimizer_match = _OPTIMIZER_NAMES.search(text)
        if optimizer_match:
            hyperparameters["optimizer"] = optimizer_match.group(0)

    hardware = _unique(match.group(0) for match in _HARDWARE_RE.finditer(text))
    memory = _unique(match.group(0) for match in _MEMORY_RE.finditer(text))
    seeds = _unique(match.group(0) for match in _SEED_RE.finditer(text))

    environment = {}
    python_match = _PYTHON_RE.search(text)
    if python_match:
        environment["python"] = python_match.group(1)
    torch_match = _TORCH_RE.search(text)
    if torch_match:
        environment["pytorch"] = torch_match.group(1) or "mentioned"
    tensorflow_match = _TENSORFLOW_RE.search(text)
    if tensorflow_match:
        environment["tensorflow"] = tensorflow_match.group(1) or "mentioned"

    artifact_points = 25 if artifacts else 0
    hyperparameter_points = round(30 * len(hyperparameters) / len(_HYPERPARAMETER_PATTERNS))
    compute_points = round(15 * (bool(hardware) + bool(memory)) / 2)
    seed_points = 10 if seeds else 0
    environment_points = round(20 * min(len(environment), 2) / 2)
    breakdown = {
        "artifacts": {"points": artifact_points, "possible": 25},
        "hyperparameters": {"points": hyperparameter_points, "possible": 30},
        "compute_resources": {"points": compute_points, "possible": 15},
        "random_seed": {"points": seed_points, "possible": 10},
        "environment_dependencies": {"points": environment_points, "possible": 20},
    }

    checklist = {
        "artifacts": {
            "present": bool(artifacts),
            "items": artifacts,
        },
        "hyperparameters": {
            "present": bool(hyperparameters),
            "items": hyperparameters,
            "missing": [name for name in _HYPERPARAMETER_PATTERNS if name not in hyperparameters],
        },
        "compute_resources": {
            "present": bool(hardware or memory),
            "hardware": hardware,
            "memory": memory,
        },
        "random_seed": {
            "present": bool(seeds),
            "items": seeds,
        },
        "environment_dependencies": {
            "present": bool(environment),
            "items": environment,
            "detected": list(environment),
        },
    }

    return {
        "score": sum(item["points"] for item in breakdown.values()),
        "checklist": checklist,
        "score_breakdown": breakdown,
    }


def extract_reproducibility_profile(text):
    """Alias with a concise name for applications consuming a profile."""
    return extract_methodology_reproducibility_signals(text)
