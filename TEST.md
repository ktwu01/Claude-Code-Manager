# 测试指南

> **重要：Claude Code 必须自主维护本文件。** 新增功能时同步更新测试，修改代码前先跑测试，修改后再跑一遍确认无回归。

## 快速命令

```bash
# 运行全部后端测试
python -m pytest backend/tests/ -v

# 运行单个测试文件
python -m pytest backend/tests/test_task_queue.py -v

# 运行匹配名称的测试
python -m pytest backend/tests/ -k "dequeue" -v

# 前端类型检查
cd frontend && npx tsc --noEmit

# 安装测试依赖（首次）
pip install -e ".[dev]"
```

---

## 自动化测试

### 后端测试（pytest + pytest-asyncio）

测试使用内存 SQLite，不依赖真实数据库或外部服务。

#### `test_task_queue.py` — 任务队列核心逻辑

| 测试 | 验证内容 |
|------|---------|
| `test_create_task` | 创建任务，确认默认值正确（status=pending, priority=0） |
| `test_dequeue_priority_order` | **关键**：P0 先于 P1 先于 P10 出队（数字越小优先级越高） |
| `test_dequeue_fifo_within_same_priority` | 同优先级按创建时间 FIFO |
| `test_dequeue_returns_none_when_empty` | 队列空时返回 None |
| `test_mark_completed` | 标记完成，确认 status 和 completed_at |
| `test_mark_failed` | 标记失败，确认 error_message 存储 |
| `test_mark_status_generic` | 通用状态更新（如 executing、merging） |
| `test_retry_increments_count` | 重试时 retry_count+1，error_message 清空 |
| `test_cancel_task` | 取消 pending 任务 |
| `test_cancel_executing_task` | 取消 executing/merging 状态的任务 |
| `test_delete_conflict_task` | 允许删除 conflict 状态的任务 |
| `test_delete_running_task_rejected` | 禁止删除 in_progress 状态的任务 |
| `test_list_tasks_ordered` | 列表按优先级排序 |
| `test_list_tasks_filter_status` | 按状态筛选 |

#### `test_stream_parser.py` — NDJSON 解析

| 测试 | 验证内容 |
|------|---------|
| `test_empty_line` | 空行返回 None |
| `test_invalid_json` | 非 JSON 返回 parse_error 事件 |
| `test_system_init` | 解析 session_id |
| `test_assistant_message` | 提取助手消息内容 |
| `test_tool_use` | 解析工具调用名称和输入 |
| `test_tool_result` | 解析工具结果 |
| `test_tool_result_error` | 检测错误结果 |
| `test_result_with_cost` | 提取 session_id 和 cost_usd |
| `test_result_is_error` | 检测错误结果事件 |
| `test_content_extraction_*` | 各种 content 格式（string, list, nested） |

#### `test_models.py` — ORM 模型

| 测试 | 验证内容 |
|------|---------|
| `test_task_defaults` | Task 所有默认值正确 |
| `test_task_with_project_id` | project_id 外键可正常存储 |
| `test_instance_defaults` | Instance 所有默认值正确 |
| `test_project_defaults` | Project 所有默认值正确 |
| `test_project_unique_name` | 项目名唯一约束生效 |

#### `test_api_tasks.py` — Task API 端点

| 测试 | 验证内容 |
|------|---------|
| `test_create_task` | POST 创建任务，状态码 201 |
| `test_create_task_with_project_id` | 支持 project_id 创建 |
| `test_list_tasks` | GET 列出全部任务 |
| `test_get_task` | GET 获取单个任务 |
| `test_get_task_not_found` | 404 处理 |
| `test_delete_task` | DELETE 删除任务 |
| `test_cancel_task` | 取消任务 |
| `test_retry_task` | 重试任务 |
| `test_resolve_conflict_wrong_status` | 非 conflict 状态调用 resolve 返回 400 |

### 前端检查

| 检查 | 命令 | 说明 |
|------|------|------|
| TypeScript 类型检查 | `cd frontend && npx tsc --noEmit` | 确认无类型错误 |
| 构建检查 | `cd frontend && npm run build` | 确认生产构建成功 |

