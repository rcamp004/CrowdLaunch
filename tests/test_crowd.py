import copy
import datetime as dt
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from crowd import validate, reconcile, summarize
Q=json.loads((Path(__file__).resolve().parents[1]/'config/questions.json').read_text())[0]
P={'version':1,'question_id':Q['id'],'vote':'GO','p_go':80,'reason':'Operator evidence supports liftoff.','source_url':'https://example.com/evidence'}
NOW=dt.datetime(2026,9,12,tzinfo=dt.timezone.utc)
def issue(n=1,p=None,at='2026-09-08T12:00:00Z',user=12):
 return {'number':n,'title':'[CrowdLaunch forecast] test','body':'```json\n'+json.dumps(p or P)+'\n```','updated_at':at,'user':{'id':user,'login':'tester','type':'User'},'labels':[]}
class ForecastTests(unittest.TestCase):
 def test_go_only_has_no_invented_loss(self):
  records,_=reconcile([issue()],[],[Q],NOW)
  s=summarize(records,Q)
  self.assertEqual(s['n'],1);self.assertEqual(s['loss_n'],0);self.assertNotIn('conditional_loss_rate',s)
 def test_probability_validation(self):
  for value in [-1,101,float('nan'),float('inf'),True,'90']:
   with self.subTest(value=value),self.assertRaises(ValueError):validate(P|{'p_go':value},Q,'2026-09-08T00:00:00Z')
  with self.assertRaises(ValueError):validate(P|{'p_total_loss':50},Q,'2026-09-08T00:00:00Z')
  with self.assertRaises(ValueError):validate(P|{'p_total_loss':90,'p_partial_loss':20,'partial_severity':30},Q,'2026-09-08T00:00:00Z')
 def test_window_enforced(self):
  for t in ['2026-09-06T23:59:59Z',Q['closes_at']]:
   with self.assertRaises(ValueError):validate(P,Q,t)
 def test_latest_account_only_and_products_before_average(self):
  p=P|{'p_total_loss':10,'p_partial_loss':20,'partial_severity':50,'p_go':100}
  p2=p|{'p_go':0,'p_total_loss':80,'p_partial_loss':0}
  rows,_=reconcile([issue(1,p,user=1),issue(2,p2,user=2),issue(3,p,at='2026-09-09T00:00:00Z',user=1)],[],[Q],NOW)
  s=summarize(rows,Q)
  self.assertEqual(s['n'],2);self.assertAlmostEqual(s['conditional_loss_rate'],.5);self.assertAlmostEqual(s['window_loss_rate'],.1)
 def test_late_edits_preserve_observed_forecast(self):
  rows,_=reconcile([issue()],[],[Q],NOW)
  late=issue(p=P|{'p_go':0},at='2026-09-11T00:00:00Z')
  rows,_=reconcile([late],rows,[Q],NOW)
  self.assertEqual(rows[0]['p_go'],80)
  self.assertEqual(reconcile([late],[],[Q],NOW)[0],[])
 def test_exclusion_and_deletion(self):
  rows,_=reconcile([issue()],[],[Q],NOW)
  excluded=issue();excluded['labels']=[{'name':'crowd-exclude'}]
  self.assertEqual(reconcile([excluded],rows,[Q],NOW)[0],[])
  self.assertEqual(reconcile([],rows,[Q],NOW)[0],[])
 def test_malformed_and_bot_not_counted(self):
  bad=issue();bad['body']='not json'
  bot=issue(2);bot['user']['type']='Bot'
  rows,errors=reconcile([bad,bot],[],[Q],NOW)
  self.assertEqual(rows,[]);self.assertEqual(len(errors),1)
 def test_brier_needs_sourced_outcome(self):
  rows,_=reconcile([issue()],[],[Q],NOW)
  self.assertNotIn('go_brier',summarize(rows,Q))
  self.assertAlmostEqual(summarize(rows,Q|{'resolution':{'go':1,'source_url':'https://example.com'}})['go_brier'],.04)
if __name__=='__main__':unittest.main()
