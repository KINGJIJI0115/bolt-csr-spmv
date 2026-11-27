"""Rebuild and verify the tail-peeling candidate; calibrate by default."""
import argparse,pathlib,subprocess,json,hashlib,struct,os,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];F=ROOT/'frozen'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sections(p):
 z=p.read_bytes();off=struct.unpack_from('<Q',z,40)[0];ent,n,si=struct.unpack_from('<HHH',z,58);ss=[struct.unpack_from('<IIQQQQIIQQ',z,off+i*ent) for i in range(n)];ns=z[ss[si][4]:ss[si][4]+ss[si][5]]
 return {ns[s[0]:].split(b'\0')[0].decode():(s[3],hashlib.sha256(z[s[4]:s[4]+s[5]]).hexdigest()) for s in ss if s[2]&4}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',nargs='?',default='calibrate',choices=['verify','calibrate','fixed']);ap.add_argument('--out',default='/results/run');ap.add_argument('--cpu',type=int);a=ap.parse_args()
 affinity=sorted(os.sched_getaffinity(0));cpu=affinity[0] if a.cpu is None else a.cpu
 if cpu not in affinity:ap.error('CPU is outside the allowed affinity')
 if 'fma' not in pathlib.Path('/proc/cpuinfo').read_text().split():raise RuntimeError('An x86-64 CPU with FMA is required')
 for rel,h in json.loads((ROOT/'content-manifest.json').read_text()).items():
  if sha(ROOT/rel)!=h:raise RuntimeError('Content hash mismatch: '+rel)
 O=pathlib.Path(a.out).resolve();O.mkdir(parents=True,exist_ok=False);B=O/'bin';B.mkdir()
 for v in ['pgo','old','tail']:
  cmd=[str(F/'llvm-bolt'),str(F/'o3'),'-o',str(B/v),'--data='+str(F/'branch.fdata'),'--reorder-blocks=ext-tsp','--reorder-functions=hfsort','--split-functions']
  if v!='pgo':cmd+=['--indirect-prefetch-mode=selected','--indirect-prefetch-profile='+str(F/'selected.json')]
  if v=='tail':cmd+=['--grouped-fma-peel-tail']
  with (O/(v+'-rewrite.log')).open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
  if sections(B/v)!=sections(F/v):raise RuntimeError('Rebuilt executable sections differ: '+v)
 checks=[]
 for data in sorted((ROOT/'data').glob('*.csr')):
  hs=[]
  for binary in [F/'o3',B/'pgo',B/'old',B/'tail']:
   dump=O/'vector.y';subprocess.run(['taskset','-c',str(cpu),str(binary),str(data),'1','61331',str(dump)],stdout=subprocess.DEVNULL,check=True);hs.append(sha(dump))
  if len(set(hs))!=1:raise RuntimeError('Full-vector mismatch: '+data.stem)
  checks.append({'matrix':data.stem,'all_four_equal':True,'sha256':hs[0]})
 safety={}
 for n in ['guard','fp']:
  base=json.loads(subprocess.check_output([str(ROOT/'tests'/n/'original')],text=True));actual=json.loads(subprocess.check_output([str(ROOT/'tests'/n/'tail')],text=True))
  if actual!=base:raise RuntimeError('Safety failure: '+n)
  safety[n]=actual
 (O/'verification.json').write_text(json.dumps({'rebuild_sections_equal':True,'content_hashes_verified':True,'vectors':checks,'safety':safety},indent=2))
 print('Verified candidate rebuilding, all 19 vectors, boundaries and special floating point',flush=True)
 if a.mode=='verify':return
 if a.mode=='calibrate':
  subprocess.run([sys.executable,str(ROOT/'scripts/select_tail.py'),'--bin',str(B),'--data',str(ROOT/'data'),'--out',str(O/'calibration'),'--cpu',str(cpu)],check=True)
  evaluation=json.loads((O/'calibration/evaluation.json').read_text());bad=[n for n,d in evaluation.items() if d['needs_review']]
  (O/'status.json').write_text(json.dumps({'status':'needs_review' if bad else 'validated','needs_review':bad,'selected_tail':[n for n,d in evaluation.items() if d['new_policy']=='tail']},indent=2))
  if bad:raise RuntimeError('Held-out validation requires review: '+', '.join(bad))
 else:
  subprocess.run([sys.executable,str(ROOT/'scripts/fixed.py'),'--root',str(F),'--data',str(ROOT/'data'),'--out',str(O/'fixed'),'--cpu',str(cpu)],check=True)
if __name__=='__main__':main()
