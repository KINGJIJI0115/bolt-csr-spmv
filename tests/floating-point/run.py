"""Compile and test the original and BOLT-rewritten scalar FMA loop."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    ap.add_argument('--runtime', default='/opt/loop-repro/libbolt_rt_instr.a')
    a = ap.parse_args()
    out = pathlib.Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    tool = ROOT / 'frozen/llvm-bolt'
    original = out / 'original'

    def run(args, name):
        p = subprocess.run([str(x) for x in args], capture_output=True, text=True)
        (out / (name + '.log')).write_text(p.stdout + p.stderr)
        p.check_returncode()
        return p.stdout

    run(['gcc', '-O3', '-mfma', '-g', '-fno-pie', '-no-pie', '-Wl,--emit-relocs',
         ROOT / 'frozen/csr_kernel.c', HERE / 'fp_guard.c', '-lm', '-o', original], 'compile')
    run([sys.executable, HERE / 'collect.py', '--tool', tool, '--input', original,
         '--out', out / 'trip', '--single-threaded'], 'collect')
    expected = json.loads((out / 'trip/baseline.stdout').read_text())
    if expected != json.loads((out / 'trip/instrumented.stdout').read_text()):
        raise RuntimeError('Training changed floating-point test results')
    profile = json.loads((out / 'trip/trip-profile.json').read_text())
    targets = [r for r in profile['loops'] if r['function'] == 'spmv']
    if len(targets) != 1:
        raise RuntimeError('Expected exactly one recognized spmv loop')
    for r in profile['loops']:
        r['selected'] = r in targets
    (out / 'selected.json').write_text(json.dumps(profile, indent=2))
    run([tool, original, '-o', out / 'instrumented', '--instrument',
         '--instrumentation-file=' + str(out / 'branch.fdata'),
         '--runtime-instrumentation-lib=' + a.runtime], 'branch')
    if json.loads(run([out / 'instrumented'], 'branch-run')) != expected:
        raise RuntimeError('Branch instrumentation changed test results')
    run([tool, original, '-o', out / 'optimized', '--data=' + str(out / 'branch.fdata'),
         '--reorder-blocks=ext-tsp', '--reorder-functions=hfsort', '--split-functions',
         '--indirect-prefetch-mode=selected',
         '--indirect-prefetch-profile=' + str(out / 'selected.json')], 'rewrite')
    if json.loads(run([out / 'optimized'], 'optimized-run')) != expected:
        raise RuntimeError('Rewritten binary changed test results')
    record = {'result': expected, 'selected_loops': len(targets),
              'source_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
              'tool_sha256': hashlib.sha256(tool.read_bytes()).hexdigest()}
    (out / 'result.json').write_text(json.dumps(record, indent=2))
    print(json.dumps(record))

if __name__ == '__main__':
    main()
