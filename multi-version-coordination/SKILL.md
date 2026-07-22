---
name: "multi-version-coordination"
description: "多版本同步建议：Git 管理（提交+.gitignore 清理+版本号递增）、服务重启（健康检查+返回访问信息）、跨版本更新同步（CHANGELOG+详细文档）。触发词 'git' / '重启' / 'restart'。Invoke when user mentions git management, restart, or cross-version reference."
---

# 多版本同步建议

> **V3 双文件模式**：VERSION（Git 代码版本）和 RELEASE_VERSION（发行版本）分离，互不干扰。

## 触发规则

### 关键词

| 关键词 | 操作 |
| --- | --- |
| `git` | Git 管理（提交 + .gitignore 清理 + 版本号递增） |
| `重启` / `restart` | 服务重启 + 健康检查 + 返回访问信息 |

### 触发位置

| 位置 | 时机 | 说明 |
| --- | --- | --- |
| 第一行单独写 | **前置触发** | 先执行操作，再做正文任务 |
| 最后一行单独写 | **后置触发** | 先做正文任务，最后执行操作 |
| 行文中出现 | **行内触发** | 在当前位置触发一次 |

> 必须是完整词组单独成行才算前置/后置触发。

---

## Git 管理操作

对本版本目录执行：

### 1. 检查变更

```bash
cd {版本目录}  # 如 v8.0.3 或 v8.0.4
git status
```

### 2. 提交该提交的

代码变更、配置更新、文档更新等 → `git add` + `git commit`

```bash
git add {文件1} {文件2} ...
git commit -m "{简要描述}"
```

### 3. 排除不该提交的

检查 `.gitignore` 是否已覆盖以下类型，未覆盖的补充规则：

`__pycache__/` · `data/` · `dist/` · `build/` · `.env` · `*.log` · `logs/` · `*.tmp` · `.venv/` · `node_modules/` · `*.bak` · `*.db-shm` · `*.db-wal`

### 4. 同步远程最新（防止版本号冲突）

> **关键步骤**：多 AI 并行开发时，其他 AI 可能已 push 了更高的版本号。必须先同步远程，确保本地 `version_counter.txt` 是最新值。

```bash
git pull origin master
```

> **不用 `--rebase`**：正常情况下直接 `git pull` 即可，基本不会出现冲突。仅当出现冲突时才手动使用 `git rebase` 解决。

如果出现 VERSION 文件冲突：
1. 解决冲突，保留远程的更高版本号
2. `git add` 冲突文件
3. `git commit` 完成合并

### 5. 递增版本号（Git 管理）

Git 管理使用 `--git` 参数：**只写 VERSION 文件**（序号+1），不动 RELEASE_VERSION。

```bash
python deploy/maintenance/bump_version.py --git --base {大版本号}
# 示例：python deploy/maintenance/bump_version.py --git --base 8.0.4
# 结果：VERSION = v8.0.4-0722-0042
# RELEASE_VERSION 不变（保留旧值或不存在）
```

> **双文件规则（V3）**：
> - `--git` 只写 `VERSION` 文件，序号+1，无字母
> - `--release` 只写 `RELEASE_VERSION` 文件，追加 `-{Release日期}{字母}`
> - 两个文件互不干扰，不再共写同一个文件导致冲突
> - `/api/version` 优先返回 `RELEASE_VERSION`（若存在），否则返回 `VERSION`
>
> 详见 `deploy/maintenance/bump_version.py`。

### 6. 提交版本号并推送

```bash
git add VERSION {版本目录}/VERSION
git commit -m "v{版本号}: 描述"
git push origin master
```

### 7. 确认干净

```bash
git status  # 应显示 nothing to commit, working tree clean
```

> **流程要点**：先提交代码 → pull → bump 版本号 → 单独提交版本号 → push。版本号变更单独提交，避免与代码变更混在一个 commit 中，便于追溯。

---

## 重启操作

### 1. 识别目标

根据上下文确定要重启的服务（本地 uvicorn/npm、远程 Supervisor 进程等）。

### 2. 执行重启

```bash
# 本地
cd {版本目录} && .venv/bin/python run.py --host 0.0.0.0 --port {端口}

# 远程（需用户明确授权）
CTL="/www/server/panel/pyenv/bin/supervisorctl -c /etc/supervisor/supervisord.conf"
$CTL restart {进程名}
```

