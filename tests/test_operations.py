import importlib.util,tempfile,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Operations(unittest.TestCase):
 def test_bootstrap_is_private_and_non_destructive(self):
  m=module('bootstrap')
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'runtime';m.bootstrap(root,'https://id.example.test','https://flights.example.test','owner@example.test')
   cfg=json.loads((root/'casdoor/init.json').read_text());apps={a['name']:a for a in cfg['applications']}
   self.assertFalse(apps['flightwatch-web']['enableSignUp'])
   self.assertIn('urn:ietf:params:oauth:grant-type:device_code',apps['flightwatch-cli']['grantTypes'])
   self.assertFalse(cfg['users'][0]['emailVerified'])
   self.assertEqual((root/'credentials.json').stat().st_mode & 0o777,0o600)
   with self.assertRaises(ValueError):m.bootstrap(root,'https://id.example.test','https://flights.example.test','owner@example.test')
 def test_retention_daily_and_weekly(self):
  m=module('backup')
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for day in range(1,32):(root/f'202607{day:02d}T000000Z.tar.age').touch()
   (root/'do-not-delete.txt').touch();m.retain(root)
   kept=list(root.glob('*.tar.age'));self.assertGreaterEqual(len(kept),7);self.assertLessEqual(len(kept),11)
   for day in range(25,32):self.assertTrue((root/f'202607{day:02d}T000000Z.tar.age').exists())
   self.assertTrue((root/'do-not-delete.txt').exists())
if __name__=='__main__':unittest.main()
