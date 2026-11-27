import pathlib,subprocess,json,hashlib,struct
P=pathlib.Path('/opt/csr-group4-experiment/frozen');R=pathlib.Path('/results');D=pathlib.Path('/opt/csr-group4-experiment/data')
def sections(p):
 z=p.read_bytes();off=struct.unpack_from('<Q',z,40)[0];ent,n,si=struct.unpack_from('<HHH',z,58);ss=[struct.unpack_from('<IIQQQQIIQQ',z,off+i*ent) for i in range(n)];ns=z[ss[si][4]:ss[si][4]+ss[si][5]]
 return {ns[s[0]:].split(b'\0')[0].decode():(s[3],hashlib.sha256(z[s[4]:s[4]+s[5]]).hexdigest()) for s in ss if s[2]&4}
with (R/'rewrite.log').open('w') as log:subprocess.run([str(P/'llvm-bolt'),str(P/'o3'),'-o',str(R/'recreated'),'--data='+str(P/'branch.fdata'),'--reorder-blocks=ext-tsp','--reorder-functions=hfsort','--split-functions','--indirect-prefetch-mode=selected','--indirect-prefetch-profile='+str(P/'selected.json')],check=True,stdout=log,stderr=subprocess.STDOUT)
assert sections(R/'recreated')==sections(P/'new');V=R/'vectors';V.mkdir(exist_ok=False)
expected=json.loads((R/'expected-outputs.json').read_text());out={'recreated_executable_sections_identical':True,'vectors':{}}
for n in ['rail2536','rail507','rail582','bcsstk17']:
 raw=[]
 for v in ['o3','pgo','new','old','recreated']:
  exe=R/v if v=='recreated' else P/v;y=V/(n+'-'+v+'.y')
  subprocess.run([str(exe),str(D/(n+'.csr')),'1','104729',str(y)],check=True,stdout=subprocess.DEVNULL);raw.append(y.read_bytes())
 assert all(x==raw[0] for x in raw);h=hashlib.sha256(raw[0]).hexdigest();assert h==expected[n]['sha256']
 out['vectors'][n]={'all_five_bitwise_equal':True,'sha256_matches_original_machine':h}
(R/'rewrite-and-vector-checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
