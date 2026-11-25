import pathlib,json,hashlib,subprocess
E=pathlib.Path('/results');F=pathlib.Path('/opt/csr-group4-experiment/frozen');results=[]
for r in json.loads((E/'classification.json').read_text()):
 p=E/'data'/(r['name']+'.csr');assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
 hashes=[]
 for v in ['o3','pgo','new','old']:
  y=E/(r['name']+'-'+v+'.y');subprocess.run([str(F/v),str(p),'1','61331',str(y)],check=True,stdout=subprocess.DEVNULL);hashes.append(hashlib.sha256(y.read_bytes()).hexdigest())
 assert all(h==r['output_sha256'] for h in hashes)
 results.append({'name':r['name'],'data_sha256_matches':True,'four_full_vector_sha256_match_local':True})
(E/'server-correctness.json').write_text(json.dumps(results,indent=2));print('server full vector checks passed',len(results))
