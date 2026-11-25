import pathlib,struct,json,hashlib,subprocess,shutil
import numpy as np
from scipy.io import mmread
E=pathlib.Path(__file__).resolve().parent;P=pathlib.Path('/home/jiji/prefetch-indirect-pilot/real-csr-opt');D=E/'data';D.mkdir(exist_ok=False)
for name,dim,nnz in [('bcsstk14',1806,63454),('bcsstk15',3948,117816),('bcsstk16',4884,290378)]:
 raw=E/'downloads'/(name+'.mtx.gz');m=mmread(str(raw)).tocsr();assert m.shape==(dim,dim) and m.nnz==nnz
 f=D/(name+'.csr')
 with f.open('wb') as h:
  h.write(struct.pack('<4Q',0x3152434454455354,dim,dim,nnz));np.asarray(m.indptr,dtype='<u8').tofile(h);np.asarray(m.indices,dtype='<u4').tofile(h);np.asarray(m.data,dtype='<f8').tofile(h)
 lens=np.diff(m.indptr);qs=np.quantile(lens,[0,.5,.9,.99,1]);frac=float(np.mean(lens>16));matches=bool(24<=qs[1]<=64 and qs[3]<=128 and frac>=.8 and dim*8<=256*1024)
 meta={'name':name,'rows':dim,'nnz':nnz,'row_quantiles':qs.tolist(),'long_row_fraction':frac,'vector_bytes':dim*8,'matches_predeclared_scope':matches,'csr_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'conversion':'Original real coefficients; symmetric storage expanded once; sorted CSR, no padding, tiling, permutation or modification.','source':'https://math.nist.gov/pub/MatrixMarket2/Harwell-Boeing/bcsstruc2/'+raw.name}
 (E/(name+'-metadata.json')).write_text(json.dumps(meta,indent=2));print(meta,flush=True)
 state=61331;mask=(1<<64)-1;x=np.empty(dim)
 for i in range(dim):
  state^=(state<<13)&mask;state^=state>>7;state^=(state<<17)&mask;x[i]=(state%2003-1001)/1009.
 ref=m@x;outputs=[]
 for variant in ['o3','pgo','new','old']:
  y=E/(name+'-'+variant+'.y');subprocess.run([str(P/'group4-frozen-v1'/variant),str(f),'1','61331',str(y)],check=True,stdout=subprocess.DEVNULL);outputs.append(y.read_bytes())
 assert all(v==outputs[0] for v in outputs)
 y=np.frombuffer(outputs[0],dtype='<f8');n=lens.astype(float);u=np.finfo(float).eps/2;bound=2*(2*n*u/(1-2*n*u))*(abs(m)@abs(x))+np.finfo(float).tiny
 assert np.all(np.abs(y-ref)<=bound)
 meta['full_vectors_equal']=True;meta['reference_bound_passed']=True;meta['output_sha256']=hashlib.sha256(outputs[0]).hexdigest();(E/(name+'-metadata.json')).write_text(json.dumps(meta,indent=2))
L=P/'specialized-data';shutil.copytree(D,L)
shutil.copy2(E.parent/'confirm.py',E/'confirm.py');shutil.copy2(E.parent/'专项负载范围方案.md',E/'测试前范围方案.md')
