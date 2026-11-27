import pathlib,json,hashlib
E=pathlib.Path(__file__).resolve().parent;names=['bcsstk14','bcsstk15','bcsstk16'];batches={k:json.loads((E/(k+'.json')).read_text()) for k in ['local-a','local-b','server-a','server-b']}
checks=json.loads((E/'server-vector-checks.json').read_text())
for n in names:assert checks[n]['full_vectors_equal_on_server'] and checks[n]['full_vector_sha256_matches_local']==json.loads((E/(n+'-metadata.json')).read_text())['output_sha256']
expected=json.loads((E.parent/'frozen/manifest.json').read_text())['files']
for label,q in batches.items():
 assert set(q['cases'])==set(names) and len(q['records'])==180
 assert all(h==expected[v] for v,h in q['binaries'].items())
for suffix in ['a','b']:
 for n in names:
  hs=[{r['output_hash'] for r in batches[k+'-'+suffix]['records'] if r['case']==n} for k in ['local','server']];assert len(hs[0])==1 and hs[0]==hs[1]
def fmt(q,n,base='pgo'):
 r=q['cases'][n][base];return f"{r['time_reduction_pct']:+.2f}% [{r['ci95'][0]:+.2f}, {r['ci95'][1]:+.2f}]"
lines=['# 专项CSR负载独立验证结果','','2026-11-24。原有交付及冻结实现未修改。仅新增三个真实矩阵，不重新训练或调参。','','## 测试前范围与实际结构','','筛选条件在计时之前固定：行长中位数24～64、99百分位不超过128、超过16元素的行至少80%、输入向量不超过256KiB。它们是离线数据范围假设，不是当前BOLT实现的自动选择规则。','','|矩阵|中位行长|99百分位|长于16的行|向量字节|符合范围|','|---|---:|---:|---:|---:|---|']
for n in names:
 m=json.loads((E/(n+'-metadata.json')).read_text());assert m['full_vectors_equal'] and m['reference_bound_passed'];lines.append(f"|{n}|{m['row_quantiles'][1]:g}|{m['row_quantiles'][3]:g}|{m['long_row_fraction']*100:.2f}%|{m['vector_bytes']}|{m['matches_predeclared_scope']}|")
lines+=['','三者均来自NIST/Harwell-Boeing结构工程矩阵。原系数保留，按对称存储展开一次并转CSR，不做填充、转置或重新排列矩阵行。来源与哈希见metadata文件。','','## 相对常规BOLT的耗时降低','','每台机器两批，每矩阵每批15轮；种子104729/130363，随机交错四种变体。正值表示耗时降低，方括号为配对bootstrap 95%区间。每轮目标0.7秒，最多10000次调用，因此部分小矩阵计时较短，真实时长全部保留。','','|矩阵|本机第一批|本机第二批|服务器第一批|服务器第二批|','|---|---:|---:|---:|---:|']
for n in names:lines.append('|'+n+'|'+'|'.join(fmt(q,n) for q in batches.values())+'|')
lines+=['','## 相对原始O3的耗时降低','','用于区分新增收益与恢复常规BOLT回退；不能混用两个基线。','','|矩阵|本机第一批|本机第二批|服务器第一批|服务器第二批|','|---|---:|---:|---:|---:|']
for n in names:lines.append('|'+n+'|'+'|'.join(fmt(q,n,'o3') for q in batches.values())+'|')
positive=[n for n in names if all(q['cases'][n]['pgo']['ci95'][0]>0 for q in batches.values())]
summary={'all_four_batches_positive_vs_bolt':positive,'all_three_in_predeclared_scope':True,'same_frozen_binaries':True,'same_output_hashes_across_machines':True,'all_negative_results_retained':True}
lines+=['','## 结论与限制','',f"三个新矩阵中，两台机器两批相对常规BOLT的区间均高于零的矩阵：{', '.join(positive) or '无'}。",'', '计时覆盖完整SpMV计算阶段，不含文件加载、内存分配与参考计算。原始程序GCC O3+FMA；本机Core Ultra 9 275HX/WSL，服务器Xeon Gold 6133/Ubuntu22.04。均绑定逻辑CPU2，服务器内存节点0；Docker没有改变参数和代码。服务器共享服务未停止。','', '所有变体内部完整参考校验和每轮输出检查通过；两种种子下两台机器输出hash完全一致；本机另比较四种变体完整向量，并用SciPy逐行误差界验证。','', '这些数据可以检验这一初始范围是否值得继续研究，但三个同系列结构工程实例不足以证明所有符合阈值的矩阵都受益，更不证明任意编译器或向量化循环有效。bcsstk17仅作为发现规律的旧参照。旧铁路矩阵和LiveJournal的负结果仍然保留。','', '若根据本次结果继续调整阈值、实现或训练，这三个矩阵转为开发集，需要新的独立验证集。下一步应优先明确可实现的选择策略，避免只在报告中缩小范围，却让不适合的程序默认进入优化。']
(E/'专项负载验证报告.md').write_text('\n'.join(lines)+'\n');(E/'decision.json').write_text(json.dumps(summary,indent=2));print(summary)
with (E/'专项负载验证报告.md').open('a') as f:f.write('\n补充：服务器亦导出了四种变体的完整输出向量，逐字节比较一致；SHA256与本机seed61331完整输出一致。见server-vector-checks.json。\n')
(E/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(E))+'\n' for p in sorted(E.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'))
for n in names:print(n,[(k,fmt(q,n),fmt(q,n,'o3')) for k,q in batches.items()])
