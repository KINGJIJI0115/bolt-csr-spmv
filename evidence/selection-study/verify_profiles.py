import pathlib,json,struct,subprocess,argparse
def sections(p):
 z=p.read_bytes();off=struct.unpack_from('<Q',z,40)[0];ent,n,si=struct.unpack_from('<HHH',z,58)
 ss=[struct.unpack_from('<IIQQQQIIQQ',z,off+i*ent) for i in range(n)];names=z[ss[si][4]:ss[si][4]+ss[si][5]]
 return {names[s[0]:].split(b'\0')[0]: (s[3],z[s[4]:s[4]+s[5]]) for s in ss if s[2]&4}
ap=argparse.ArgumentParser();ap.add_argument('--frozen',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
F=pathlib.Path(a.frozen);O=pathlib.Path(a.out);D=O/'rewritten';D.mkdir(exist_ok=False)
expected={v:sections(F/v) for v in ['pgo','new']};checks=[]
for n,d in json.loads((O/'frozen-decisions.json').read_text()).items():
 cmd=[str(F/'llvm-bolt'),str(F/'o3'),'-o',str(D/n),'--data='+str(F/'branch.fdata'),'--reorder-blocks=ext-tsp','--reorder-functions=hfsort','--split-functions','--indirect-prefetch-mode=selected','--indirect-prefetch-profile='+str(O/(n+'-selected.json'))]
 with (D/(n+'.log')).open('w') as log:subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT)
 assert sections(D/n)==expected[d['chosen_binary']]
 checks.append({'name':n,'chosen_binary':d['chosen_binary'],'executable_sections_identical':True})
(O/'profile-checks.json').write_text(json.dumps(checks,indent=2));print('all profiles applied and executable sections verified',len(checks))