---

## 手动测试清单

以下场景需要人工验证（涉及真实子进程、git 操作、网络）。

### 启动与调度器

- [ ] 启动后端 → 确认 Dispatcher 自动创建 worker instances（查看 DB 或 API）
- [ ] `GET /api/dispatcher/status` → 返回 `{"running": true, ...}`
- [ ] `POST /api/dispatcher/stop` → 调度器停止，不再分配新任务
- [ ] `POST /api/dispatcher/start` → 调度器恢复

### 项目管理

- [ ] 创建 Project（填 git URL）→ 确认后台自动 clone 到 `WORKSPACE_DIR/{name}`
- [ ] 等待 clone 完成 → 项目 status 变为 `ready`
- [ ] clone 失败（错误 URL）→ 项目 status 变为 `error`，有 error_message
- [ ] 创建重名项目 → 返回 400 错误

### 任务创建与执行

- [ ] 用项目下拉框创建任务 → 确认 project_id 正确
- [ ] 用手动路径创建任务 → 确认 target_repo 正确
- [ ] 创建多个不同优先级任务 → 确认 P0 最先执行
- [ ] 任务执行中 → 前端状态显示蓝色 `executing`
- [ ] 任务合并中 → 前端状态显示青色 `merging`

### Git 工作流

- [ ] 任务开始前 → 确认 worktree 创建时执行了 `git fetch origin`
- [ ] 任务完成后 → 确认 rebase + merge --ff-only + push 成功
- [ ] 确认 worktree 和分支在任务完成后被清理
- [ ] 模拟 push 冲突（两个任务同时完成）→ 确认重试机制工作
- [ ] push 持续失败（超过 max retries）→ 任务进入 conflict 状态

### 冲突处理

- [ ] 任务 conflict 后 → 前端显示橙色标识 + Retry 按钮
- [ ] 点击 Retry → 任务重新入队为 pending
- [ ] `POST /api/tasks/{id}/resolve-conflict` → 正确重新入队

### 并发控制

- [ ] 同时创建 10 个任务 → 确认并行不超过 `MAX_CONCURRENT_INSTANCES`
- [ ] 合并操作（merge lock）→ 确认同一时间只有一个任务执行 rebase+push

### 前端 UI

- [ ] Dashboard 统计栏 → 显示 executing、merging、conflict 等新状态的计数
- [ ] InstanceGrid → Dispatcher 开关按钮功能正常
- [ ] TaskForm → 项目下拉框正确加载项目列表
- [ ] TaskForm → 选择项目后手动路径输入框禁用
- [ ] TaskList → 各状态颜色正确显示

### 兼容性

- [ ] Plan Mode → 仍然正常工作（plan → review → approve → execute）
- [ ] Chat/Resume → 仍然正常工作
- [ ] 语音输入 → 仍然正常工作

---

## 开发规范

### Claude Code 开发时必须遵守：

1. **改代码前先跑测试**：`python -m pytest backend/tests/ -v`，确认基线全绿
2. **改代码后再跑测试**：确认无回归，新增功能需要对应新增测试
3. **前端改动后检查类型**：`cd frontend && npx tsc --noEmit`
4. **新增 service/model/API 时**：在对应 test 文件中添加测试用例
5. **修 bug 时**：先写一个复现 bug 的测试（红），修复后确认测试变绿
6. **更新本文件**：新增测试后同步更新 TEST.md 的测试表格

### 测试文件对应关系

| 源文件 | 测试文件 |
|--------|---------|
| `backend/services/task_queue.py` | `backend/tests/test_task_queue.py` |
| `backend/services/stream_parser.py` | `backend/tests/test_stream_parser.py` |
| `backend/models/*.py` | `backend/tests/test_models.py` |
| `backend/api/tasks.py` | `backend/tests/test_api_tasks.py` |
| `backend/services/dispatcher.py` | (待补充 — 需 mock 子进程) |
| `backend/services/worktree_manager.py` | (待补充 — 需 mock git) |
| `backend/api/projects.py` | (待补充 — 需 mock git clone) |
| `frontend/src/**` | TypeScript 类型检查 (`tsc --noEmit`) |
