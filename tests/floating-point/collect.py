import argparse, pathlib, subprocess, struct, json, os, re, hashlib
ap = argparse.ArgumentParser()
ap.add_argument('--tool', required=True)
ap.add_argument('--input', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--single-threaded', action='store_true', required=True)
ap.add_argument('args', nargs=argparse.REMAINDER)
a = ap.parse_args()
R = pathlib.Path(a.out)
R.mkdir(exist_ok=False, parents=True)
src = pathlib.Path(a.input).resolve()
tool = pathlib.Path(a.tool).resolve()
original = src.read_bytes()
if not (original[:4] == b'\x7fELF' and original[4:6] == bytes([2, 1]) and (original[16:18] == b'\x02\x00')):
    raise RuntimeError("Check failed: original[:4] == b'\\x7fELF' and original[4:6] == bytes([2, 1]) and (original[16:18] == b'\\x02\\x00')")
exe = R / 'instrumented'
cmd = [str(tool), str(src), '-o', str(exe), '--reorder-blocks=none', '--indirect-prefetch-mode=trip-train', '--runtime-lib-init-hook=init']
p = subprocess.run(cmd, capture_output=True, text=True)
(R / 'rewrite.log').write_text(p.stdout + p.stderr)
if not p.returncode == 0:
    raise RuntimeError('Check failed: p.returncode == 0')
loops = []
for line in p.stdout.splitlines():
    m = re.fullmatch('TRIP-TRAIN __bolt_trip_(\\d+) function (.+) offset (\\d+)', line)
    if m:
        loops.append({'index': int(m[1]), 'function': m[2], 'offset': int(m[3])})
if not (loops and [r['index'] for r in loops] == list(range(len(loops)))):
    raise RuntimeError("Check failed: loops and [r['index'] for r in loops] == list(range(len(loops)))")
raw = exe.read_bytes()
so = struct.unpack_from('<Q', raw, 40)[0]
(se, sn, si) = struct.unpack_from('<HHH', raw, 58)
sh = [struct.unpack_from('<IIQQQQIIQQ', raw, so + i * se) for i in range(sn)]
strings = raw[sh[si][4]:sh[si][4] + sh[si][5]]
sec = next((r for r in sh if strings[r[0]:].split(b'\x00')[0] == b'.bolt.tripcounts'))
if not sec[5] == 192 * len(loops):
    raise RuntimeError('Check failed: sec[5] == 192 * len(loops)')
code = '#include <stdio.h>\n#include <stdlib.h>\n__attribute__((destructor)) static void dump(void){const char*p=getenv("BOLT_TRIP_OUTPUT");if(!p)_Exit(90);FILE*f=fopen(p,"wb");if(!f)_Exit(91);if(fwrite((void*)' + hex(sec[3]) + ',1,' + str(sec[5]) + ',f)!=' + str(sec[5]) + ')_Exit(92);if(fclose(f))_Exit(93);}\n'
(R / 'dump.c').write_text(code)
subprocess.run(['gcc', '-shared', '-fPIC', str(R / 'dump.c'), '-o', str(R / 'dump.so')], check=True)
argv = a.args[1:] if a.args[:1] == ['--'] else a.args
baseline = subprocess.run([str(src), *argv], capture_output=True, check=True)
env = dict(os.environ, LD_PRELOAD=str((R / 'dump.so').resolve()), BOLT_TRIP_OUTPUT=str((R / 'counts.bin').resolve()))
run = subprocess.run([str(exe), *argv], env=env, capture_output=True, check=True)
(R / 'baseline.stdout').write_bytes(baseline.stdout)
(R / 'instrumented.stdout').write_bytes(run.stdout)
(R / 'instrumented.stderr').write_bytes(run.stderr)
counts = (R / 'counts.bin').read_bytes()
if not len(counts) == sec[5]:
    raise RuntimeError('Check failed: len(counts) == sec[5]')
for r in loops:
    (n, it, pre, tail, long, odd, h1, h2, h3, h4, lo, hi, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16) = struct.unpack_from('<24Q', counts, r['index'] * 192)
    if not (pre + tail == it and long + odd <= n and (pre % 2 == 0) and (not long or pre >= 2 * long) and (tail >= n)):
        raise RuntimeError('Check failed: pre + tail == it and long + odd <= n and (pre % 2 == 0) and (not long or pre >= 2 * long) and (tail >= n)')
    r['counts'] = {'entries': n, 'iterations': it, 'prefetch_iterations': pre, 'plain_iterations': tail, 'eligible_entries': long, 'odd_long_entries': odd, 'peel_exit_1': h1, 'peel_exit_2': h2, 'peel_exit_3': h3, 'peel_exit_4': h4, 'local_low': lo, 'local_high': hi, 'peel_exit_5': h5, 'peel_exit_6': h6, 'peel_exit_7': h7, 'peel_exit_8': h8, 'peel_exit_9': h9, 'peel_exit_10': h10, 'peel_exit_11': h11, 'peel_exit_12': h12, 'peel_exit_13': h13, 'peel_exit_14': h14, 'peel_exit_15': h15, 'peel_exit_16': h16}
    r['selected'] = False
profile = {'schema': 'bolt-group-u4-d0-m16-h2-v1', 'single_threaded_training': True, 'source_sha256': hashlib.sha256(original).hexdigest(), 'tool_sha256': hashlib.sha256(tool.read_bytes()).hexdigest(), 'distance': 0, 'unroll': 4, 'loops': loops, 'command': argv, 'selection': 'not performed'}
(R / 'trip-profile.json').write_text(json.dumps(profile, indent=2))
print(json.dumps(profile, indent=2))
