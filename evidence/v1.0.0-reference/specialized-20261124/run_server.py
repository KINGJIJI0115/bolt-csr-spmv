import pathlib,subprocess,json,hashlib
R=pathlib.Path(__file__).resolve().parent
for n in ['bcsstk14','bcsstk15','bcsstk16']:
 q=json.loads((R/(n+'-metadata.json')).read_text());assert hashlib.sha256((R/'data'/(n+'.csr')).read_bytes()).hexdigest()==q['csr_sha256']
(R/'environment.txt').write_text(subprocess.check_output(['lscpu'],text=True)+subprocess.check_output(['mpstat','-P','2,42','1','3'],text=True))
base=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--cpuset-cpus','2','--cpuset-mems','0','--memory','4g','--user','1000:1000','-v',str(R)+':/results','bolt-loop-course:20261124-group4-experiment']
for label,seed in [('a',104729),('b',130363)]:
 cmd=base+['--binary-dir','/opt/csr-group4-experiment/frozen','--data','/results/data','--cases','bcsstk14','bcsstk15','bcsstk16','--seed',str(seed),'--rounds','15','--cpu','2','--out','/results/server-'+label+'.json']
 (R/('command-'+label+'.json')).write_text(json.dumps(cmd,indent=2))
 with (R/('server-'+label+'.log')).open('w') as log:subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT)
 print('completed server',label,flush=True)
