---
name: "trae-conventions"
description: "TRAE environment output protocol: environment self-awareness + computer:// file link convention. Always active in TRAE sessions. Invoke at session start to establish TRAE context memory and enforce computer:// link format for all file references."
---

# TRAE Conventions — TRAE 环境输出协议规范

> **TRAE 专用 Skill**：本 Skill 仅适用于 TRAE 环境。非 TRAE 环境下 `computer://` 协议不可用。

---

## 1. 环境自感知

### 判断规则

在每次会话开始时，AI 应通过以下信号判断自己是否运行在 TRAE 环境中：

| 信号 | 判断方式 | 确认度 |
| --- | --- | --- |
| 工作目录路径包含 `.trae-cn` | 检查 cwd 或临时目录路径 | ✅ 确认 TRAE |
| 系统提示中包含 TRAE 相关指令 | 检查 system prompt 中是否有 TRAE 工具说明 | ✅ 确认 TRAE |
| 可用工具中包含 TRAE 专有工具 | 检查是否有 Skill、PureShowWidget、OpenPreview 等工具 | ✅ 确认 TRAE |
| 以上信号均无法确认 | — | **默认按 TRAE 处理** |

> **默认规则**：本项目（宁海教师人才智查助手）所有 AI 会话均在 TRAE 中运行。如果无法判断环境，默认按 TRAE 处理。

### 长记忆形成

确认 TRAE 环境后，在整个会话期间保持以下上下文记忆：

- **我是 TRAE AI** — 运行在 TRAE 环境中
- **文件引用用 `computer://`** — 所有本地文件引用使用 `computer://` 绝对路径
- **文件路径用绝对路径** — 所有文件操作使用绝对路径
- **利用 TRAE 工具** — 优先使用 Read、Write、SearchReplace、Grep、Glob 等 TRAE 文件操作工具

---

## 2. 链接协议 — computer:// 格式

### 核心规则

在对话回复中引用任何本地文件时，**必须**使用 `computer://` 协议格式：

```markdown
[显示名称](computer://绝对路径)
```

### 正确示例

#### 单文件引用

```markdown
详见 [封板计划](computer://c:\work\teachSeek\v8.0.4\docs\newStruct\24-v8.0.4封板计划.md)
```

#### 多文件引用

```markdown
这是 [Q2 营收图表](computer://c:\work\teachSeek\chart.png) 和完整的 [竞争分析](computer://c:\work\teachSeek\report.html)
```

#### workspace 内文件

```markdown
配置模板见 [sample.env](computer://c:\work\teachSeek\deploy\sample.env)
```

#### 临时工作目录文件

```markdown
处理脚本在 [convert.py](computer://c:\Users\nshop\.trae-cn\work\6a4f327aa6c190840e4cb4c5\convert.py)
```

### 错误示例（禁止）

| 错误类型 | 示例 | 问题 |
| --- | --- | --- |
| 相对路径 | `[文档](v8.0.4/docs/xxx.md)` | Web 端/手机端无法解析 |
| 纯路径文本 | `` `v8.0.4/docs/xxx.md` `` | 不可点击 |
| file:// 协议 | `[文档](file:///c:/work/...)` | Web 端不支持 |
| 无协议路径 | `[文档](/c:/work/...)` | 非标准格式 |

---

## 3. 特殊场景

### 目录引用

引用目录时，路径末尾加 `\`：

```markdown
部署文档在 [deploy 目录](computer://c:\work\teachSeek\deploy\)
```

### 同一文件多次引用

第一次用完整链接，后续可用简称：

```markdown
详见 [封板计划](computer://c:\work\teachSeek\v8.0.4\docs\newStruct\24-v8.0.4封板计划.md)。

根据封板计划中的时间线...
```

### GitHub 文件

GitHub 上的文件使用普通 Markdown 链接（不是 `computer://`）：

```markdown
Skill 源码在 [true-monad-skills 仓库](https://github.com/China1223/true-monad-skills)
```

### 文件不存在的情况

如果要引用的文件尚未创建，先创建文件，再用 `computer://` 引用。不要引用不存在的文件路径。

---

## 4. 检查清单

发送回复前，自检以下项目：

- [ ] 所有本地文件引用都使用了 `computer://` 协议
- [ ] 路径都是绝对路径（以盘符开头，如 `c:\`）
- [ ] 没有使用相对路径（如 `v8.0.4/docs/...`）
- [ ] 没有使用纯路径文本（如 `` `v8.0.4/docs/xxx.md` ``）
- [ ] 没有使用 `file://` 协议
- [ ] GitHub/外部 URL 使用普通 Markdown 链接
