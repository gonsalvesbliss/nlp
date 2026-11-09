import unittest

from NLP.academic_readability import profile_academic_readability
from NLP.methodology_reproducibility import extract_methodology_reproducibility_signals


class ReproducibilityScorerTests(unittest.TestCase):
    def test_extracts_expected_evidence_and_full_score(self):
        text = (
            "The learning rate is 3e-5, batch size is 32, and training used "
            "8 epochs with the AdamW optimizer. Runs used one NVIDIA A100 GPU "
            "with 40 GB memory and random seed 42. We used PyTorch 2.2 on "
            "Python 3.11. Code: https://github.com/example/project; "
            "paper DOI: 10.5281/zenodo.12345."
        )

        result = extract_methodology_reproducibility_signals(text)

        self.assertEqual(result["score"], 100)
        self.assertEqual(
            set(result["checklist"]["hyperparameters"]["items"]),
            {"learning_rate", "batch_size", "epochs", "optimizer"},
        )
        self.assertTrue(result["checklist"]["artifacts"]["present"])
        self.assertTrue(result["checklist"]["compute_resources"]["present"])
        self.assertTrue(result["checklist"]["random_seed"]["present"])
        self.assertTrue(result["checklist"]["environment_dependencies"]["present"])

    def test_no_evidence_returns_zero_score(self):
        result = extract_methodology_reproducibility_signals("We report our findings.")
        self.assertEqual(result["score"], 0)
        self.assertTrue(all(not item["present"] for item in result["checklist"].values()))


class AcademicReadabilityTests(unittest.TestCase):
    def test_returns_normalized_score_and_requested_diagnostics(self):
        result = profile_academic_readability(
            "The model was trained using a transformer. We evaluate the benchmark "
            "and report the results, which are reproducible."
        )

        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        self.assertIn("flesch_kincaid_grade_level", result["metrics"])
        self.assertIn("gunning_fog_index", result["metrics"])
        self.assertIn("coleman_liau_index", result["metrics"])
        self.assertIn("clause_entropy_bits", result["metrics"])
        self.assertGreater(result["metrics"]["passive_voice_frequency"], 0)

    def test_empty_text_is_safe_and_scores_zero(self):
        result = profile_academic_readability("")
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["metrics"]["word_count"], 0)
        self.assertTrue(result["diagnostics"])


if __name__ == "__main__":
    unittest.main()
