import pathlib,struct,json,sys
import numpy as np
E=pathlib.Path(__file__).resolve().parent;P=pathlib.Path('/home/jiji/prefetch-indirect-pilot/real-csr-opt')
paths=list((P/'other-series-data').glob('*.csr'))+list((P/'specialized-data').glob('*.csr'))+[P/'holdout-data/bcsstk17.csr']
rows=[]
for path in sorted(paths):
 with path.open('rb') as f:
  _,nr,nc,nnz=struct.unpack('<4Q',f.read(32));rp=np.fromfile(f,'<u8',nr+1);ci=np.fromfile(f,'<u4',nnz)
 lengths=np.diff(rp).astype(np.int64);long=lengths>16;groups=np.where(long,(lengths-1)//4,0);tails=lengths-4*groups
 counts=np.unique(lengths,return_counts=True)[1];prob=counts/nr
 line_switches=sum(np.count_nonzero(np.diff(ci[int(a):int(b)]//8)) for a,b in zip(rp[:-1],rp[1:]))
 distinct=sum(len(np.unique(ci[int(a):int(b)]//8)) for a,b in zip(rp[:-1],rp[1:]))
 rec={'name':path.stem,'mean_row':float(lengths.mean()),'median':float(np.median(lengths)),
 'row_length_entropy_bits':float(-np.sum(prob*np.log2(prob))),'dominant_row_fraction':float(max(prob)),
 'adjacent_rows_equal_fraction':float(np.mean(lengths[1:]==lengths[:-1])),
 'grouped_work_fraction':float(4*sum(groups)/nnz),'tail_work_fraction':float(sum(tails)/nnz),
 'estimated_inner_instruction_reduction_pct':float(100*(1-(20*sum(groups)+6*sum(tails)+4*sum(lengths>0)+sum(long))/(6*nnz))),
 'distinct_x_cachelines_per_stored_element':distinct/nnz,'within_row_x_cacheline_switch_fraction':line_switches/nnz,
 'matrix_bytes':int(32+8*(nr+1)+12*nnz),'vector_bytes':int(nc*8)}
 rows.append(rec)
(E/'features.json').write_text(json.dumps(rows,indent=2))
for r in rows:print(r['name'],'mean',round(r['mean_row'],2),'entropy',round(r['row_length_entropy_bits'],2),'dominant',round(r['dominant_row_fraction'],2),'tail',round(r['tail_work_fraction'],3),'insnsave',round(r['estimated_inner_instruction_reduction_pct'],2),'xlines',round(r['distinct_x_cachelines_per_stored_element'],3))
