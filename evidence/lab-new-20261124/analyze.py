import pathlib,json
E=pathlib.Path(__file__).resolve().parent
a=json.loads((E/'batch-a.json').read_text());b=json.loads((E/'batch-b.json').read_text());env=json.loads((E/'environment.json').read_text());v=json.loads((E/'verified-content.json').read_text())
extra=json.loads((E/'rewrite-and-vector-checks.json').read_text());assert extra['recreated_executable_sections_identical'] and all(x['all_five_bitwise_equal'] for x in extra['vectors'].values())
locals=[json.loads((E.parent/n).read_text()) for n in ['holdout-host.json','holdout-container.json']]
assert a['binaries']==b['binaries']==locals[0]['binaries']==locals[1]['binaries']
for remote,local in zip([a,b],locals):
 assert remote['seed']==local['seed']
 for name in remote['cases']:
  hr={r['output_hash'] for r in remote['records'] if r['case']==name};hl={r['output_hash'] for r in local['records'] if r['case']==name};assert hr==hl and len(hr)==1
def fmt(x):return f"{x['time_reduction_pct']:+.2f}% [{x['ci95'][0]:+.2f}, {x['ci95'][1]:+.2f}]"
lines=['# 学校服务器跨机器复现报告','', '服务器：lab-new，Intel Xeon Gold 6133，Ubuntu 22.04。对照本机：Core Ultra 9 275HX / WSL Ubuntu 22.04。日期：2026-11-24。','', '目录：`/home/ubuntu/hdd2/zxz/bolt-group4-repro-20261124`。原有服务未停止，原有文件未修改。镜像安装使用Docker默认存储；镜像压缩包、脚本、日志与结果放在独立实验目录。','', '## 方法','', '固定同一Docker镜像、程序、矩阵与优化参数；压缩包SHA256、容器内冻结文件及CSR数据SHA256全部通过。没有重新编译或按服务器结果调参。','', 'CPU固定为逻辑CPU2，属于NUMA节点0；它的超线程伙伴为CPU42，采样时空闲。容器限制CPU2、内存节点0、4GiB内存，无网络、只读根文件系统，结果目录可写。这限制本次任务资源，不代表独占CPU或排除系统干扰。','', '两批各15轮随机配对，种子分别104729/130363，与本机两个独立矩阵批次对应。每轮对照原始O3、相同训练的常规BOLT、旧候选、新候选。完整SpMV计算阶段计时，不含加载/分配/校验，不是进程总耗时。','', '正值代表耗时降低，括号内为配对bootstrap 95%区间。没有删除负结果或慢样本。','', '## 相对常规BOLT的结果','', '|矩阵|本机第一批|本机第二批|服务器第一批|服务器第二批|','|---|---:|---:|---:|---:|']
for n in a['cases']:lines.append(f"|{n}|{locals[0]['cases'][n]['pgo']['time_reduction_pct']:+.2f}%|{locals[1]['cases'][n]['pgo']['time_reduction_pct']:+.2f}%|{fmt(a['cases'][n]['pgo'])}|{fmt(b['cases'][n]['pgo'])}|")
lines+=['','## 相对原始O3的结果','','|矩阵|服务器第一批|服务器第二批|','|---|---:|---:|']
for n in a['cases']:lines.append(f"|{n}|{fmt(a['cases'][n]['o3'])}|{fmt(b['cases'][n]['o3'])}|")
positive=[n for n in a['cases'] if all(q['cases'][n]['pgo']['ci95'][0]>0 for q in [a,b])]
negative=[n for n in a['cases'] if all(q['cases'][n]['pgo']['ci95'][1]<0 for q in [a,b])]
summary={'frozen_binaries_identical':True,'matrix_hashes_verified':True,'output_hashes_identical_to_local_both_seeds':True,'two_batches_positive_vs_bolt':positive,'two_batches_negative_vs_bolt':negative,'cases':{n:{'a':a['cases'][n],'b':b['cases'][n]} for n in a['cases']}}
lines+=['','## 判断与限制','',f"相对常规BOLT，两批区间均高于零：{', '.join(positive) or '无'}。两批区间均低于零：{', '.join(negative) or '无'}。其他场景按原始区间判断，不能简单当作确定获益或零回退。",'', '所有计时调用的内部完整向量参考检查通过；四种变体每轮输出hash一致，且与本机相同种子下的输出hash一致。冻结程序哈希跨机器一致。','', '这提供了第二种CPU上的实测证据，但仍只有两台机器、同一份标量FMA CSR程序和四个独立真实矩阵；不能外推到所有CPU、编译器或任意CSR程序。服务器为共享环境，测试前后负载记录保留。','', '本次仅复现冻结版本，不根据服务器成绩修改参数或替换矩阵。完整原始记录见batch-a.json、batch-b.json；命令、环境、容器导入日志与哈希验证结果均保留。']
(E/'跨机器复现报告.md').write_text('\n'.join(lines)+'\n');(E/'comparison.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='cases'},ensure_ascii=False))
with (E/'跨机器复现报告.md').open('a') as f:
 f.write('\n## 服务器重建与完整向量验证\n\n镜像内llvm-bolt成功在服务器上重新改写冻结O3输入，使用原训练profile与原选项；重建产物的所有可执行节与本机冻结优化产物完全一致。四个矩阵在O3、常规BOLT、旧候选、新候选、服务器重建版本下完整输出向量逐字节一致，向量SHA256也与本机相同种子的记录一致。详见rewrite-and-vector-checks.json和rewrite.log。\n\n## 本次复现的实际结论\n\nbcsstk17的正收益跨两种CPU保持，但服务器约2.6%～2.8%，低于本机约5.7%～5.8%。rail2536在服务器仅约0.4%～0.8%，没有复现本机约5%的明显收益。小型铁路矩阵有不足0.4%的回退，不能写成所有场景均无回退。可复现性检查通过不等于性能百分比保持；当前应按硬件和负载限定收益。此次没有调整候选或修改旧交付。\n')
for n in a['cases']:print(n,'BOLT',fmt(a['cases'][n]['pgo']),fmt(b['cases'][n]['pgo']),'O3',fmt(a['cases'][n]['o3']),fmt(b['cases'][n]['o3']))
