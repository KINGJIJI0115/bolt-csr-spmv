# LLVM BOLT：CSR SpMV 标量 FMA 循环分组与短尾展开优化

本课程项目基于 LLVM BOLT 主线提交 `37a8dd4e` 设计并实现了两阶段 Profile 驱动的 **4× 保序循环分组**（`v1.0.0`）与 **1～4 阶梯式短尾展开**（`v1.1.0`，选项 `--grouped-fma-peel-tail`）二进制优化 Pass，并配套结构筛选与目标机器三路自适应校准，在严格保持 IEEE-754 浮点累加顺序与逐字节正确性的前提下提升 CSR SpMV 性能并避免回退。

## 文档导航与快速下载

- [设计文档](设计文档.md)：完整阐述问题动机、4× 分组与 1～4 短尾展开设计、BOLT 实现细节、双平台 19 矩阵实验验证及局限性。
- [版本变更说明](CHANGELOG.md)：`v1.0.0` 到 `v1.1.0` 的增量功能与性能演进总结。
- [代码补丁](grouped-fma-loop.patch)：基于 LLVM 主线提交 `37a8dd4eb2d22ffe4ed1f71b3f0b5aa6df7c7820` 的完整统一补丁（含默认 4× 分组与 `--grouped-fma-peel-tail`）。
- [下载与复现指南](DOWNLOAD.md)：下载 `v1.1.0` 完整附件、校验 SHA-256、加载 Docker 镜像并运行验收。
- [完整复现说明](复现说明.md)：Docker 三模式入口、BOLT 命令行开关、源码构建步骤及输出文件说明。
- [交付核验记录](validation/交付核验记录.md) · [安全性测试源码](tests/README.md) · [第三方来源](THIRD_PARTY_NOTICES.md) · [仓库内容说明](CONTENTS.md)。

**最新版本下载（`v1.1.0`）：** [完整交付 ZIP](https://github.com/KINGJIJI0115/bolt-csr-spmv/releases/download/v1.1.0/bolt-csr-spmv-v1.1.0-complete.zip) · [附件校验值](https://github.com/KINGJIJI0115/bolt-csr-spmv/releases/download/v1.1.0/bolt-csr-spmv-v1.1.0-complete.zip.sha256) · [v1.1.0 Release 页面](https://github.com/KINGJIJI0115/bolt-csr-spmv/releases/tag/v1.1.0)  
*(历史基础版本 `v1.0.0` 继续保留于 [v1.0.0 Release 页面](https://github.com/KINGJIJI0115/bolt-csr-spmv/releases/tag/v1.0.0)。)*

> **复现提示**：请下载 Release Assets 中的完整 ZIP 与 `.sha256` 校验文件；GitHub 自动生成的 `Source code.zip` / `Source code.tar.gz` 仅包含精简仓库，不含大体积复现资产。完整附件已内置预构建 Docker 镜像、全部 19 个 CSR 测试矩阵、冻结工具、安全性测试及完整实验记录，下载解压后无需额外下载数据或基础镜像即可复现。

## 核心实验结果速览

性能指标为完整 CSR SpMV 计算阶段的耗时降低百分比 $100 \times (1 - T_{\text{new}}/T_{\text{base}})$，以常规 BOLT（`pgo`）为主基线，并保留相对原始 GCC `-O3` 的对照结果。

| 评估维度 | 负载范围 / 测试覆盖 | 实测表现 |
| :--- | :--- | :--- |
| **结构工程矩阵** | 本轮自动选择的结构工程负载（双平台） | 相对常规 BOLT：本机 **+3.52%～+11.86%**，Xeon **+2.02%～+5.21%**。容器复测点估计 **+2.37%～+12.57%**，区间另见核验记录；`bcsstk27` 在 Xeon 与容器中由 `tail` 新增启用 |
| **三角网格矩阵** | `s1rmt3m1`、`s2rmt3m1`、`s3rmt3m1`、`s3rmt3m3` | 本轮 Xeon 自动选择 `old`，相对常规 BOLT **+5.81%～+6.31%**；本机自动选择 `tail`，相对常规 BOLT **+1.61%～+2.79%**，相对固定 4× 增量 **+0.93%～+1.58%** |
| **三路防回退门控** | 19 矩阵（16 项入围校准，3 项 `rail*` 结构跳过） | 启用覆盖达 **12/16**（本机）、**13/16**（容器复测）、**11/16**（Xeon）；两机 **3/3** 四边形网格回退候选均安全回落常规 BOLT，新增切换到 `tail` 的项目第三批增量复查 **全部通过** |
| **严格正确性与兼容性** | 19 矩阵四变体 + 4097 边界 + 32 次浮点测试 | 8 类浮点数据 × 4 种 IEEE-754 舍入模式（共 32 次）位级与异常标志一致；19 矩阵四变体输出 SHA-256 逐字节一致；关闭 `--grouped-fma-peel-tail` 时与 `v1.0.0` 可执行节逐字节一致 |

## 仓库结构与校验

本仓库面向源码审查、设计文档与实验结果查阅；大体积的 19 个 CSR 矩阵、预构建 Docker 镜像及冻结 ELF 可执行文件统一存放于 Release 完整附件中（详见 [CONTENTS.md](CONTENTS.md)）。

- Linux / WSL 下在仓库根目录执行 `sha256sum -c REPOSITORY-SHA256SUMS.txt` 可校验本仓库全部文件；完整交付包的校验步骤见 [DOWNLOAD.md](DOWNLOAD.md)。
- 复现验收请直接加载 Release 附件中的预构建 Docker 镜像（`docker load`）；从 LLVM 主线源码应用补丁构建 `llvm-bolt` 的步骤见 [复现说明.md](复现说明.md)（`packaging/` 中保留镜像封装用的 Dockerfile 归档）。

## 验收状态说明

具体耗时与自动选择策略随目标 CPU 与系统负载变化。默认校准入口输出 `status.json`：`validated` 表示新增切换到 `tail` 的项目均通过第三批相对原选择策略的增量收益复查；若这些新增升级项的区间下界不大于 0，则标记为 `needs_review` 并以非零退出码提示审查，不自动改选。沿用 `old` 或 `pgo` 的项目不参与这项自动增量判定，其相对常规 BOLT 的结果另见原始记录。

容器第三批中，沿用 `old` 的 `bcsstk16` 相对常规 BOLT 的耗时降低点估计为 **+2.47%**，95% 区间为 **[-2.88%, +5.32%]**。本轮将其记录为测量波动跨过零点，不计为新增 `tail` 升级项；`validated` 的含义以增量复查范围为准。

提交者负责项目目标制定、技术方案取舍以及代码实现与实验结论的审核；AI 工具辅助了方案讨论、部分代码与实验脚本编写、实验执行及数据整理。
