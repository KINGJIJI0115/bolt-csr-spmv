# LLVM BOLT：CSR SpMV 标量 FMA 循环分组优化

本课程项目在 LLVM BOLT 中实现两阶段 Profile 驱动的 4× 循环分组变换。优化减少长行内循环的控制指令，保持原有浮点累加顺序；配套结构筛选与目标机器双批校准，用第三批独立测试复查选择结果。

## 阅读与下载

- [设计文档](设计文档.md)：问题、优化设计、实现、实验和局限性。
- [代码补丁](grouped-fma-loop.patch)：基于 LLVM 提交 `37a8dd4eb2d22ffe4ed1f71b3f0b5aa6df7c7820`。
- [下载与复现指南](DOWNLOAD.md)：下载完整附件、校验、加载 Docker 和运行验收。
- [完整复现说明](复现说明.md)：验收模式、输出说明及源码构建命令。
- [本次交付验证](validation/final-20261125/收尾记录.md)与[验收结果](validation/final-20261125/acceptance/acceptance.json)。
- [第三方来源](THIRD_PARTY_NOTICES.md)与[仓库内容说明](CONTENTS.md)。

**下载入口：** [完整交付 ZIP](https://github.com/KINGJIJI0115/bolt-csr-spmv/releases/download/v1.0.0/bolt-csr-spmv-v1.0.0-20261125.zip) · [附件校验清单](https://github.com/KINGJIJI0115/bolt-csr-spmv/releases/download/v1.0.0/RELEASE-SHA256SUMS.txt) · [v1.0.0 Release 页面](https://github.com/KINGJIJI0115/bolt-csr-spmv/releases/tag/v1.0.0)

**开始复现：打开本仓库右侧 Releases，选择 `v1.0.0`，下载 `bolt-csr-spmv-v1.0.0-20261125.zip` 和 `RELEASE-SHA256SUMS.txt`。** GitHub 自动生成的 `Source code.zip` / `Source code.tar.gz` 只包含精简仓库，不是完整交付包。

**完整附件已包含全部 15 个测试矩阵、预构建 Docker 镜像及运行依赖。下载解压后即可按说明复现，无需额外下载数据，也无需自行构建基础镜像。**

附件同时保留冻结程序、源码、全部实验记录和测试入口，无需 Git LFS。运行环境需具备 Docker 和支持 FMA 的 x86-64 CPU。

## 项目与实验范围

支持已识别的 x86-64 标量 double FMA CSR SpMV 内循环。默认流程依次进行正确性检查、矩阵结构筛选、两批校准、冻结选择、第三批独立复查。性能指标为完整 SpMV 计算阶段的耗时降低百分比，以常规 BOLT 为主要对照，同时保留相对原始 `-O3` 的固定实验。

### 核心实验结果速览

| 评估维度 | 负载范围 / 测试覆盖 | 实测表现 |
| :--- | :--- | :--- |
| **结构工程矩阵** | `bcsstk14`～`17`、`msc00726`（双平台） | 相对常规 BOLT 耗时降低 **+2.57%～+12.44%**；相对 `-O3` 净降低 **+2.52%～+6.01%**，两机校准均启用 |
| **三角网格矩阵** | `s1rmt3m1`～`s3rmt3m3`（双平台） | Xeon 服务器相对常规 BOLT 耗时降低 **+5.51%～+6.47%**（相对 `-O3` **+6.00%～+7.12%**），自动启用；Core Ultra 9 未达 2% 门槛自动回落 |
| **防回退门控** | 四边形网格 `s1rmq4m1`～`s3rmq4m1` 与 `rail*` | 两机 **3/3** 四边形网格回退候选均被校准跳过，铁路调度负载由结构初筛跳过；启用项第三批复查均保持正收益区间（0 例需复查） |
| **正确性核验** | 15 矩阵全量向量 + 32 次特殊浮点组合 | 8 类浮点数据 × 4 种 IEEE-754 舍入模式位级与异常标志一致；15 矩阵现场重建可执行节及输出向量 SHA-256 逐字节一致 |

历史两机实验的正负结果全部保留在 `evidence/`。2026-11-25 收尾验收完成 15 矩阵重建与输出校验，32 次特殊浮点组合通过；本轮选中 `bcsstk14`～`17`，第三批均通过。收尾结果独立保存，不替换历史实验数据。

## 目录与校验

本仓库用于阅读源码、报告和实验记录，大体积的矩阵、工具和生成二进制位于 Release 完整附件。仅克隆本仓库不能直接运行完整校准入口。

Linux / WSL 下运行 `sha256sum -c REPOSITORY-SHA256SUMS.txt` 可校验仓库文件。完整交付包及下载附件的校验方法见 [DOWNLOAD.md](DOWNLOAD.md)。`.gitattributes` 禁用换行自动转换，以保持校验值。

Dockerfile 的归档副本位于 `packaging/`，它依赖开发时的本地基础镜像；不是从空环境构建的入口。验收请使用 `docker load`，源码补丁构建步骤见复现说明。

## 补充说明

具体耗时和选择结果随 CPU、系统负载而变化。`validated` 表示本轮选中项均通过第三批复查；`no_candidate_selected` 表示本轮采用常规 BOLT；`needs_review` 会保存记录并返回退出码 2，不自动改选。本项目未测试端到端收益。

AI 工具辅助了方案讨论、部分代码与实验脚本编写、实验执行及数据整理；提交者负责项目目标制定、技术方案取舍以及实现与结论的审核。
