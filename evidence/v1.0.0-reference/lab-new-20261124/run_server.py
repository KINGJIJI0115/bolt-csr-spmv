import pathlib,subprocess,json,hashlib,datetime
R=pathlib.Path(__file__).resolve().parent
tag='bolt-loop-course:20261124-group4-experiment'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def capture(cmd):return subprocess.check_output(cmd,text=True,stderr=subprocess.STDOUT)
manifest=json.loads((R/'docker-manifest.json').read_text());assert sha(R/manifest['archive'])==manifest['sha256']
assert not (R/'batch-a.json').exists() and not (R/'batch-b.json').exists()
existing=subprocess.run(['docker','image','inspect',tag],capture_output=True,text=True)
if existing.returncode==0:raise RuntimeError('Refuse to overwrite pre-existing image tag')
with (R/'image-load.log').open('w') as log:subprocess.run(['docker','load','-i',str(R/manifest['archive'])],check=True,stdout=log,stderr=subprocess.STDOUT)
environment={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cpu':capture(['lscpu']),'os':pathlib.Path('/etc/os-release').read_text(),'kernel':capture(['uname','-a']),'docker_image':json.loads(capture(['docker','image','inspect',tag]))[0]['Id'],'baseline_containers':capture(['docker','ps','--format','{{.ID}} {{.Names}} {{.Status}}']),'memory':capture(['free','-h']),'cpu_affinity':'2','smt_sibling':'42','memory_node':'0','archive_sha256':manifest['sha256'],'method':'Frozen binaries and four independent matrices, no recompilation or retuning. 15 paired rounds in each of two batches. Read-only root, no network, one logical CPU, NUMA node0, memory cap4GiB.'}
(R/'environment.json').write_text(json.dumps(environment,indent=2))
base=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--cpuset-cpus','2','--cpuset-mems','0','--memory','4g','--pids-limit','128','--user','1000:1000','-v',str(R)+':/results']
verify="""import pathlib,json,hashlib
p=pathlib.Path('/opt/csr-group4-experiment');f=p/'frozen';m=json.loads((f/'manifest.json').read_text())
for n,h in m['files'].items():assert hashlib.sha256((f/n).read_bytes()).hexdigest()==h,n
out={'frozen_files':m['files'],'data':{}}
for n in m['holdouts']:
 h=hashlib.sha256((p/'data'/(n+'.csr')).read_bytes()).hexdigest();q=json.loads((pathlib.Path('/results')/(n+'-metadata.json')).read_text());assert h==q['csr_sha256'],n;out['data'][n]=h
pathlib.Path('/results/verified-content.json').write_text(json.dumps(out,indent=2))
print('Frozen binary and matrix hashes verified')
"""
print(capture(base+['--entrypoint','python3',tag,'-c',verify]),flush=True)
for batch,seed in [('a',104729),('b',130363)]:
 (R/('before-'+batch+'.txt')).write_text(capture(['uptime'])+capture(['mpstat','-P','2,42','1','3']))
 cmd=base+['--name','zxz-group4-repro-'+batch,tag,'--binary-dir','/opt/csr-group4-experiment/frozen','--data','/opt/csr-group4-experiment/data','--cases','rail2536','rail507','rail582','bcsstk17','--seed',str(seed),'--rounds','15','--cpu','2','--out','/results/batch-'+batch+'.json']
 (R/('command-'+batch+'.json')).write_text(json.dumps(cmd,indent=2));print('Starting batch',batch,flush=True)
 with (R/('batch-'+batch+'.log')).open('w') as log:subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT)
 result=json.loads((R/('batch-'+batch+'.json')).read_text());assert len(result['cases'])==4
 print('Completed batch',batch,{n:{b:round(c[b]['time_reduction_pct'],3) for b in ['o3','pgo']} for n,c in result['cases'].items()},flush=True)
(R/'after.txt').write_text(capture(['uptime'])+capture(['docker','ps','--format','{{.ID}} {{.Names}} {{.Status}}']))
print('All two-batch measurements completed',flush=True)
