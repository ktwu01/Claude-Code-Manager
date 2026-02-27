# Claude Code Manager - 项目指南

> **重要：Claude 必须自主维护本文件。** 当项目架构、约定、关键路径发生变化时，只做必要的修改，保持简洁。不要大段重写，只更新变化的部分。

## 概述

Web 端调度管理多个 Claude Code 实例并行工作。Backend (FastAPI) + Frontend (React/Vite) + SQLite。

GitHub: https://github.com/zjw49246/Claude-Code-Manager.git

## 技术栈

- **后端**: Python 3.11+, FastAPI, SQLAlchemy async, SQLite (aiosqlite)
- **前端**: React 19, Vite, Tailwind CSS v4, TypeScript, Lucide icons
- **实时通信**: WebSocket (原生, channel-based pub/sub)
- **语音**: OpenAI Whisper API
- **隧道**: Cloudflare Tunnel / ngrok

## 项目结构

```
claude-manager/
├── backend/
│   ├── main.py                  # FastAPI 入口, 全局单例, 静态文件服务
│   ├── config.py                # Pydantic BaseSettings (.env)
│   ├── database.py              # SQLAlchemy async engine + session
│   ├── api/                     # 路由
│   │   ├── tasks.py             # 任务 CRUD + plan 审批 + conflict 解决
│   │   ├── chat.py              # 多轮对话 (基于 task, --resume)
│   │   ├── instances.py         # 实例 CRUD + Ralph Loop 控制 + Dispatcher 端点
│   │   ├── projects.py          # Project CRUD + git clone
│   │   ├── ws.py                # WebSocket 端点
│   │   ├── voice.py             # Whisper 语音转文字
│   │   ├── auth.py              # Token 登录
│   │   └── system.py            # 健康检查 + 统计
│   ├── middleware/auth.py       # Bearer token 认证中间件
│   ├── models/                  # SQLAlchemy ORM 模型
│   │   ├── task.py              # Task (含 session_id, last_cwd, project_id)
│   │   ├── instance.py          # Claude Code 实例
│   │   ├── project.py           # Project (name, git_url, local_path)
│   │   ├── log_entry.py         # 执行日志
│   │   └── worktree.py          # Git worktree 跟踪
│   ├── schemas/                 # Pydantic 请求/响应模型
│   └── services/                # 核心业务逻辑
│       ├── instance_manager.py  # 子进程生命周期 (launch/stop/consume output)
│       ├── dispatcher.py        # 全局调度器 (9 步任务生命周期)
│       ├── ralph_loop.py        # 自动取活循环 (legacy, 保留兼容)
│       ├── stream_parser.py     # NDJSON stream-json 解析器
│       ├── task_queue.py        # 优先级队列 (asc = 优先级越高)
│       ├── worktree_manager.py  # Git worktree 创建/合并/删除 + rebase+push
│       ├── ws_broadcaster.py    # WebSocket channel 广播
│       └── whisper_client.py    # OpenAI Whisper 客户端
├── frontend/
│   └── src/
│       ├── api/client.ts        # API 客户端 + 类型 (401 自动登出)
│       ├── api/ws.ts            # WebSocket 客户端 (指数退避重连)
│       ├── pages/               # Dashboard, TasksPage, LoginPage
│       ├── components/
│       │   ├── Chat/ChatView.tsx       # 多轮对话 UI (基于 task)
│       │   ├── Instances/              # InstanceGrid, InstanceLog
│       │   ├── Tasks/                  # TaskForm, TaskList
│       │   ├── PlanReview/PlanPanel.tsx # Plan 审批
│       │   └── Voice/VoiceButton.tsx   # MediaRecorder → Whisper
│       └── hooks/useWebSocket.ts
├── scripts/
│   ├── dev.sh                   # 一键启动开发环境
│   └── tunnel.sh                # ngrok 隧道
├── .env                         # AUTH_TOKEN, OPENAI_API_KEY, DATABASE_URL
└── pyproject.toml
```

## 关键约定

- **优先级**: 数字越小优先级越高 (P0 > P1 > P2)，排序用 `.asc()`
- **Session 绑定**: `session_id` 和 `last_cwd` 在 **Task** 上（不是 Instance），因为 instance 是轮换执行不同 task 的 worker
- **Claude Code 调用**: `claude -p [prompt] --dangerously-skip-permissions --output-format stream-json --verbose`
- **Resume**: `claude -p [follow-up] --resume [session_id]` — 必须使用和原始 session 相同的 cwd
- **环境变量清理**: 生成子进程前必须 unset `CLAUDECODE` / `CLAUDE_CODE`，避免嵌套检测
- **停止顺序**: SIGTERM → 等 10s → SIGKILL
- **WebSocket channels**: `instance:{id}`, `task:{id}`, `tasks`, `system`
- **认证**: 除 `/api/system/health` 和 `/api/auth/login` 外，所有 API 需要 `Authorization: Bearer <token>`
- **前端 type 导入**: 用 `import type { X }` 导入类型，`import { api }` 导入值（Vite 会去除 type-only exports）
- **Tailwind v4**: 用 `@import "tailwindcss"` + `@tailwindcss/vite` 插件，无 tailwind.config
- **调度器**: `GlobalDispatcher` 替代 per-instance `RalphLoop`，启动时自动创建 worker、自动调度
- **任务生命周期**: pending → in_progress → executing → merging → completed（失败回 pending 重试，冲突进 conflict）
- **Merge 流程**: worktree 中 fetch + merge origin/main → rebase origin/main + merge --ff-only + push（带重试）
- **项目**: `Project` 模型管理 git repo，创建时自动 clone 到 `workspace_dir/{name}`
- **Task.project_id**: 可选关联 Project，dispatcher 自动解析为 target_repo

## 任务生命周期（9 步）

```
1. 领取任务    → dequeue, status=in_progress
2. 创建工作区  → git fetch origin, git worktree add -b task/xxx origin/main
3. 实现功能    → Claude Code 在 worktree 中执行, status=executing
4. 提交代码    → Claude Code 自动 commit（已有）
5. 集成最新代码 → git fetch origin && git merge origin/main（在 worktree 中）
6. 合并到 main → git rebase origin/main, merge --ff-only, git push origin main（带重试）
7. 标记完成    → status=completed
8. 清理        → git worktree remove + 删除分支
9. 经验沉淀    → 记录到日志
```

**状态流转：**
```
pending → in_progress → executing → merging → completed
                           ↓           ↓
                        (fail)     (conflict)
                           ↓           ↓
                        pending     conflict
                       (retry)   (需人工/retry)
```

## 开发命令

```bash
# 一键启动 (后端 + 前端)
./scripts/dev.sh

# 仅后端
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 仅前端
cd frontend && npx vite --host

# 构建前端
cd frontend && npm run build

# 生产模式 (单端口，后端服务前端静态文件)
cd frontend && npm run build && cd ..
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 公网隧道
cloudflared tunnel --url http://localhost:8000
```

## 数据库

SQLite 位于 `./claude_manager.db`，首次启动时通过 `init_db()` 自动创建。

Schema 变更需删除 DB 文件重建（暂无迁移）：
```bash
rm claude_manager.db  # 下次启动自动重建
```

## 文件维护规则

- **CLAUDE.md**（本文件）：架构或约定变化时更新，只改变化的部分
- **README.md**：面向用户的文档，功能变化时同步更新

## 经验教训沉淀

每次遇到问题或完成重要改动后，要在 [PROGRESS.md](./PROGRESS.md) 中记录：
- 遇到了什么问题
- 如何解决的
- 以后如何避免
- **必须附上 git commit ID**

**同样的问题不要犯两次！**
