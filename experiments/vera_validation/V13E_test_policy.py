import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from V13E_review_policy import assess

class Mock:
    def __init__(self,labels):self.labels=labels; self.calls=[]
    def score(self,text,indicator):
        self.calls.append(indicator)
        return [{k:(0.9 if k==label else 0.05) for k in ['entailment','neutral','contradiction']} for label in self.labels]

class PolicyTests(unittest.TestCase):
    def test_rule_supported_and_offsets(self):
        text='Provide your account recovery answers.'
        r=assess(text,indicators=[])['indicators']['credential_sensitive_data_request']
        self.assertEqual(r['state'],'supported')
        self.assertTrue(r['evidence'])
        self.assertTrue(all(text[x['start']:x['end']]==x['text'] for x in r['evidence']))
    def test_semantic_does_not_promote_false_positive(self):
        m=Mock(['entailment']*3)
        r=assess('This lecture discusses prize-based persuasion.',semantic=m,indicators=['reward_lure'])['indicators']['reward_lure']
        self.assertEqual(r['state'],'absent'); self.assertTrue(r['needs_review'])
    def test_semantic_does_not_veto_grounded_request(self):
        m=Mock(['neutral']*3)
        r=assess('Provide your account recovery answers.',semantic=m,indicators=['credential_sensitive_data_request'])['indicators']['credential_sensitive_data_request']
        self.assertEqual(r['state'],'supported'); self.assertTrue(r['needs_review'])
    def test_uneven_hypotheses_flagged(self):
        m=Mock(['entailment','neutral','contradiction'])
        r=assess('Complete your verification before midnight.',semantic=m,indicators=['urgency'])['indicators']['urgency']
        self.assertEqual(r['state'],'supported'); self.assertEqual(r['semantic_review'],'hypothesis_disagreement')
    def test_unavailable_does_not_call_model(self):
        m=Mock(['entailment']*3)
        r=assess('http://example.invalid',modality='standalone_url',semantic=m,indicators=['urgency'])['indicators']['urgency']
        self.assertEqual(r['state'],'unavailable'); self.assertEqual(m.calls,[])
    def test_invalid_indicator(self):
        with self.assertRaises(ValueError): assess('Hello',indicators=['fake'])
    def test_duplicate_indicator(self):
        with self.assertRaises(ValueError): assess('Hello',indicators=['urgency','urgency'])
    def test_rules_only_no_model(self):
        r=assess('Please reply tomorrow.',indicators=['urgency'])
        self.assertFalse(r['semantic_changes_final_labels'])
        self.assertNotIn('nli_scores',r['indicators']['urgency'])
if __name__=='__main__':unittest.main()
