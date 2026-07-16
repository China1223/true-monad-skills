---
name: "multi-version-coordination"
description: "多版本同步建议：Git 管理（提交+.gitignore 清理）、重启（健康检查+返回访问信息）、跨版本更新同步（CHANGELOG+详细文档）。触发词 'git' / '重启' / 'restart'。Invoke when user mentions git management, restart, or cross-version reference."
---

# 多版本同步建议 — Multi-Version Coordination

## 1. 触发关键词与位置规则

### 关键词

| 关键词 | 含义 |
| --- | --- |
| `git`（全小写） | 执行 Git 管理（提交 + .gitignore 清理 + 版本号递增） |
| `重启`（中文）或 `restart`（英文） | 执行服务重启操作 |

### 触发位置

| 位置 | 触发时机 | 说明 |
| --- | --- | --- |
| **第一行**单独写关键词 | **前置触发** | 先执行操作，再做正文任务 |
| **最后一行**单独写关键词 | **后置触发** | 先做正文任务，最后执行操作 |
| 行文中间出现完整词组 | **行内触发** | 任务执行到该处时触发一次 |

> 注意：必须是完整词组单独成行才算前置/后置触发。行文中间出现关键词时，在当前位置触发一次 Git 管理或重启操作。

---

## 2. Git 管理操作

当 `git` 触发时，对本版本目录执行以下操作：

### 2.1 检查变更

```bash
cd {版本目录}  # 如 v8.0.3 或 v8.0.4
git status
```

### 2.2 提交该提交的

- 代码变更（`.py`、`.vue`、`.js`、`.css` 等）
- 配置更新（`.yaml`、`.json`、`.sql` DDL 文件等）
- 文档更新（`.md` 文件）
- 正常 `git add {文件}` + `git commit -m "v{版本号}: 描述"`

### 2.3 Ignore 不该提交的

以下文件必须排除，检查 `.gitignore` 是否已覆盖，未覆盖的补充规则：

| 类型 | 模式 | 说明 |
| --- | --- | --- |
| 运行时缓存 | `__pycache__/` | Python 缓存 |
| 运行时数据 | `data/` | 反馈数据、运行时文件 |
| 构建产物 | `dist/`、`build/` | PyInstaller / npm 构建产物 |
| 环境配置 | `.env` | 各环境独立配置 |
| 数据库快照 | `conf/*_*.sql` | 运行时导出的 DDL 快照 |
| 日志文件 | `*.log`、`logs/` | 运行时日志 |
| 临时文件 | `*.tmp`、`.tmp/` | 临时文件 |
| 虚拟环境 | `.venv/`、`node_modules/` | 依赖目录 |

### 2.4 版本号递增

提交前执行版本号递增：

```bash
python bump_version.py --base {大版本号}
# 如 python bump_version.py --base 8.0.3
# 或 python bump_version.py --base 8.0.4
```

### 2.5 提交流程

```bash
# 1. 递增版本号
python bump_version.py --base {版本号}

# 2. 检查 .gitignore 覆盖
git status  # 确认无不该提交的文件

# 3. 暂存该提交的文件
git add {文件1} {文件2} ...

# 4. 提交
git commit -m "v{版本号}: 描述"

# 5. 推送
git push origin master

# 6. 确认干净
git status  # 应显示 nothing to commit, working tree clean
```

### 2.6 保证代码干净

提交完成后再次 `git status` 确认无遗留未提交文件。如有遗留，判断是否应加入 `.gitignore`。

---

## 3. 重启操作

当 `重启` 或 `restart` 触发时：

### 3.1 识别目标

根据上下文确定要重启的服务：

| 场景 | 目标 |
| --- | --- |
| 本地开发 | uvicorn 后端 / npm run dev 前端 |
| 远程 Release1（8001） | SSH 执行 `supervisorctl restart teachseek_backend` |
| 远程 Release2 8002 | SSH 执行 `supervisorctl restart teachseek_v803` |
| 远程 Release2 8003 | SSH 执行 `supervisorctl restart teachseek_8003` |
| 反馈查看器 | SSH 执行 `supervisorctl restart feedback_viewer` |

