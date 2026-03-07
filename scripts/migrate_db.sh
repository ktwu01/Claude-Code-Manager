#!/bin/bash
# 数据库迁移脚本
#
# 适用场景：生产环境旧库（无 Alembic 版本控制，且没有 loop task 相关字段）
# 执行后数据库将升级到最新 schema，原有数据不丢失。
#
# 如果旧库已经有 alembic_version 表，直接运行：
#   uv run alembic upgrade head

set -e

echo "检查数据库状态..."
CURRENT=$(uv run alembic current 2>/dev/null || echo "")

if echo "$CURRENT" | grep -q "head"; then
  echo "数据库已是最新版本，无需迁移。"
  exit 0
fi

if echo "$CURRENT" | grep -q "6b3f8a1c2d9e"; then
  echo "检测到初始 schema，应用 loop task 字段变更..."
  uv run alembic upgrade head
elif [ -z "$(echo "$CURRENT" | grep -v '^$' | grep -v 'INFO' | grep -v 'WARNING')" ]; then
  echo "未检测到 Alembic 版本记录，标记初始 schema 并应用 loop task 变更..."
  uv run alembic stamp 6b3f8a1c2d9e
  uv run alembic upgrade head
else
  echo "未知状态，直接尝试 upgrade..."
  uv run alembic upgrade head
fi

echo "迁移完成，当前版本："
uv run alembic current
