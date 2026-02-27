# Claude Code Manager

Web 端调度和管理多个 Claude Code 实例并行工作。灵感来自胡渊鸣的文章「我给 10 个 Claude Code 打工」。

## 功能

- **任务队列** — 创建任务，按优先级自动调度（数字越小优先级越高）
- **多实例并行** — 同时运行多个 Claude Code 实例，各自处理不同任务
- **Ralph Loop** — 自动取活循环：完成一个任务后自动取下一个
- **Git Worktree** — 每个实例在独立的 worktree 中工作，互不干扰
- **多轮对话** — 任务完成后可通过 Chat 界面继续追问，自动 `--resume` 同一 session
- **实时日志** — WebSocket 推送，实时查看每个实例的执行过程
- **Plan Mode** — 敏感任务先生成计划，人工审批后再执行
- **语音输入** — 通过 OpenAI Whisper API 语音转文字创建任务
- **PWA** — 手机浏览器 Add to Home Screen，原生 App 体验
- **Token 认证** — Bearer Token 保护所有 API，安全远程访问
- **远程访问** — 通过 ngrok 隧道暴露到公网，手机随时管理

## 技术栈

| 层 | 技术 |
|---|------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), SQLite |
| Frontend | React, Vite, Tailwind CSS v4, TypeScript |
| 实时通信 | WebSocket |
| 语音 | OpenAI Whisper API |
| 远程 | ngrok |

## 项目结构

```
claude-manager/
├── backend/
│   ├── api/            # REST + WebSocket 路由
│   ├── middleware/      # Token 认证中间件
│   ├── models/          # SQLAlchemy ORM (task, instance, log_entry, worktree)
│   ├── schemas/         # Pydantic 请求/响应模型
│   ├── services/        # 核心业务逻辑
│   │   ├── instance_manager.py   # Claude Code 子进程管理
│   │   ├── ralph_loop.py         # 自动取活循环
│   │   ├── stream_parser.py      # NDJSON stream-json 解析
│   │   ├── task_queue.py         # 优先级任务队列
│   │   ├── worktree_manager.py   # Git worktree 管理
│   │   ├── ws_broadcaster.py     # WebSocket 广播
│   │   └── whisper_client.py     # 语音转文字
│   └── main.py          # FastAPI 入口
├── frontend/
│   ├── public/          # PWA manifest, service worker, icons
│   └── src/
│       ├── api/         # HTTP + WebSocket 客户端
│       ├── components/  # Chat, Instances, Tasks, PlanReview, Voice
│       ├── hooks/       # useWebSocket
│       └── pages/       # Dashboard, TasksPage, LoginPage
├── scripts/
│   ├── dev.sh           # 一键启动开发环境
│   └── tunnel.sh        # ngrok 隧道
├── pyproject.toml
└── .env
```

## 快速开始

### 前置条件

- macOS（Claude Code 部署在本机）
- Python 3.11+
- Node.js 18+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) 已安装

### 安装

```bash
git clone <repo-url> && cd claude-manager

# 后端依赖
pip install -e .

# 前端依赖
cd frontend && npm install && cd ..

# 配置
cp .env.example .env
# 编辑 .env，设置：
#   AUTH_TOKEN=你的访问密码
#   OPENAI_API_KEY=sk-...（语音功能需要）
```

### 启动

```bash
# 一键启动
./scripts/dev.sh

# 或分别启动
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
cd frontend && npx vite --host &
```

访问 http://localhost:5173，输入 `AUTH_TOKEN` 登录。

### 远程访问（ngrok）

```bash
# 安装 ngrok
brew install ngrok
ngrok config add-authtoken YOUR_NGROK_TOKEN

# 生产模式：构建前端静态文件，由后端统一服务
cd frontend && npm run build && cd ..
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# 启动隧道
ngrok http 8000
```

用 ngrok 给出的 https URL 从手机访问。

## 使用流程

### 基本流程

1. **Dashboard** — 创建 Instance（如 `worker-1`），点击 ⚡ Start Loop 开启 Ralph Loop
2. **Tasks** — 创建任务，填写标题、Prompt、目标仓库路径、优先级
3. Ralph Loop 自动取最高优先级任务 → 创建 worktree → 执行 Claude Code → 完成后取下一个
4. 点击任务的 **Chat** 按钮，可以对已完成的任务继续追问

### Plan Mode

创建任务时选择 Mode = `plan`：
1. Claude Code 先以只读模式分析代码，生成执行计划
2. 任务进入 `plan_review` 状态，在 Tasks 页面显示计划内容
3. 点击 Approve 批准后，任务重新入队执行

### 语音输入

任务创建表单的标题和描述字段旁有 🎙 按钮，点击后录音，松开自动转文字填入。

## API

| 模块 | 端点 | 说明 |
|------|------|------|
| Tasks | `GET/POST /api/tasks` | 任务列表/创建 |
| | `GET/PUT/DELETE /api/tasks/{id}` | 任务详情/更新/删除 |
| | `POST /api/tasks/{id}/cancel` | 取消任务 |
| | `POST /api/tasks/{id}/retry` | 重试任务 |
| | `POST /api/tasks/{id}/plan/approve` | 批准计划 |
| | `POST /api/tasks/{id}/chat` | 发送追问消息 |
| | `GET /api/tasks/{id}/chat/history` | 获取对话历史 |
| Instances | `GET/POST /api/instances` | 实例列表/创建 |
| | `DELETE /api/instances/{id}` | 删除实例 |
| | `POST /api/instances/{id}/stop` | 停止实例 |
| | `POST /api/instances/{id}/run` | 手动执行 |
| | `GET /api/instances/{id}/logs` | 获取日志 |
| | `POST /api/instances/{id}/ralph/start` | 启动 Ralph Loop |
| | `POST /api/instances/{id}/ralph/stop` | 停止 Ralph Loop |
| Voice | `POST /api/voice/transcribe` | 语音转文字 |
| WebSocket | `ws://host/ws` | 实时推送（subscribe channel） |
| Auth | `POST /api/auth/login` | Token 登录 |
| System | `GET /api/system/health` | 健康检查 |
| | `GET /api/system/stats` | 统计信息 |

所有 API（除 health 和 login）需要 `Authorization: Bearer <token>` 头。

## 架构要点

- **Claude Code 集成**：通过 `claude -p [prompt] --dangerously-skip-permissions --output-format stream-json --verbose` 非交互模式调用，逐行解析 NDJSON 输出
- **多轮对话**：session_id 绑定在 Task 上，follow-up 时使用 `--resume <session_id>` 续接会话，cwd 保持一致
- **进程管理**：`asyncio.create_subprocess_exec` 启动，必须 unset `CLAUDECODE` 环境变量避免嵌套检测
- **停止机制**：SIGTERM → 等待 10s → SIGKILL