### 3.2 执行重启

```bash
# 本地
# 后端
cd {版本目录} && .venv/bin/python run.py --host 0.0.0.0 --port {端口}
# 前端
cd {版本目录}/frontend && npm run dev

# 远程（需用户明确授权）
CTL="/www/server/panel/pyenv/bin/supervisorctl -c /etc/supervisor/supervisord.conf"
$CTL restart {进程名}
```

### 3.3 验证

等待服务启动（通常 3-5 秒），执行健康检查：

```bash
curl -s http://localhost:{端口}/api/health
# 或远程
curl -s http://{IP}:{端口}/api/health
```

### 3.4 返回信息（必须）

重启完成后，必须返回以下信息：

| 返回项 | 示例 |
| --- | --- |
| **访问地址** | `http://8.130.133.217:8003/` |
| **启动路径** | `/opt/teachseek_8003/` |
| **启动命令** | `/opt/teachseek_8003/teachseek --host 0.0.0.0 --port 8003` |
| **健康检查** | `200 OK` 或 `{"detail":"未登录或令牌无效"}`（服务正常运行） |

---

## 4. 多版本同步目录

### 4.1 目录结构

每个版本在自己的 `docs/` 下维护同步目录：

```
v8.0.3/docs/multi-version-sync/
├── CHANGELOG.md          ← 本版本更新日志
└── details/              ← 详细更新文档目录
    └── v8.0.3-0716-0001-xxx.md

v8.0.4/docs/multi-version-sync/
├── CHANGELOG.md
└── details/
    └── v8.0.4-0716-0001-xxx.md
```

### 4.2 CHANGELOG.md 格式

```markdown
# {版本号} 更新日志

| 版本号 | 更新标题 | 详细文档 | 日期 |
| --- | --- | --- | --- |
| v8.0.3-0716-0001 | 修复筛选组件日期选择 | [详情](details/v8.0.3-0716-0001-date-picker-fix.md) | 2026-07-16 |
| v8.0.3-0715-0003 | 新增语义搜索组件 | [详情](details/v8.0.3-0715-0003-semantic-search.md) | 2026-07-15 |
```

### 4.3 详细文档格式

文件名：`v{版本号}-{更新标题kebab-case}.md`，如 `v8.0.3-0716-0001-date-picker-fix.md`

```markdown
# {版本号} — {更新标题}

## 更新原因
（为什么更新，什么问题触发的）

## 解决的问题
（具体问题描述，包含错误信息或复现步骤）

## 更新操作
1. 修改了 `xxx.py` 中的 `yyy` 函数
2. 新增了 `zzz.vue` 组件
3. 更新了 `conf/filter_fields.yaml` 配置

## 解决方案
（技术方案说明，方便其他版本参考移植。包含关键代码片段或配置变更。）
```

### 4.4 创建流程

1. 确认版本号（从 `VERSION` 文件读取）
2. 如 `docs/multi-version-sync/` 目录不存在则创建
3. 在 `CHANGELOG.md` 中新增一行（最新在最上方）
4. 在 `details/` 下创建详细文档
5. 确保 CHANGELOG 中的链接指向正确的详细文档

---

## 5. 参考其他版本

### 5.1 触发条件

**仅在用户明确指令时触发**，例如：

- "参考 v8.0.4 的最新更新"
- "看一下 v8.0.3 的 xxx 更新"
- "参考其他版本的 xxx 功能实现"
- "同步 v8.0.4 的 xxx 修改到 v8.0.3"

### 5.2 操作步骤

1. 读取目标版本的 `docs/multi-version-sync/CHANGELOG.md`
2. 找到用户指定的更新（最新或特定标题）
3. 如需详情，读取 `details/` 下对应的详细文档
4. 将参考内容应用到当前版本
5. 应用完成后，在当前版本的 CHANGELOG 中记录本次同步

### 5.3 不触发的情况

- 用户没说"参考其他版本"
- 用户只说"更新"或"修复"但没有提到其他版本
- 任何没有明确指定参考其他版本的指令
- **默认不主动参考其他版本**

