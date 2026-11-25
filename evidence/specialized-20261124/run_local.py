import pathlib,subprocess
E=pathlib.Path(__file__).resolve().parent
for label,seed in [('a',104729),('b',130363)]:
 cmd=['python3',str(E/'confirm.py'),'--binary-dir','/home/jiji/prefetch-indirect-pilot/real-csr-opt/group4-frozen-v1','--data','/home/jiji/prefetch-indirect-pilot/real-csr-opt/specialized-data','--cases','bcsstk14','bcsstk15','bcsstk16','--seed',str(seed),'--rounds','15','--cpu','2','--out',str(E/('local-'+label+'.json'))]
 with (E/('local-'+label+'.log')).open('w') as log:subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT)
 print('completed local',label,flush=True)
