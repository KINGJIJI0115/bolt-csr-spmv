"""Default: target-machine calibration and held-out validation. Use fixed for full audit."""
import argparse, pathlib, json, hashlib, os, subprocess, struct, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
F = ROOT / 'frozen'

def sections(p):
    z = p.read_bytes()
    off = struct.unpack_from('<Q', z, 40)[0]
    (ent, n, si) = struct.unpack_from('<HHH', z, 58)
    ss = [struct.unpack_from('<IIQQQQIIQQ', z, off + i * ent) for i in range(n)]
    names = z[ss[si][4]:ss[si][4] + ss[si][5]]
    return {names[s[0]:].split(b'\x00')[0]: (s[3], hashlib.sha256(z[s[4]:s[4] + s[5]]).hexdigest()) for s in ss if s[2] & 4}

def acceptance_status(selected, failures):
    if failures:
        return 'needs_review'
    return 'validated' if selected else 'no_candidate_selected'

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', nargs='?', default='calibrate', choices=['verify', 'fixed', 'calibrate'])
    ap.add_argument('--out', default='/results/run')
    ap.add_argument('--cpu', type=int)
    ap.add_argument('--rounds', type=int, default=15, help='fixed mode only')
    ap.add_argument('--seconds', type=float, default=0.7, help='fixed mode only')
    a = ap.parse_args()
    cpus = sorted(os.sched_getaffinity(0))
    cpu = a.cpu if a.cpu is not None else cpus[0]
    if cpu not in cpus:
        ap.error('CPU is not available in the container affinity')
    if a.rounds < 2 or a.seconds <= 0:
        ap.error('rounds >=2 and seconds >0 required')
    if 'fma' not in pathlib.Path('/proc/cpuinfo').read_text().split():
        raise RuntimeError('x86-64 CPU with FMA required; do not emulate for timing')
    for (rel, h) in json.loads((ROOT / 'content-manifest.json').read_text()).items():
        if not hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == h:
            raise RuntimeError('Check failed: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == h' + ('; ' + str(rel)))
    O = pathlib.Path(a.out).resolve()
    O.mkdir(parents=True, exist_ok=False)
    (O / 'environment.txt').write_text(subprocess.check_output(['lscpu'], text=True) + '\nCPU affinity: ' + str(cpus) + '\nSelected CPU: ' + str(cpu))
    names = sorted((p.stem for p in (ROOT / 'data').glob('*.csr')))
    for v in ['pgo', 'new']:
        cmd = [str(F / 'llvm-bolt'), str(F / 'o3'), '-o', str(O / v), '--data=' + str(F / 'branch.fdata'), '--reorder-blocks=ext-tsp', '--reorder-functions=hfsort', '--split-functions']
        if v == 'new':
            cmd += ['--indirect-prefetch-mode=selected', '--indirect-prefetch-profile=' + str(F / 'selected.json')]
        with (O / (v + '-rewrite.log')).open('w') as log:
            subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
        if not sections(O / v) == sections(F / v):
            raise RuntimeError('Check failed: sections(O / v) == sections(F / v)' + ('; ' + str(v)))
    checks = []
    for n in names:
        hs = []
        for v in ['o3', 'pgo', 'new']:
            y = O / (n + '-' + v + '.y')
            exe = F / v if v == 'o3' else O / v
            subprocess.run(['taskset', '-c', str(cpu), str(exe), str(ROOT / 'data' / (n + '.csr')), '1', '61331', str(y)], check=True, stdout=subprocess.DEVNULL)
            hs.append(hashlib.sha256(y.read_bytes()).hexdigest())
        if not len(set(hs)) == 1:
            raise RuntimeError('Check failed: len(set(hs)) == 1' + ('; ' + str(n)))
        checks.append({'matrix': n, 'full_vectors_equal': True, 'sha256': hs[0]})
    (O / 'verification.json').write_text(json.dumps({'content_hashes_verified': True, 'rebuilt_executable_sections_equal': True, 'vectors': checks}, indent=2))
    if a.mode == 'verify':
        print('Verified rebuild and full outputs for all 15 matrices. No performance claim.')
        return
    if a.mode == 'fixed':
        for (label, seed) in [('a', 104729), ('b', 130363)]:
            subprocess.run([sys.executable, str(ROOT / 'scripts/confirm.py'), '--binary-dir', str(F), '--data', str(ROOT / 'data'), '--cases', *names, '--seed', str(seed), '--rounds', str(a.rounds), '--seconds', str(a.seconds), '--cpu', str(cpu), '--out', str(O / ('fixed-' + label + '.json'))], check=True)
        batches = [json.loads((O / ('fixed-' + s + '.json')).read_text()) for s in ['a', 'b']]
        lines = ['# 固定对照实验结果', '', '下表比较优化前后的 SpMV 计算耗时。正数表示耗时减少，负数表示回退；方括号内为 95% 置信区间，用于观察测量波动。A、B 对应两批测试。', '', '|矩阵|相对常规BOLT：A|相对常规BOLT：B|相对O3：A|相对O3：B|', '|---|---:|---:|---:|---:|']
        for n in names:
            cells = [n]
            for base in ['pgo', 'o3']:
                for b in batches:
                    r = b['cases'][n][base]
                    cells.append(f"{r['time_reduction_pct']:+.2f}% [{r['ci95'][0]:+.2f}, {r['ci95'][1]:+.2f}]")
            lines.append('|' + '|'.join(cells) + '|')
        lines += ['', '完整计时保存在 fixed-a.json 和 fixed-b.json，机器配置见 environment.txt。', '', '## 补充说明', '', '本表统计完整 SpMV 计算阶段，未计入加载、分配、参考校验及校准成本。不同机器和运行负载会影响结果；低轮数快速检查用于确认入口，正式分析使用完整重复实验。全部矩阵的正负结果均保留。']
        (O / 'report.md').write_text('\n'.join(lines) + '\n')
    else:
        D = O / 'calibration-data'
        D.mkdir()
        scope = []
        for n in names:
            with (ROOT / 'data' / (n + '.csr')).open('rb') as f:
                (magic, rows, cols, nnz) = struct.unpack('<4Q', f.read(32))
                ptr = struct.unpack('<' + str(rows + 1) + 'Q', f.read(8 * (rows + 1)))
            if not (magic == 3553977016699409236 and ptr[0] == 0 and (ptr[-1] == nnz)):
                raise RuntimeError('Check failed: magic == 3553977016699409236 and ptr[0] == 0 and (ptr[-1] == nnz)')
            lengths = sorted((ptr[i + 1] - ptr[i] for i in range(rows)))
            if not (not lengths or lengths[0] >= 0):
                raise RuntimeError('Check failed: not lengths or lengths[0] >= 0')

            def quantile(q):
                pos = (rows - 1) * q
                i = int(pos)
                return lengths[i] + (lengths[min(i + 1, rows - 1)] - lengths[i]) * (pos - i)
            median = quantile(0.5)
            p99 = quantile(0.99)
            fraction = sum((x > 16 for x in lengths)) / rows
            eligible = 24 <= median <= 64 and p99 <= 128 and (fraction >= 0.8) and (cols * 8 <= 262144)
            scope.append({'matrix': n, 'eligible': eligible, 'median': median, 'p99': p99, 'long_fraction': fraction, 'vector_bytes': cols * 8})
            if eligible:
                (D / (n + '.csr')).symlink_to(ROOT / 'data' / (n + '.csr'))
        (O / 'structural-screen.json').write_text(json.dumps(scope, indent=2))
        subprocess.run([sys.executable, str(ROOT / 'scripts/gate.py'), '--frozen', str(F), '--data', str(D), '--out', str(O / 'calibration'), '--cpu', str(cpu)], check=True)
        subprocess.run([sys.executable, str(ROOT / 'scripts/verify_profiles.py'), '--frozen', str(F), '--out', str(O / 'calibration')], check=True)
        results = json.loads((O / 'calibration/results.json').read_text())
        evaluation = json.loads((O / 'calibration/evaluation.json').read_text())['decisions']

        def fmt(r):
            return f"{r['gain_pct']:+.2f}% [{r['ci95'][0]:+.2f}, {r['ci95'][1]:+.2f}]"
        lines = ['# 自动校准结果', '', '程序先运行两批测试，比较优化候选与常规 BOLT，再根据收益选择版本。选择确定后，第三批检查它的实际表现。下表保留每个候选的成绩，正数表示 SpMV 计算耗时减少，负数表示回退；方括号内为 95% 置信区间。', '', '|矩阵|第一批校准|第二批校准|选择结果|第三批候选收益|校准耗时(秒)|', '|---|---:|---:|---|---:|---:|']
        failures = []
        for (n, d) in evaluation.items():
            r = results[n]
            lines.append('|' + '|'.join([n, fmt(r['cal-a']), fmt(r['cal-b']), '开启' if d['enabled'] else '常规BOLT', fmt(r['validation']), f"{d['calibration_wall_seconds']:.2f}"]) + '|')
            if d['enabled'] and r['validation']['ci95'][0] <= 0:
                failures.append(n)
        skipped = [r['matrix'] for r in scope if not r['eligible']]
        lines += ['', '结构筛选跳过的矩阵：' + ', '.join(skipped) + '。运行 fixed 可查看全部矩阵的固定对照结果。', '', '第三批中需要复查的已选项目：' + (', '.join(failures) or '无') + '。', '', '生成的程序位于 calibration/rewritten/，选择记录位于 calibration/frozen-decisions.json。', '', '## 补充说明', '', '收益对应 SpMV 计算阶段，校准耗时单独列出；加载等开销未计入，本文未测试端到端收益。“常规BOLT”表示采用基线代码，表中仍显示优化候选自身的成绩。第三批只检查已保存的选择，出现需复查项目时应结合原始数据审查。更换数据或重要环境后需重新验证。']
        (O / 'report.md').write_text('\n'.join(lines) + '\n')
        selected = [n for (n, d) in evaluation.items() if d['enabled']]
        status = acceptance_status(selected, failures)
        lines += ['', '验收状态：' + status + '。']
        (O / 'report.md').write_text('\n'.join(lines) + '\n')
        (O / 'acceptance.json').write_text(json.dumps({'status': status, 'exit_code': 2 if failures else 0, 'mode': 'calibrate', 'candidate_count': len(evaluation), 'structural_skipped': skipped, 'selected': [n for (n, d) in evaluation.items() if d['enabled']], 'selected_without_positive_validation_ci': failures, 'validation_used_for_selection': False, 'end_to_end_test': False}, indent=2))
        if failures:
            print('Needs review: third-batch validation; results saved:', O, file=sys.stderr)
            return 2
    print('Complete:', O)
    return 0
if __name__ == '__main__':
    sys.exit(main())
