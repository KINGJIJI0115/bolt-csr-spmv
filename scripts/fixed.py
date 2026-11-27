import pathlib,subprocess,json,hashlib,random,statistics,math,time,argparse,os
ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--data',required=True);ap.add_argument('--out',required=True);ap.add_argument('--cpu',default='2');a=ap.parse_args()
R=pathlib.Path(a.root);D=pathlib.Path(a.data);O=pathlib.Path(a.out);O.mkdir(exist_ok=False,parents=True)
names=sorted(p.stem for p in D.glob('*.csr'));variants=['o3','pgo','old','tail']
protocol={'cases':names,'variants':variants,'rounds':15,'target_seconds':.3,'max_reps':30000,'seeds':[104729,130363],'cpu':a.cpu,'phase':'Fixed four-binary audit; separate from automatic selection','binaries':{v:hashlib.sha256((R/v).read_bytes()).hexdigest() for v in variants}}
(O/'protocol.json').write_text(json.dumps(protocol,indent=2));(O/'environment.txt').write_text(subprocess.check_output(['lscpu'],text=True)+'\n'+subprocess.check_output(['uptime'],text=True)+'\nAffinity '+str(sorted(os.sched_getaffinity(0))))
def exe(v,name,reps,seed):return json.loads(subprocess.check_output(['taskset','-c',a.cpu,str(R/v),str(D/(name+'.csr')),str(reps),str(seed)],text=True))
def stats(ratios):
 logs=list(map(math.log,ratios));rng=random.Random(71);b=sorted(100*(1-math.exp(statistics.mean(rng.choices(logs,k=len(logs))))) for _ in range(10000))
 return {'time_reduction_pct':100*(1-math.exp(statistics.mean(logs))),'ci95':[b[250],b[9750]],'paired_ratios':ratios}
for label,seed in zip(['a','b'],protocol['seeds']):
 out={'seed':seed,'records':[],'cases':{}}
 for name in names:
  probes=[exe('old',name,1,seed)['seconds'] for _ in range(3)]
  if not all(math.isfinite(x) and x>0 for x in probes):raise RuntimeError('Invalid probe')
  reps=min(30000,max(2,math.ceil(.3/statistics.median(probes))))
  for i in range(15):
   order=variants[:];random.Random(seed+977*i).shuffle(order);outputs={v:exe(v,name,reps,seed) for v in order}
   if len({x['output_hash'] for x in outputs.values()})!=1:raise RuntimeError('Outputs differ')
   if not all(math.isfinite(x['seconds']) and x['seconds']>0 for x in outputs.values()):raise RuntimeError('Invalid timing')
   out['records'].append({'case':name,'round':i,'order':order,'reps':reps,'outputs':outputs})
  rows=[r for r in out['records'] if r['case']==name]
  out['cases'][name]={v:{base:stats([r['outputs'][v]['seconds']/r['outputs'][base]['seconds'] for r in rows]) for base in ['old','pgo','o3']} for v in ['tail']}
  (O/(label+'.json')).write_text(json.dumps(out,indent=2));print(label,name,{v:round(out['cases'][name][v]['old']['time_reduction_pct'],3) for v in ['tail']},flush=True)
