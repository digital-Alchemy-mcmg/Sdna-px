import unittest

from sdna_px.semantic import contextual_ratio, defensible_without_retreat, hard_gate, independent_cluster_support, objective_authority, soft_interpretive_support

class SemanticCalibrationTest(unittest.TestCase):
    def test_soft_support_progression_and_ceiling(self):
        self.assertEqual(soft_interpretive_support(0), 0.0)
        self.assertEqual(soft_interpretive_support(1), 0.25)
        self.assertEqual(soft_interpretive_support(2), 0.40)
        self.assertEqual(soft_interpretive_support(3), 0.50)
        self.assertEqual(soft_interpretive_support(20), 0.50)

    def test_independent_cluster_deduplicates_sources(self):
        self.assertEqual(independent_cluster_support(["A", "A", "B"]), 0.40)

    def test_candidate_authority_is_not_penalized_for_missing_external_receipt(self):
        self.assertEqual(objective_authority(authoritative_source=True), 1.0)
        self.assertEqual(objective_authority(authoritative_source=True, contradicted=True), 0.0)

    def test_semantic_category_is_not_a_hard_gate(self):
        self.assertEqual(contextual_ratio(7.0, baseline=4.5, target_anchor=10.0), 0.7)
        self.assertFalse(hard_gate(7.0, 10.0))

    def test_below_baseline_does_not_support_category(self):
        self.assertEqual(contextual_ratio(4.49, baseline=4.5), 0.0)

    def test_surplus_is_preserved(self):
        self.assertGreater(contextual_ratio(9.0, baseline=4.5, target_anchor=6.0), 1.0)

    def test_defensibility_gate(self):
        self.assertTrue(defensible_without_retreat(supported=True))
        self.assertFalse(defensible_without_retreat(supported=True, materially_misleading=True))
        self.assertFalse(defensible_without_retreat(supported=False))

if __name__ == "__main__":
    unittest.main()
