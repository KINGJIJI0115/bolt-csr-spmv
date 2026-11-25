import pathlib,json
E=pathlib.Path(__file__).resolve().parent
names=json.loads((E/'cases.json').read_text());meta=json.loads((E/'classification.json').read_text())
batches={k:json.loads((E/(k+'.json')).read_text()) for k in ['local-a','local-b','server-a','server-b']}
expected=json.loads((E.parent/'frozen/manifest.json').read_text())['files']
for k,b in batches.items():
 assert len(b['records'])==len(names)*60 and set(b['cases'])==set(names)
 assert all(h==expected[v] for v,h in b['binaries'].items())
for suffix in ['a','b']:
 for n in names:
  hashes=[{r['output_hash'] for r in batches[h+'-'+suffix]['records'] if r['case']==n} for h in ['local','server']]
  assert len(hashes[0])==1 and hashes[0]==hashes[1]
assert len(json.loads((E/'server-correctness.json').read_text()))==len(names)
def fmt(b,n,baseline):
 r=b['cases'][n][baseline];return f"{r['time_reduction_pct']:+.2f}% [{r['ci95'][0]:+.2f}, {r['ci95'][1]:+.2f}]"
lines=['# 非 bcsstk 系列：冻结范围验证','','2026-11-24。阈值、训练数据、程序和 BOLT 工具全部保持冻结。本次不是调参实验。旧交付未修改。','','## 全部候选的结构筛选','','|矩阵|中位行长|P99|行长>16占比|向量字节|显式零数|是否符合|','|---|---:|---:|---:|---:|---:|---|']
for r in meta:lines.append(f"|{r['name']}|{r['median']:g}|{r['p99']:g}|{100*r['long_row_fraction']:.2f}%|{r['vector_bytes']}|{r['explicit_zeros']}|{r['eligible']}|")
lines+=['','圆柱壳系列来自 NIST Matrix Market；msc00726 来自 SuiteSparse 的 UF 镜像，代表 MSC/NASTRAN 结构分析测试。原系数、原显式零保留，对称存储展开一次，不填充、不改变行列顺序。存储行长统计包含显式零，因此可能与网页的数学非零数量不同。来源、原始文件和 CSR 哈希保留在 classification.json。','', '这 8 个候选是基于领域及规模初筛的，不是对整个矩阵库的随机抽样；8/8 满足条件不能解释为这类负载普遍占比很高。7 个 Cylshell 矩阵相互关联，不能按 7 个完全独立应用计算。']
for baseline,title in [('pgo','相对常规 BOLT'),('o3','相对原始 O3')]:
 lines+=['','## '+title,'','正值表示耗时减少，负值表示回退；括号为配对 bootstrap 95% 区间。','','|矩阵|本机 A|本机 B|服务器 A|服务器 B|','|---|---:|---:|---:|---:|']
 for n in names:lines.append('|'+n+'|'+'|'.join(fmt(b,n,baseline) for b in batches.values())+'|')
positive=[n for n in names if all(b['cases'][n]['pgo']['ci95'][0]>0 for b in batches.values())]
negative=[n for n in names if any(b['cases'][n]['pgo']['ci95'][1]<0 for b in batches.values())]
lines+=['','## 结论及边界','', '两机两批相对常规 BOLT 的区间都为正：'+(', '.join(positive) or '无')+'。','至少一批有明确回退：'+(', '.join(negative) or '无')+'。','', '每台机器两批，每个矩阵每批15轮，四种变体随机交错。种子104729/130363。单轮目标0.7秒、最多10000次调用，小矩阵可能达不到0.7秒，实际时长保留。完整 SpMV 计算阶段计时，不含输入加载、离线选择、分配、参考计算；不是求解器端到端性能。','', '两机使用相同冻结二进制及原 profile。本机 Core Ultra 9 275HX/WSL，服务器 Xeon Gold 6133/Ubuntu，绑定 CPU2，服务器内存节点0。服务器共享服务保持运行，不能保证完全独占。','', '每轮程序内完整参考校验和输出 hash 检查通过。两种计时种子跨机器输出 hash 一致。本机另用 SciPy 误差界检查；种子61331下两机四种变体完整向量的SHA256均相同。','', '本次保持所有结果，不根据测得收益删除矩阵或改动阈值。若符合结构条件却回退，说明该条件不能保证收益，必须在报告中保留这一限制。']
(E/'其他系列验证报告.md').write_text('\n'.join(lines)+'\n')
summary={'positive_all_four_vs_bolt':positive,'regression_at_least_one_batch_vs_bolt':negative,'matrix_count':len(names),'cross_machine_hashes_equal':True}
(E/'decision.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
for n in names:print(n,[(k,round(b['cases'][n]['pgo']['time_reduction_pct'],2)) for k,b in batches.items()])
