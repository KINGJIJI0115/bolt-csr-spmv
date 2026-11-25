# v1.0.0 — 课程提交版本（2026-11-25）

基于 LLVM BOLT 的 CSR SpMV 标量 FMA 4× 循环分组优化。提供源码 patch、设计文档、目标机自动校准和固定全量对照入口。

请下载 Assets 中的 `bolt-csr-spmv-v1.0.0-20261125.zip` 和 `RELEASE-SHA256SUMS.txt`。自动生成的 Source code 压缩包不含复现所需的大文件。

完整附件包括已验收 Docker 镜像、15 个矩阵、冻结程序、源码、脚本和全部实验记录。校验 ZIP 后解压，进入 `course-submission-readable-20261124`，按 README 执行 `docker load` 和默认验收。

本轮交付通过 15 矩阵重建与输出核验、32 次特殊浮点组合及完整默认校准，选中 bcsstk14～17，第三批全部通过。历史实验结果原样保留，具体性能随目标机器和系统负载变化。测量范围为 SpMV 计算阶段，未做端到端测试。
