# 镜像构建记录

`Dockerfile.reference` 和 `dockerignore.reference` 为交付时使用文件的原样副本。Dockerfile 的 `COPY .` 以完整交付目录为上下文，不能用精简仓库替代。

它依赖本地基础镜像 `bolt-loop-course:20261124-group4-experiment`，不是独立的从零构建配方。课程复现使用 Release 已导出的完整镜像，通过 `docker load` 加载，不需要先构建基础镜像。自行编译 BOLT 可按根目录 `复现说明.md` 的固定提交与 patch 步骤操作。
