import pathlib,shutil,json
E=pathlib.Path(__file__).resolve().parent;P=pathlib.Path('/home/jiji/prefetch-indirect-pilot/real-csr-opt')
D=P/'selection-study-data';D.mkdir(exist_ok=False)
paths=list((P/'other-series-data').glob('*.csr'))+list((P/'specialized-data').glob('*.csr'))+[P/'holdout-data/bcsstk17.csr']
assert len(paths)==12
for p in paths:shutil.copy2(p,D/p.name)
shutil.copytree(D,E/'data')
(E/'预先声明.md').write_text('''# 目标机器校准规则验证

固定四项结构条件作为候选范围，不添加矩阵名或拟合后的新结构阈值。此前所有计时已经看过，12个矩阵均属于已见数据，本轮不能作为新矩阵泛化验证。

固定两批新种子32452843/49979687进行校准，每批12轮随机配对，单变体目标0.25秒、最多30000次调用。只有两批相对常规BOLT的耗时减少均至少2%，且各自配对bootstrap 95%区间下界大于1%，才选择优化版本；否则选择常规BOLT。阈值是保守工程裕量，不是通过因果分析推导的最优值。

两批结束后将选择写入 frozen-decisions.json。第三批新种子67867967只用于检查选择结果，不可据此修改选择。两台机器各自校准，规则相同但允许选择不同。验证保留被拒绝候选的实际优化结果，不能把未选择记成优化算法自身没有回退。

保持原程序、训练profile和工具不变。本轮检验短测选择的重复性，不证明新矩阵、运行环境变化或任意机器都有效。成本为离线扫描、生成候选及校准；校准墙钟时间单独记录，计算阶段收益不包含这些成本。只有长期重复使用数据、足以摊销成本时才适用。
''')
