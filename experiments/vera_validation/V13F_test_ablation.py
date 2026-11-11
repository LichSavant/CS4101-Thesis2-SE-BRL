import unittest
from pathlib import Path
from V13F_ablation_audit import summarize_semantic, load_cases, run

HERE=Path(__file__).resolve().parent
class TestAblation(unittest.TestCase):
    def test_votes_not_probability(self):
        scores=[{'entailment':.9,'neutral':.05,'contradiction':.05},
                {'entailment':.1,'neutral':.8,'contradiction':.1},
                {'entailment':.2,'neutral':.7,'contradiction':.1}]
        summary=summarize_semantic(scores)
        self.assertEqual(summary['entailment_votes'],1)
        self.assertAlmostEqual(summary['entailment_spread'],.8)
    def test_v10_all_rows(self):
        result=run('v10')
        self.assertEqual(result['count'],20)
        self.assertEqual(result['rules_successes'],19)
        self.assertFalse(result['nli_changes_labels'])
    def test_v11_all_pairs(self):
        result=run('v11')
        self.assertEqual(result['count'],20)
        self.assertEqual(result['rules_successes'],20)
    def test_semantic_does_not_override(self):
        class Fake:
            def score(self,text,indicator):
                return [{'hypothesis':'x','entailment':.95,'neutral':.025,'contradiction':.025}]*3
        result=run('v10',semantic=Fake(),limit=1)
        self.assertEqual(result['count'],1)
        self.assertFalse(result['nli_changes_labels'])
        self.assertEqual(result['results'][0]['decision']['semantic_diagnostic']['entailment_votes'],3)
    def test_schema(self):
        self.assertEqual(len(load_cases(HERE/'counterfactual_pairs.csv','v11')),20)
if __name__=='__main__': unittest.main()
