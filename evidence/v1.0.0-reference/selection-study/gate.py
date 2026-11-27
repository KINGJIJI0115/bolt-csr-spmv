"""Prospective target-machine calibration; validate after freezing decisions."""
import argparse,hashlib,json,math,pathlib,random,statistics,subprocess,time,platform

POLICY={'calibration_seeds':[32452843,49979687],'validation_seed':67867967,
        'rounds':12,'target_seconds':.25,'max_reps':30000,
        'minimum_point_gain_pct':2.,'minimum_ci_lower_pct':1.,
        'bootstrap_samples':4000,'decision':'Both calibration batches must pass; validation cannot change selection.'}

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()

def stats(ratios):
 logs=list(map(math.log,ratios));rng=random.Random(8128)
 boot=sorted(100*(1-math.exp(statistics.mean(rng.choices(logs,k=len(logs))))) for _ in range(POLICY['bootstrap_samples']))
 return {'gain_pct':100*(1-math.exp(statistics.mean(logs))),'ci95':[boot[100],boot[3900]]}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--frozen',required=True);ap.add_argument('--data',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 F=pathlib.Path(a.frozen);D=pathlib.Path(a.data);O=pathlib.Path(a.out);O.mkdir(exist_ok=False,parents=True)
 manifest=json.loads((F/'manifest.json').read_text());hashes={n:sha(F/n) for n in ['pgo','new']}
 assert all(v==manifest['files'][n] for n,v in hashes.items())
 paths=sorted(D.glob('*.csr'));assert len(paths)==12
 env=subprocess.check_output(['lscpu'],text=True)
 (O/'protocol.json').write_text(json.dumps(dict(POLICY,data_sha256={p.stem:sha(p) for p in paths},binaries=hashes,environment=env,python=platform.python_version()),indent=2))
 results={};decisions={};all_start=time.perf_counter()
 def exe(v,p,reps,seed):
  return json.loads(subprocess.check_output(['taskset','-c','2',str(F/v),str(p),str(reps),str(seed)],text=True))
 for stage,seed in [('cal-a',POLICY['calibration_seeds'][0]),('cal-b',POLICY['calibration_seeds'][1]),('validation',POLICY['validation_seed'])]:
  for p in paths:
   start=time.perf_counter();probe=exe('pgo',p,1,seed);reps=min(POLICY['max_reps'],max(2,math.ceil(POLICY['target_seconds']/probe['seconds'])))
   records=[];ratios=[]
   for i in range(POLICY['rounds']):
    variants=['pgo','new'];random.Random(seed+977*i).shuffle(variants);r={v:exe(v,p,reps,seed) for v in variants}
    assert r['pgo']['output_hash']==r['new']['output_hash']
    ratios.append(r['new']['seconds']/r['pgo']['seconds']);records.append({'round':i,'order':variants,'outputs':r})
   summary=stats(ratios);summary.update(wall_seconds=time.perf_counter()-start,reps=reps,seed=seed,records=records)
   results.setdefault(p.stem,{})[stage]=summary
   if stage=='cal-b':
    q=results[p.stem];enabled=all(q[k]['gain_pct']>=POLICY['minimum_point_gain_pct'] and q[k]['ci95'][0]>POLICY['minimum_ci_lower_pct'] for k in ['cal-a','cal-b'])
    profile=json.loads((F/'selected.json').read_text());profile['loops'][0]['selected']=enabled
    profile['selection']='target-machine two-batch calibration gate v1'
    profile['calibration_binding']={'matrix_sha256':sha(p),'environment_sha256':hashlib.sha256(env.encode()).hexdigest(),'binary_sha256':hashes,'policy':POLICY}
    (O/(p.stem+'-selected.json')).write_text(json.dumps(profile,indent=2))
    decisions[p.stem]={'enabled':enabled,'chosen_binary':'new' if enabled else 'pgo','calibration_wall_seconds':sum(q[k]['wall_seconds'] for k in ['cal-a','cal-b'])}
   (O/'results.json').write_text(json.dumps(results,indent=2))
   print(stage,p.stem,round(summary['gain_pct'],2),summary['ci95'],flush=True)
  if stage=='cal-b':
   (O/'frozen-decisions.json').write_text(json.dumps(decisions,indent=2))
 # Validation is never consulted by the selector.
 for n,d in decisions.items():
  v=results[n]['validation'];d['validation_gain_pct']=v['gain_pct'];d['validation_ci95']=v['ci95']
  saved=statistics.mean((r['outputs']['pgo']['seconds']-r['outputs']['new']['seconds'])/v['reps'] for r in v['records'])
  d['estimated_calls_to_amortize_calibration']=math.ceil(d['calibration_wall_seconds']/saved) if d['enabled'] and saved>0 else None
  d['selected_policy_validation_gain_pct']=v['gain_pct'] if d['enabled'] else 0.
 (O/'evaluation.json').write_text(json.dumps({'decisions':decisions,'total_wall_seconds':time.perf_counter()-all_start},indent=2))

if __name__=='__main__':main()
