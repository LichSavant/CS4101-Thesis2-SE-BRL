import unittest
from V13D_hybrid_extractor import rules_only, extract

class ExtractorTests(unittest.TestCase):
    def check(self,text,indicator,state):
        self.assertEqual(rules_only(text)[indicator]['state'],state)
    def test_12_indicators_present(self):
        self.assertEqual(len(rules_only('Please review your account.')),12)
    def test_urgency(self):self.check('Please submit before midnight.','urgency','supported')
    def test_fear(self):self.check('Your account will be disabled unless you respond.','fear_threat','supported')
    def test_scarcity(self):self.check('Only three seats remain.','scarcity','supported')
    def test_curiosity(self):self.check('Check this out!','curiosity','supported')
    def test_reward(self):self.check('Register to receive a complimentary ticket.','reward_lure','supported')
    def test_authority(self):self.check('I am your manager. Submit it.','authority','supported')
    def test_impersonation_unavailable(self):self.check('I am your bank.','impersonation','unavailable')
    def test_brand_unavailable(self):self.check('Trusted brand says hello.','brand_exploitation','unavailable')
    def test_confidentiality(self):self.check('Keep this private.','confidentiality_isolation','supported')
    def test_action(self):self.check('Please download the form.','call_to_action','supported')
    def test_credential(self):self.check('Provide your account password.','credential_sensitive_data_request','supported')
    def test_finance(self):self.check('Transfer money to this account.','financial_action_request','supported')
    def test_education(self):self.check('The lesson explains the word urgent.','urgency','absent')
    def test_negation(self):self.check('Never send your password to anyone.','credential_sensitive_data_request','absent')
    def test_url(self):
        self.assertTrue(all(x['state']=='unavailable' for x in rules_only('https://sample.org','standalone_url').values()))
    def test_offsets(self):
        t='Please submit before midnight.'
        for e in rules_only(t)['urgency']['evidence']:
            self.assertEqual(t[e['start']:e['end']],e['text'])
    def test_no_fake_evidence(self):
        for x in rules_only('This handbook explains prize-based persuasion.').values():
            self.assertFalse(x['evidence'])
    def test_review_flags_mock(self):
        class Fake:
            def score(self,text,indicator):
                return [{'hypothesis':'test','entailment':.9,'neutral':.05,'contradiction':.05}]
        out=extract('Please read this.',semantic=Fake())
        self.assertEqual(out['mode'],'hybrid_review_only')
        self.assertTrue(out['indicators']['urgency']['needs_review'])
        self.assertEqual(out['indicators']['urgency']['state'],'absent')

if __name__=='__main__':unittest.main()