---

## 6. 多版本同步建议开关

### 6.1 开关名称

**多版本同步建议开关**（`MULTI_VERSION_SYNC`）

### 6.2 开关位置（两级，OR 关系）

开关可在两个位置配置，**只要其中任一位置打开，即视为打开**（OR 关系）：

| 位置 | 路径 | 作用范围 |
| --- | --- | --- |
| **全局开关** | 项目根目录 `AGENTS.md` | 打开后，**所有子版本**全部自动记录更新 |
| **子版本开关** | 子版本目录 `AGENTS.md`（如 `v8.0.3/AGENTS.md`） | 打开后，仅本版本自动记录更新 |

### 6.3 开关判定逻辑

```
if (全局开关 == true OR 子版本开关 == true):
    多版本同步建议 = 开启
else:
    多版本同步建议 = 关闭
```

> **全局优先**：全局开关打开后，所有子版本无论自身开关状态，都视为打开。

### 6.4 全局开关配置

在项目根目录 `AGENTS.md` 中：

```markdown
## 多版本同步建议开关

- `MULTI_VERSION_SYNC=true` ← 全局开关已打开，所有子版本自动记录更新
```

### 6.5 子版本开关配置

在子版本目录的 `AGENTS.md` 中（如 `v8.0.3/AGENTS.md`）：

```markdown
## 多版本同步建议开关

- `MULTI_VERSION_SYNC=true` ← 本版本开关已打开
```

### 6.6 开关操作

| 用户指令 | 操作 |
| --- | --- |
| "打开多版本同步建议开关" / "全局打开" | 在根目录 `AGENTS.md` 中设置 `MULTI_VERSION_SYNC=true` |
| "在 v8.0.3 打开开关" | 在 `v8.0.3/AGENTS.md` 中设置 `MULTI_VERSION_SYNC=true` |
| "关掉开关" | 修改对应位置的 `MULTI_VERSION_SYNC=false` 或删除该行 |
| "关掉全局开关" | 在根目录 `AGENTS.md` 中设置 `MULTI_VERSION_SYNC=false` 或删除 |

### 6.7 开关打开后的行为

当开关生效时（全局或子版本任一打开），每次对该版本完成代码修改后自动：

1. 确认版本号（从 `VERSION` 文件读取）
2. 创建 `docs/multi-version-sync/details/` 下的详细文档
3. 在 `CHANGELOG.md` 中新增记录
4. 在 Git 提交时一并提交这些文档

### 6.8 开关关闭时的行为

当开关未打开时（全局和子版本均为 false 或未配置），不自动写入 CHANGELOG。仅当用户单次指令时才写入。

### 6.9 触发条件汇总

| 触发方式 | 说明 | 持续性 |
| --- | --- | --- |
| **单次指令** | 用户明确说"写入多版本同步" / "记录到 CHANGELOG" | 仅本次 |
| **全局开关打开** | 根目录 `AGENTS.md` 中 `MULTI_VERSION_SYNC=true` | 所有子版本永久生效 |
| **子版本开关打开** | 子版本 `AGENTS.md` 中 `MULTI_VERSION_SYNC=true` | 仅本版本永久生效 |

---

## 7. 检查清单

每次触发本 Skill 时，根据触发的操作类型执行对应检查：

### Git 管理

- [ ] 版本号已递增
- [ ] `.gitignore` 覆盖所有不该提交的文件
- [ ] `git status` 确认无遗留
- [ ] 已 `git push`

### 重启

- [ ] 服务已重启
- [ ] 健康检查通过
- [ ] 返回了访问地址、启动路径、启动命令

### 多版本同步

- [ ] CHANGELOG.md 已新增记录
- [ ] 详细文档已创建
- [ ] CHANGELOG 链接指向正确的详细文档
- [ ] 文档已 Git 提交

### 参考其他版本

- [ ] 用户明确指定了参考目标
- [ ] 读取了目标版本的 CHANGELOG
- [ ] 读取了详细文档（如需）
- [ ] 在当前版本记录了同步操作
