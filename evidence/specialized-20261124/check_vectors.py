import pathlib,subprocess,json,hashlib
R=pathlib.Path('/results');V=R/'server-vectors';V.mkdir(exist_ok=False);B=pathlib.Path('/opt/csr-group4-experiment/frozen');out={}
for n in ['bcsstk14','bcsstk15','bcsstk16']:
 ys=[]
 for v in ['o3','pgo','new','old']:
  dst=V/(n+'-'+v+'.y');subprocess.run([str(B/v),str(R/'data'/(n+'.csr')),'1','61331',str(dst)],check=True,stdout=subprocess.DEVNULL);ys.append(dst.read_bytes())
 assert all(x==ys[0] for x in ys);h=hashlib.sha256(ys[0]).hexdigest();assert h==json.loads((R/(n+'-metadata.json')).read_text())['output_sha256'];out[n]={'full_vectors_equal_on_server':True,'full_vector_sha256_matches_local':h}
(R/'server-vector-checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
