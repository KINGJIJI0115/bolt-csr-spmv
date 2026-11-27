import pathlib,json,subprocess,argparse
E=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--server',action='store_true');a=ap.parse_args()
names=json.loads((E/'cases.json').read_text());assert names
if a.server:
 (E/'environment.txt').write_text(subprocess.check_output(['lscpu'],text=True)+subprocess.check_output(['mpstat','-P','2,42','1','3'],text=True))
 base=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--cpuset-cpus','2','--cpuset-mems','0','--memory','4g','--pids-limit','128','--user','1000:1000','-v',str(E)+':/results','bolt-loop-course:20261124-group4-experiment','--binary-dir','/opt/csr-group4-experiment/frozen','--data','/results/data'];label='server'
else:
 base=['python3',str(E/'confirm.py'),'--binary-dir','/home/jiji/prefetch-indirect-pilot/real-csr-opt/group4-frozen-v1','--data','/home/jiji/prefetch-indirect-pilot/real-csr-opt/other-series-data'];label='local'
for suffix,seed in [('a',104729),('b',130363)]:
 name=label+'-'+suffix
 cmd=base+['--cases',*names,'--seed',str(seed),'--rounds','15','--cpu','2','--out',('/results/' if a.server else str(E)+'/')+name+'.json']
 (E/(name+'-command.json')).write_text(json.dumps(cmd,indent=2))
 with (E/(name+'.log')).open('w') as f:subprocess.run(cmd,check=True,stdout=f,stderr=subprocess.STDOUT)
 print(name,'complete',flush=True)
