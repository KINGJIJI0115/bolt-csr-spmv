# 安全性与浮点等价性测试源码

本目录保留 `v1.1.0` 内置自动化验证所使用的两份 C 测试源码（对应的预编译与 BOLT 改写后可执行文件包含在 Release 完整交付包中，并由容器 `verify` 与默认 `calibrate` 入口自动运行）：

- **`fp/fp_guard.c`**：IEEE-754 特殊浮点语义测试，覆盖 **8 类浮点数据 × 4 种舍入模式（`FE_TONEAREST`、`FE_TOWARDZERO`、`FE_UPWARD`、`FE_DOWNWARD`），共 32 次组合测试**，逐比特核对计算输出并校验全部浮点异常标志位（`fetestexcept`）一致。
- **`guard/guard.c`**：边界访问与结构健壮性测试，覆盖 **4097 种行长边界**（含 0、1～16 短行、16/17 切换临界点、4× 分组余数 1～4 尾长等）、空矩阵、空指针空行及 8 类特殊浮点数输入。

完整运行记录保存在 `evidence/correctness.json` 与 `evidence/container-verification.json`。
