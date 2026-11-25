import pathlib,json,hashlib,math
E=pathlib.Path(__file__).resolve().parent
hosts={h:{f:json.loads((E/h/(f+'.json')).read_text()) for f in ['protocol','results','frozen-decisions','evaluation']} for h in ['local','server']}
assert hosts['local']['protocol']['data_sha256']==hosts['server']['protocol']['data_sha256']
assert hosts['local']['protocol']['binaries']==hosts['server']['protocol']['binaries']
for h,q in hosts.items():
 checks=json.loads((E/h/'profile-checks.json').read_text())
 assert len(checks)==12 and all(c['executable_sections_identical'] for c in checks)
 for n,d in q['frozen-decisions'].items():
  r=q['results'][n]
  assert d['enabled']==all(r[s]['gain_pct']>=2 and r[s]['ci95'][0]>1 for s in ['cal-a','cal-b'])
  assert len(r['validation']['records'])==12
for n in hosts['local']['results']:
 for s in ['cal-a','cal-b','validation']:
  hashes=[{v['output_hash'] for r in hosts[h]['results'][n][s]['records'] for v in r['outputs'].values()} for h in hosts]
  assert len(hashes[0])==1 and hashes[0]==hashes[1]
lines=['# 收益筛选规则：结构分析与目标机器校准','','## 结论的依据','','旧四项结构阈值只适合作为候选范围。四边形网格反例的尾部占比约3.9%，低于三角形网格约5.4%；估算循环指令减少约14.4%，高于三角形网格约13.7%，却出现回退。bcsstk16和反例的行长中位数同为54。因此不能把回退简单归因于尾部太多、减少指令太少或中位行长54。','', 'features.json还保存了行长熵、相同行长占比、相邻同行长比例、矩阵字节数以及假设64字节缓存行下的向量访问特征。这些是静态描述与分析估算，不是硬件性能计数器。没有新的PMU证据，不能宣称已证明分支预测或缓存是原因。','', '本轮不追加按矩阵名、领域或测得结果反推的结构阈值。改为先过结构/机器码安全条件，再进行目标机器上的保守实测校准。','','## 固定的选择规则','','1. 机器码必须通过既有变换识别与安全检查；正确性不依赖收益阈值。','2. 四项结构条件保持不变，仅限定候选范围。','3. 在目标机器以同一O3输入、相同常规BOLT配置比较pgo和new。两批各12轮随机配对；两批收益点估计都至少2%，且各自95%配对bootstrap区间下界都大于1%，才启用。','4. 不满足、结果不确定或校验失败时，保留常规BOLT；不能把失败结果从报告中删除。','5. 选择绑定矩阵SHA256、二进制SHA256和环境记录。换数据、换CPU或重要运行环境变化后重新校准。JSON中的绑定是审计信息，不是运行时强制检测。','', '2%与1%是预先确定的工程裕量，不是最优阈值或统计保证。12轮bootstrap也不能排除系统性噪声。该流程适合长期重复计算同一类/已知数据的部署，不适合每个矩阵仅执行一次。','','## 新计时批次的验证','','所有12个矩阵此前均已看过，不能称为独立新矩阵验证。校准使用两个新种子32452843/49979687，选择冻结后使用第三个种子67867967验证。验证结果没有反馈到选择规则；不宣称在新矩阵上泛化。每变体目标0.25秒、最多30000次调用，全部原始计时保留。主指标为完整SpMV计算阶段耗时，不含离线校准、文件加载、参考计算。','','|矩阵|本机选择|本机第三批候选收益|服务器选择|服务器第三批候选收益|','|---|---|---:|---|---:|']
def fmt(v):return f"{v['gain_pct']:+.2f}% [{v['ci95'][0]:+.2f}, {v['ci95'][1]:+.2f}]"
summary={}
for n in hosts['local']['results']:
 cells=[n]
 for h,q in hosts.items():
  cells+=['启用' if q['frozen-decisions'][n]['enabled'] else '常规BOLT',fmt(q['results'][n]['validation'])]
 lines.append('|'+ '|'.join(cells)+'|')
for h,q in hosts.items():
 selected=[n for n,d in q['frozen-decisions'].items() if d['enabled']]
 failures=[n for n in selected if q['results'][n]['validation']['ci95'][0]<=0]
 costs=[d['calibration_wall_seconds'] for d in q['evaluation']['decisions'].values()]
 calls=[d['estimated_calls_to_amortize_calibration'] for d in q['evaluation']['decisions'].values() if d['estimated_calls_to_amortize_calibration'] is not None]
 summary[h]={'selected':selected,'selected_without_positive_validation_ci':failures,'calibration_wall_seconds_range':[min(costs),max(costs)],'amortization_calls_range':[min(calls),max(calls)] if calls else None}
lines+=['','表格对未启用者仍展示候选自身的实测收益或回退。选择常规BOLT之后没有新增变换，但本轮没有把两份相同程序重复计时并声称精确0%波动。','', '全部阶段两机两变体输出hash一致，程序内完整参考比较通过。']
for h,r in summary.items():
 lines+=['',f"{h}：选中{len(r['selected'])}个，第三批收益区间未保持为正的选中项：{r['selected_without_positive_validation_ci']}。每个矩阵两批校准墙钟成本范围{r['calibration_wall_seconds_range']}秒。按第三批平均单次计算节省估算，选中项需约{r['amortization_calls_range']}次SpMV才摊销校准成本；不包括候选构建和数据准备，不能视为端到端收益承诺。"]
lines+=['','## 交付建议','','两台机器各12份选择profile均实际传入冻结llvm-bolt生成程序，并检查可执行节地址与字节：启用者与new一致，跳过者与pgo一致。记录见各主机profile-checks.json。','', '保留冻结变换作为优化核心；新增规则定位为可选部署校准工具，不宣称是新的通用优化算法。若提交材料需要无校准成本的自动收益选择，当前工作尚未解决。若要求某一份部署配置在两台已测机器均有收益，可要求它分别通过两机校准；这仍不能推及所有机器。','', '不建议继续把已有反例排除后重新宣称结构规则可靠。后续最有价值的验证是先冻结完整校准流程，再拿未见矩阵进行端到端验证，且计入校准成本。','', '本次实测校准成本对应的摊销次数很高，说明该方案更适合安装/离线验证一次后反复复用结果，而非每次执行或每个一次性矩阵都校准。没有实际足够的重复调用时，不应以计算阶段收益声称整体更快。']
(E/'筛选规则研究报告.md').write_text('\n'.join(lines)+'\n');(E/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
