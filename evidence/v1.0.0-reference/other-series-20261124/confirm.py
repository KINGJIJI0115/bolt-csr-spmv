import pathlib,subprocess,json,statistics,random,math,argparse,hashlib,time
ap=argparse.ArgumentParser();ap.add_argument('--binary-dir',required=True);ap.add_argument('--data',required=True);ap.add_argument('--cases',nargs='+',required=True);ap.add_argument('--seed',type=int,required=True);ap.add_argument('--rounds',type=int,default=15);ap.add_argument('--seconds',type=float,default=.7);ap.add_argument('--out',required=True);ap.add_argument('--cpu',default='2');a=ap.parse_args();D=pathlib.Path(a.binary_dir)
paths={v:D/v for v in ['o3','pgo','new','old'] if (D/v).exists()}
out={'seed':a.seed,'rounds':a.rounds,'cpu':a.cpu,'target_seconds':a.seconds,'start_time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'binaries':{v:hashlib.sha256(p.read_bytes()).hexdigest() for v,p in paths.items()},'records':[],'cases':{}}
def exe(p,f,reps):return json.loads(subprocess.check_output(['taskset','-c',a.cpu,str(p),str(f),str(reps),str(a.seed)],text=True))
for name in a.cases:
 f=pathlib.Path(a.data)/(name+'.csr');cal=exe(paths['o3'],f,1);reps=min(10000,max(2,math.ceil(a.seconds/cal['seconds'])))
 for i in range(a.rounds):
  vs=list(paths);random.Random(a.seed+977*i).shuffle(vs);hs=[]
  for v in vs:
   r=exe(paths[v],f,reps);out['records'].append(dict(case=name,round=i,variant=v,**r));hs.append(r['output_hash'])
  assert len(set(hs))==1,(name,i,hs)
  pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
 result={}
 for b in paths:
  if b=='new':continue
  ratios=[]
  for i in range(a.rounds):
   ts={r['variant']:r['seconds'] for r in out['records'] if r['case']==name and r['round']==i};ratios.append(ts['new']/ts[b])
  logs=list(map(math.log,ratios));rng=random.Random(71);bs=sorted(100*(1-math.exp(statistics.mean(rng.choices(logs,k=len(logs))))) for _ in range(10000))
  result[b]={'time_reduction_pct':100*(1-math.exp(statistics.mean(logs))),'ci95':[bs[250],bs[9750]],'median_pct':100*(1-statistics.median(ratios)),'paired_ratios':ratios}
 out['cases'][name]=result;pathlib.Path(a.out).write_text(json.dumps(out,indent=2));print(name,json.dumps(result),flush=True)