### 3. 健康检查

```bash
curl -s http://{IP}:{端口}/api/health
```

### 4. 返回信息（必须）

| 返回项 | 示例 |
| --- | --- |
| 访问地址 | `http://8.130.133.217:8003/` |
| 启动路径 | `/opt/teachseek_8003/` |
| 启动命令 | `/opt/teachseek_8003/teachseek --host 0.0.0.0 --port 8003` |
| 健康状态 | `200 OK` 或 `{"detail":"未登录或令牌无效"}` |

---

## 多版本同步目录

### 目录结构

```
v8.0.x/docs/multi-version-sync/
├── CHANGELOG.md     ← 更新日志（最新在最上方）
└── details/         ← 详细文档
    └── v{版本号}-{更新标题}.md
```

### CHANGELOG.md 格式

```markdown
# {版本号} 更新日志

| 版本号 | 更新标题 | 详细文档 | 日期 |
| --- | --- | --- | --- |
| v8.0.3-0716-0001 | 修复筛选组件日期选择 | [详情](details/v8.0.3-0716-0001-date-picker-fix.md) | 2026-07-16 |
```

### 详细文档格式

文件名：`v{版本号}-{kebab-case标题}.md`

```markdown
# {版本号} — {更新标题}

## 更新原因
（为什么更新，什么问题触发的）

## 解决的问题
（具体问题描述，含错误信息或复现步骤）

## 更新操作
1. 修改了 `xxx.py` 中的 `yyy` 函数
2. 新增了 `zzz.vue` 组件

## 解决方案
（技术方案说明，方便其他版本参考移植）
```

### 创建流程

1. 从 `VERSION` 文件读取版本号
2. 创建目录（如不存在）
3. 在 `CHANGELOG.md` 新增一行（最新在最上方）
4. 在 `details/` 创建详细文档
5. 确保链接正确

---

## 参考其他版本

### 触发条件

**仅在用户明确指令时触发**，例如"参考 v8.0.4 的最新更新"、"同步 v8.0.4 的 xxx 修改到 v8.0.3"。

### 操作步骤

1. 读取目标版本的 `docs/multi-version-sync/CHANGELOG.md`
2. 找到用户指定的更新
3. 如需详情，读取 `details/` 下对应文档
4. 将参考内容应用到当前版本
5. 在当前版本 CHANGELOG 中记录本次同步

### 不触发的情况

- 用户没说"参考其他版本"
- 用户只说"更新"或"修复"但没提到其他版本
- **默认不主动参考其他版本**

---

## 多版本同步建议开关

### 开关名称

`MULTI_VERSION_SYNC`

### 开关位置与判定（OR 关系）

| 位置 | 路径 | 作用范围 |
| --- | --- | --- |
| 全局开关 | 项目根目录 `AGENTS.md` | 打开后所有子版本全部生效 |
| 子版本开关 | 子版本目录 `AGENTS.md`（如 `v8.0.3/AGENTS.md`） | 仅本版本生效 |

> **OR 关系**：任一位置打开即生效。全局打开时，所有子版本无论自身开关状态都视为打开。

### 配置方式

在对应 `AGENTS.md` 中添加：

```markdown
## 多版本同步建议开关

- `MULTI_VERSION_SYNC=true`
```

### 开关操作

| 用户指令 | 操作 |
| --- | --- |
| "打开多版本同步建议开关" / "全局打开" | 根目录 `AGENTS.md` 设置 `MULTI_VERSION_SYNC=true` |
| "在 v8.0.3 打开开关" | `v8.0.3/AGENTS.md` 设置 `MULTI_VERSION_SYNC=true` |
| "关掉开关" / "关掉全局开关" | 对应位置设为 `false` 或删除 |

### 开关打开后

每次对该版本完成代码修改后自动：确认版本号 → 创建详细文档 → 更新 CHANGELOG → 随 Git 提交。

### 开关关闭时

不自动写入 CHANGELOG，仅当用户单次指令时才写入。

---

## 检查清单

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
- [ ] 链接指向正确的详细文档
- [ ] 文档已 Git 提交

### 参考其他版本

- [ ] 用户明确指定了参考目标
- [ ] 读取了目标版本 CHANGELOG
- [ ] 读取了详细文档（如需）
- [ ] 在当前版本记录了同步操作
