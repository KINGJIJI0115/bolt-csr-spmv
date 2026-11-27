# 下载与复现指南（`v1.1.0`）

## 1. 下载完整附件

打开仓库右侧 Releases，进入 **`v1.1.0`**，在 Assets 中下载以下两份文件至同一目录：

- `bolt-csr-spmv-v1.1.0-complete.zip`（约 998.5 MB）
- `bolt-csr-spmv-v1.1.0-complete.zip.sha256`

请勿用 GitHub 自动生成的 `Source code.zip` / `Source code.tar.gz` 替代完整附件。完整附件已内置完整五段式 `设计文档.md`、预构建 Docker 镜像、全部 19 个 CSR 矩阵、冻结二进制、安全性测试与完整实验记录。

## 2. 校验与解压

Linux / WSL：

```sh
sha256sum -c bolt-csr-spmv-v1.1.0-complete.zip.sha256
unzip bolt-csr-spmv-v1.1.0-complete.zip
sha256sum -c RELEASE-SHA256SUMS.txt
cd v1.1.0-rc1
sha256sum -c SHA256SUMS.txt
```

Windows PowerShell 也可先校验并解压，随后在 WSL 中进入解压后的 `v1.1.0-rc1` 目录运行 Docker 命令：

```powershell
Get-FileHash .\bolt-csr-spmv-v1.1.0-complete.zip -Algorithm SHA256
Expand-Archive .\bolt-csr-spmv-v1.1.0-complete.zip -DestinationPath .\unpacked
```

## 3. 加载镜像并运行默认验收（三路校准 + 全量正确性核验）

需使用支持 FMA 的 x86-64 CPU 与 Linux Docker 环境（Windows 可通过 WSL2 使用）。发布说明与最新设计文档位于 ZIP 根目录；`v1.1.0-rc1/` 是保持原样的已核验运行包。发布版本为 `v1.1.0`，内部镜像标签继续使用 `1.1.0-rc1`。进入解压目录 `v1.1.0-rc1` 后执行：

```sh
docker load -i course-tail-v1.1.0-rc1.docker.tar.gz
mkdir -p results
docker run --rm --user "$(id -u):$(id -g)" \
  --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --memory 4g --pids-limit 128 \
  -v "$PWD/results:/results" bolt-csr-spmv:1.1.0-rc1 \
  --out /results/acceptance
```

默认入口会依次完成：**内容哈希校验 → 使用 `llvm-bolt` 现场重建 `pgo`/`old`/`tail` 并核对可执行节 → 19 矩阵四变体逐字节输出核验 → 4097 行长边界与 32 次特殊浮点测试 → 矩阵结构初筛 → 16 候选两批三路校准与冻结决策 → 第三批独立复查**。

- 多次运行时请更换输出目录名（如 `/results/acceptance-2`）；
- 可在镜像名之前加入 `--cpuset-cpus 2`（或在命令末尾加 `--cpu 2`）指定较空闲的逻辑 CPU 核心；
- 主要结果位于 `results/acceptance/status.json`、`verification.json`、`calibration/frozen-decisions.json` 与 `calibration/evaluation.json`。

## 4. 独立审查入口

在前述 `docker run` 命令末尾替换参数即可切换模式：

| 目的 | 末尾参数 |
| :--- | :--- |
| 仅重建并核验全部 19 矩阵、边界与特殊浮点 | `verify --out /results/verify` |
| 运行全部 19 矩阵四变体（`o3`/`pgo`/`old`/`tail`）固定对照实验 | `fixed --out /results/fixed` |

完整 BOLT 命令行开关、从 LLVM 源码应用补丁构建步骤与文件说明请参见 [复现说明.md](复现说明.md)。如需复现历史基础版本 `v1.0.0`，请访问仓库 Releases 中的 `v1.0.0` 页面。
