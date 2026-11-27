# 仓库与完整附件内容对照

| 内容类别 | 精简 GitHub 仓库 | Release 完整 ZIP（`v1.1.0`） |
| :--- | :---: | :---: |
| 设计文档、变更说明、完整 patch 与复现脚本 | 包含 | 包含 |
| BOLT 优化源码（`frozen/GroupedFmaLoop.h`、`BinaryPassManager.cpp`）、测试内核与训练工具 | 包含 | 包含 |
| 安全性测试 C 源码（`tests/fp/fp_guard.c`、`tests/guard/guard.c`） | 包含 | 包含 |
| `v1.1.0` 两机与容器实验 JSON、`tail.asm` 及 `v1.0.0-reference` 全部历史实验记录 | 包含 | 包含 |
| 19 个 CSR 测试矩阵、预构建 Docker 镜像归档、冻结 `llvm-bolt` 及测试 ELF 可执行文件 | 不放入 Git 历史 | 全部包含 |
| 二进制输出向量（`*.y`）、Python 缓存与本地研发目录 | 不包含 | 仅原清单内交付项 |

## 校验说明

- 精简仓库根目录的 `REPOSITORY-SHA256SUMS.txt` 校验本仓库内全部文本、源码与实验记录文件（清单不校验自身）。
- `manifests/DELIVERY-SHA256SUMS.txt` 与 `manifests/delivery-content-manifest.json` 是完整交付包校验清单的归档副本；校验下载并解压后的完整交付目录时，请在解压目录 `v1.1.0-rc1/` 内运行 `sha256sum -c SHA256SUMS.txt`。
- `evidence/` 中保留了部分历史实验脚本用于完整溯源；正式便携复现请使用完整交付包中的 `scripts/run.py` 及预构建 Docker 镜像。

- `manifests/RELEASE-WRAPPER-SHA256SUMS.txt` 是完整 ZIP 根目录发布说明的校验清单副本。运行包内部清单保持原样。
