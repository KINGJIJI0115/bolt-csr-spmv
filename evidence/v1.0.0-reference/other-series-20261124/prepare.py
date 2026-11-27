import pathlib,json,struct,hashlib,tarfile,sys,shutil,subprocess
import numpy as np
from scipy.io import mmread
E=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(E.parent/'scope-selector'))
from select_scope import inspect,POLICY
P=pathlib.Path('/home/jiji/prefetch-indirect-pilot/real-csr-opt')
D=P/'other-series-data';D.mkdir(exist_ok=False)
F=P/'group4-frozen-v1';records=[]
names=['s3rmt3m3','s1rmt3m1','s2rmt3m1','s3rmt3m1','s1rmq4m1','s2rmq4m1','s3rmq4m1','msc00726']
(E/'protocol.json').write_text(json.dumps({'policy':POLICY,'candidates':names,'selection':'All candidates satisfying frozen structural policy are timed, including negative results. No retraining or parameter adjustment.','seeds':[104729,130363],'rounds':15,'variants':['o3','pgo','new','old'],'explicit_zeros':'preserve original stored zeros; no elimination or padding'},indent=2))
for n in names:
 raw=E/'downloads'/(n+('.tar.gz' if n=='msc00726' else '.mtx.gz'))
 if n=='msc00726':
  with tarfile.open(raw) as t:
   with t.extractfile('msc00726/msc00726.mtx') as f:m=mmread(f).tocsr()
 else:m=mmread(str(raw)).tocsr()
 m.sort_indices();rows,cols=m.shape
 path=D/(n+'.csr')
 with path.open('wb') as f:
  f.write(struct.pack('<4Q',0x3152434454455354,rows,cols,m.nnz));np.asarray(m.indptr,dtype='<u8').tofile(f);np.asarray(m.indices,dtype='<u4').tofile(f);np.asarray(m.data,dtype='<f8').tofile(f)
 rec=inspect(path);rec['name']=n;rec['raw_sha256']=hashlib.sha256(raw.read_bytes()).hexdigest();rec['explicit_zeros']=int(np.sum(m.data==0));rec['source']=('https://www.cise.ufl.edu/research/sparse/MM/Boeing/msc00726.tar.gz' if n=='msc00726' else 'https://math.nist.gov/pub/MatrixMarket2/misc/cylshell/'+raw.name)
 state=61331;mask=(1<<64)-1;x=np.empty(cols)
 for i in range(cols):
  state^=(state<<13)&mask;state^=state>>7;state^=(state<<17)&mask;x[i]=(state%2003-1001)/1009.
 ref=m@x;outputs=[]
 for v in ['o3','pgo','new','old']:
  y=E/(n+'-'+v+'.y');subprocess.run([str(F/v),str(path),'1','61331',str(y)],check=True,stdout=subprocess.DEVNULL);outputs.append(y.read_bytes())
 assert all(z==outputs[0] for z in outputs)
 lens=np.diff(m.indptr).astype(float);u=np.finfo(float).eps/2;bound=2*(2*lens*u/(1-2*lens*u))*(abs(m)@abs(x))+np.finfo(float).tiny
 assert np.all(abs(np.frombuffer(outputs[0],dtype='<f8')-ref)<=bound)
 rec.update(full_vectors_equal=True,reference_bound_passed=True,output_sha256=hashlib.sha256(outputs[0]).hexdigest());records.append(rec);print(n,rec['eligible'],rec['median'],rec['p99'],rec['long_row_fraction'],flush=True)
(E/'classification.json').write_text(json.dumps(records,indent=2));(E/'cases.json').write_text(json.dumps([r['name'] for r in records if r['eligible']]))
shutil.copytree(D,E/'data');shutil.copy2(E.parent/'confirm.py',E/'confirm.py')
