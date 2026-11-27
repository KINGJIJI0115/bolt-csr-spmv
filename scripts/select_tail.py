import pathlib,subprocess,json,hashlib,random,statistics,math,struct,time,argparse,os
ap=argparse.ArgumentParser();ap.add_argument('--bin',required=True);ap.add_argument('--data',required=True);ap.add_argument('--out',required=True);ap.add_argument('--cpu',default='2');a=ap.parse_args()
B=pathlib.Path(a.bin);D=pathlib.Path(a.data);O=pathlib.Path(a.out);O.mkdir(exist_ok=False,parents=True)
policy={'calibration_seeds':[86028121,104395301],'validation_seed':122949829,'rounds':12,'target_seconds':.25,'max_reps':30000,'baseline_gate':[2.,1.],'incremental_gate':[1.,.5],'variants':['pgo','old','tail'],'cpu':a.cpu,'held_out_from_tail_development':['bcsstk13','bcsstk24','bcsstk27','bcsstk28'],'binary_sha256':{v:hashlib.sha256((B/v).read_bytes()).hexdigest() for v in ['pgo','old','tail']}}
(O/'protocol.json').write_text(json.dumps(policy,indent=2));(O/'environment.txt').write_text(subprocess.check_output(['lscpu'],text=True)+'\n'+subprocess.check_output(['uptime'],text=True))
scope=[];paths=[];checks=[]
def exe(v,p,reps,seed,dump=None):
 args=['taskset','-c',a.cpu,str(B/v),str(p),str(reps),str(seed)]
 if dump:args.append(str(dump))
 return json.loads(subprocess.check_output(args,text=True))
for p in sorted(D.glob('*.csr')):
 with p.open('rb') as f:
  magic,rows,cols,nnz=struct.unpack('<4Q',f.read(32));ptr=struct.unpack('<'+str(rows+1)+'Q',f.read(8*(rows+1)))
 lengths=sorted(ptr[i+1]-ptr[i] for i in range(rows))
 def quantile(q):
  x=(rows-1)*q;i=int(x);return lengths[i]+(lengths[min(i+1,rows-1)]-lengths[i])*(x-i)
 med=quantile(.5);p99=quantile(.99);frac=sum(x>16 for x in lengths)/rows;eligible=24<=med<=64 and p99<=128 and frac>=.8 and cols*8<=262144
 scope.append({'matrix':p.stem,'eligible':eligible,'median':med,'p99':p99,'long_fraction':frac,'vector_bytes':cols*8,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 hs=[]
 for v in policy['variants']:
  dump=O/'vector.y';exe(v,p,1,61331,dump);hs.append(hashlib.sha256(dump.read_bytes()).hexdigest())
 if len(set(hs))!=1:raise RuntimeError('Vector mismatch '+p.stem)
 checks.append({'matrix':p.stem,'all_three_equal':True,'sha256':hs[0]})
 if eligible:paths.append(p)
(O/'structural-screen.json').write_text(json.dumps(scope,indent=2));(O/'correctness.json').write_text(json.dumps(checks,indent=2))
def stats(ratios):
 logs=list(map(math.log,ratios));rng=random.Random(8128);boot=sorted(100*(1-math.exp(statistics.mean(rng.choices(logs,k=len(logs))))) for _ in range(4000))
 return {'gain_pct':100*(1-math.exp(statistics.mean(logs))),'ci95':[boot[100],boot[3900]]}
results={};decisions={}
for stage,seed in [('a',86028121),('b',104395301),('validation',122949829)]:
 for p in paths:
  start=time.perf_counter();probes=[exe('pgo',p,1,seed)['seconds'] for _ in range(3)]
  if not all(math.isfinite(s) and s>0 for s in probes):raise RuntimeError('Invalid probe')
  reps=min(30000,max(2,math.ceil(.25/statistics.median(probes))));records=[]
  for i in range(12):
   order=policy['variants'][:];random.Random(seed+977*i).shuffle(order);outputs={v:exe(v,p,reps,seed) for v in order}
   if len({r['output_hash'] for r in outputs.values()})!=1:raise RuntimeError('Output mismatch')
   if not all(math.isfinite(r['seconds']) and r['seconds']>0 for r in outputs.values()):raise RuntimeError('Invalid measurement')
   records.append({'round':i,'order':order,'outputs':outputs})
  pair={v:{base:stats([r['outputs'][v]['seconds']/r['outputs'][base]['seconds'] for r in records]) for base in ['pgo','old']} for v in ['old','tail']}
  pair.update(records=records,reps=reps,wall_seconds=time.perf_counter()-start)
  results.setdefault(p.stem,{})[stage]=pair
  if stage=='b':
   r=results[p.stem]
   def passes(v,base,gain,lower):return all(r[s][v][base]['gain_pct']>=gain and r[s][v][base]['ci95'][0]>lower for s in ['a','b'])
   baseline='old' if passes('old','pgo',2,1) else 'pgo'
   selected='tail' if passes('tail','pgo',2,1) and passes('tail',baseline,1,.5) else baseline
   decisions[p.stem]={'baseline_policy':baseline,'new_policy':selected,'calibration_wall_seconds':r['a']['wall_seconds']+r['b']['wall_seconds']}
  (O/'results.json').write_text(json.dumps(results,indent=2))
  print(stage,p.stem,round(pair['tail']['old']['gain_pct'],3),flush=True)
 if stage=='b':(O/'frozen-decisions.json').write_text(json.dumps(decisions,indent=2))
for n,d in decisions.items():
 chosen=d['new_policy'];base=d['baseline_policy']
 d['incremental_validation']=results[n]['validation'][chosen][base] if chosen!=base else {'gain_pct':0.,'ci95':[0.,0.],'identical_binary':True}
 d['needs_review']=chosen!=base and d['incremental_validation']['ci95'][0]<=0
(O/'evaluation.json').write_text(json.dumps(decisions,indent=2))
print('DONE selected_tail',[n for n,d in decisions.items() if d['new_policy']=='tail'],'needs_review',[n for n,d in decisions.items() if d['needs_review']],flush=True)
