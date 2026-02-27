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

## 人机协作测试

> **流程：人在浏览器操作 UI → 告诉 Claude Code 做了什么 → Claude Code 查库/查日志/查 git 验证结果。**
>
> 人负责操作和观察 UI，Claude Code 负责查数据确认后端状态是否正确。两者配合完成验证。

### 测试 1：启动与调度器

| 步骤 | 谁 | 做什么 |
|------|-----|--------|
| 1 | 人 | 启动后端 `uvicorn backend.main:app --reload` |
| 2 | AI | 查 DB 确认 worker instances 已自动创建：`SELECT * FROM instances` |
| 3 | 人 | 打开 Dashboard，观察 instances 列表是否显示 worker |
| 4 | 人 | 点击「Stop Dispatcher」按钮 |
| 5 | AI | 调用 `GET /api/dispatcher/status` 确认 `running: false` |
| 6 | 人 | 点击「Start Dispatcher」按钮 |
| 7 | AI | 再次确认 `running: true` |

### 测试 2：项目管理

| 步骤 | 谁 | 做什么 |
|------|-----|--------|
| 1 | 人 | 在 UI 创建 Project，填入一个有效的 git URL |
| 2 | AI | 查 DB `SELECT * FROM projects` 确认记录创建，status 从 `pending` → `cloning` → `ready` |
| 3 | AI | 确认 `WORKSPACE_DIR/{name}` 目录存在且是 git repo |
| 4 | 人 | 再创建一个 Project，填入无效 URL（如 `https://invalid/repo.git`） |
| 5 | AI | 查 DB 确认 status = `error`，error_message 有内容 |
| 6 | 人 | 创建一个同名 Project |
| 7 | 人 | 确认 UI 提示错误（400） |

### 测试 3：任务创建与执行

| 步骤 | 谁 | 做什么 |
|------|-----|--------|
| 1 | 人 | 在 TaskForm 下拉选择一个 ready 的 Project，填写标题和 Prompt，创建任务 |
| 2 | AI | 查 DB 确认 task 的 project_id 正确，target_repo 为空（等 dispatcher 填充） |
| 3 | 人 | 观察 TaskList，确认任务状态从 pending → executing（蓝色闪烁） |
| 4 | AI | 查 DB 确认 task.status = `executing`，instance_id 已分配，target_repo 已填充为项目路径 |
| 5 | 人 | 等任务执行完，观察状态变为 merging（青色）→ completed（绿色） |
| 6 | AI | 查 DB 确认 task.status = `completed`，merge_status = `merged` |

### 测试 4：优先级调度

| 步骤 | 谁 | 做什么 |
|------|-----|--------|
| 1 | 人 | 先停 Dispatcher |
| 2 | 人 | 创建 3 个任务：P5、P0、P3 |
| 3 | 人 | 启动 Dispatcher |
| 4 | AI | 查 DB 确认第一个变为 in_progress 的是 P0 的任务 |
| 5 | 人 | 在 TaskList 上确认 P0 最先显示执行状态 |

### 测试 5：Git 工作流验证

| 步骤 | 谁 | 做什么 |
|------|-----|--------|
| 1 | 人 | 创建一个简单任务（如 "在 README 末尾加一行注释"） |
| 2 | 人 | 等待任务完成 |
| 3 | AI | 在项目 repo 中执行 `git log --oneline -5` 确认有新 commit 并已 push 到 main |
| 4 | AI | 执行 `git worktree list` 确认 worktree 已被清理 |
| 5 | AI | 执行 `git branch` 确认 task 分支已被删除 |

### 测试 6：冲突处理

| 步骤 | 谁 | 做什么 |
|------|-----|--------|
| 1 | 人 | 同时创建 2 个修改同一文件的任务 |
| 2 | 人 | 等待两个任务都执行完 |
| 3 | 人 | 观察是否有任务变为橙色 `conflict` 状态 |
| 4 | AI | 查 DB 确认 conflict 任务的 merge_status = `conflict` |
| 5 | 人 | 点击 conflict 任务的「Retry」按钮 |
| 6 | AI | 查 DB 确认任务 status 回到 `pending`，retry_count +1 |

### 测试 7：并发控制

| 步骤 | 谁 | 做什么 |
|------|-----|--------|
| 1 | 人 | 一次性创建 10 个任务 |
| 2 | 人 | 观察同时 executing 的任务数量 |
| 3 | AI | 查 DB `SELECT COUNT(*) FROM instances WHERE status='running'`，确认不超过 MAX_CONCURRENT_INSTANCES |

### 测试 8：前端 UI 状态

| 步骤 | 谁 | 做什么 |
|------|-----|--------|
| 1 | 人 | 打开 Dashboard，截图统计栏 |
| 2 | AI | 查 `GET /api/system/stats` 对比统计数字是否一致 |
| 3 | 人 | 在 TaskForm 选择项目 → 确认手动路径输入框变灰 |
| 4 | 人 | 清空项目选择，手动输入路径 → 确认下拉框恢复 |
| 5 | 人 | 观察 TaskList 各状态颜色：pending 黄、executing 蓝闪、merging 青闪、completed 绿、conflict 橙、failed 红 |

### 测试 9：兼容性

| 步骤 | 谁 | 做什么 |
|------|-----|--------|
| 1 | 人 | 创建一个 Plan Mode 任务 → 确认进入 plan_review（紫色） |
| 2 | 人 | 点击 Approve → 确认任务重新入队执行 |
| 3 | 人 | 任务完成后点 Chat 按钮 → 发送追问消息 |
| 4 | AI | 查 DB 确认 task.session_id 存在，`--resume` 会被使用 |
| 5 | 人 | 测试语音按钮 → 确认录音转文字填入输入框 |

### AI 验证命令速查

测试时 Claude Code 常用的验证命令：

```bash
# 查任务状态
sqlite3 claude_manager.db "SELECT id, title, status, priority, project_id, instance_id, merge_status FROM tasks ORDER BY id"

# 查实例状态
sqlite3 claude_manager.db "SELECT id, name, status, current_task_id, pid FROM instances"

# 查项目状态
sqlite3 claude_manager.db "SELECT id, name, status, local_path FROM projects"

# 查调度器
curl -s -H "Authorization: Bearer $AUTH_TOKEN" http://localhost:8000/api/dispatcher/status | python -m json.tool

# 查 git 状态（在项目目录下）
git log --oneline -5
git worktree list
git branch

# 查后端日志（看 dispatcher 行为）
# 启动时加 --log-level debug 或查看终端输出
```

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
