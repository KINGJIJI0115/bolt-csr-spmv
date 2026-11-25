# 第三方来源与署名

## LLVM / BOLT

本项目在 LLVM BOLT 提交 `37a8dd4eb2d22ffe4ed1f71b3f0b5aa6df7c7820` 上添加优化。LLVM 项目采用 Apache License 2.0 with LLVM Exceptions，原文见 [LICENSES/LLVM-LICENSE.txt](LICENSES/LLVM-LICENSE.txt)。该文件直接取自上述提交的 `llvm/LICENSE.TXT`。

上游源码：https://github.com/llvm/llvm-project 。本项目变更见 `grouped-fma-loop.patch`，未将上游代码表述为项目原创。

## 测试矩阵

| 矩阵 | 来源 |
|---|---|
| bcsstk14、15、16、17 | NIST Matrix Market / Harwell–Boeing bcsstruc2 |
| s1rmt3m1、s2rmt3m1、s3rmt3m1、s3rmt3m3 | NIST Matrix Market / Cylshell |
| s1rmq4m1、s2rmq4m1、s3rmq4m1 | NIST Matrix Market / Cylshell |
| msc00726 | SuiteSparse / UF，Boeing 集合 |
| rail2536、rail507、rail582 | OR-Library 铁路调度数据；下载来源见对应 metadata |

具体来源地址、原始或转换后校验值及处理记录保存在 `evidence/` 对应 metadata、classification 和 prepare 脚本中。矩阵按原数据转换为 CSR 用于课程复现，权益归原提供者；本项目没有给这些数据重新指定统一许可证。

Docker 中的 GCC、Python、系统库等第三方组件保留各自许可；镜像内的系统许可文件随镜像提供。本项目新增代码与文档版权归作者所有，供课程评测与学术交流使用。
