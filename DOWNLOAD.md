# 下载与复现

## 1. 下载完整附件

打开仓库的 Releases，进入 `v1.0.0`，在 Assets 中下载：

- [完整交付 ZIP](https://github.com/KINGJIJI0115/bolt-csr-spmv/releases/download/v1.0.0/bolt-csr-spmv-v1.0.0-20261125.zip)
- [RELEASE-SHA256SUMS.txt](https://github.com/KINGJIJI0115/bolt-csr-spmv/releases/download/v1.0.0/RELEASE-SHA256SUMS.txt)

两份文件放在同一个目录。不要用自动生成的 Source code 压缩包替代完整附件。

## 2. 校验下载与解压

Linux / WSL：

```sh
sha256sum -c RELEASE-SHA256SUMS.txt
unzip bolt-csr-spmv-v1.0.0-20261125.zip
cd course-submission-readable-20261124
sha256sum -c SHA256SUMS.txt
```

Windows PowerShell 也可先运行以下命令，将结果与 `RELEASE-SHA256SUMS.txt` 中的值比较：

```powershell
Get-FileHash .\bolt-csr-spmv-v1.0.0-20261125.zip -Algorithm SHA256
Expand-Archive .\bolt-csr-spmv-v1.0.0-20261125.zip -DestinationPath .\unpacked
```

随后在 WSL 中进入解压目录运行后续命令。解压目录内的 `SHA256SUMS.txt` 校验 335 个原交付文件，Release 清单校验下载的 ZIP，仓库的 `REPOSITORY-SHA256SUMS.txt` 校验精简仓库，三者用途不同。

## 3. 默认验收

需要支持 FMA 的 x86-64 CPU 和 Linux Docker 环境。先进入上一步的 `course-submission-readable-20261124` 目录：

```sh
docker load -i course-auto-readable.docker.tar.gz
mkdir -p results
docker run --rm --user "$(id -u):$(id -g)" \
  --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --memory 4g --pids-limit 128 \
  -v "$PWD/results:/results" bolt-loop-course:20261125-course-readable-final \
  --out /results/acceptance
```

查看 `results/acceptance/report.md` 和 `acceptance.json`。每次运行使用新的输出目录。需要更换 CPU 时，在镜像名之前添加 `--cpuset-cpus` 参数并选择可用核心。

## 4. 独立审查入口

用下列参数替换默认命令最后一行：

| 目的 | 参数 |
|---|---|
| 仅重建与正确性核验 | `verify --out /results/verify` |
| 固定全量性能对照 | `fixed --out /results/fixed` |
| 快速流程检查 | `fixed --out /results/smoke --rounds 2 --seconds 0.02` |

特殊浮点测试见包内 `tests/floating-point/README.md`；源码构建和全部输出说明见包内 `README.md`。快速流程检查不用于形成性能结论。
