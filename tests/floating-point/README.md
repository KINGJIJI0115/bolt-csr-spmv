# 特殊浮点正确性测试

本目录包含原始 `fp_guard.c`、循环计数采集脚本和独立运行入口。测试使用交付的 `frozen/csr_kernel.c` 与 `frozen/llvm-bolt`，重新编译测试程序、采集训练 Profile、执行 BOLT 分组变换并运行优化后的程序。不是只读取历史结果。

8 类数据包括普通有限值、正负零、次正规值、溢出、无穷、正负无穷混合、quiet NaN 和 signaling NaN；每类分别使用四种舍入模式，共 32 次组合。每次使用 1031 元素长行，对照按原顺序调用 `fma` 的参考计算，比较输出位模式和浮点异常标志。测试失败返回非零退出码。

加载交付镜像后，在 Linux / WSL 中执行（每次使用新的输出目录）：

```sh
mkdir -p results
docker run --rm --user "$(id -u):$(id -g)" \
  --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --tmpfs /tmp:rw,exec,size=256m \
  -v "$PWD/results:/results" --entrypoint python3 \
  bolt-loop-course:20261125-course-readable-final \
  /opt/course/tests/floating-point/run.py --out /results/floating-point
```

镜像已包含 GCC、Python 3 和 BOLT 插桩运行库 `/opt/loop-repro/libbolt_rt_instr.a`。本地 Linux 运行时，可用 `--runtime` 指定该运行库路径；需要支持 FMA 的 x86-64 CPU。成功结果见 `result.json`，编译、训练和改写日志均保留在输出目录。

`fp_guard.c` 与历史测试源码一致；计数采集脚本源自冻结版本，仅将 Python assert 转为显式异常，避免 Python 优化模式关闭检查。历史实验记录保持原样，本次运行产生独立结果。
