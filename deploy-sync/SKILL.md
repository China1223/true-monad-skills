---
name: "deploy-sync"
description: "部署后同步 deploy.html 和部署文档，管理 deploy/ 目录结构。每次服务器部署、更新、重启、端口变更后必须触发。Invoke when deploying, updating, restarting, or modifying any server instance."
---

# Deploy Sync — 部署同步与信息管理

## 触发条件

执行以下任一操作后，**必须**触发本 Skill：

- Release 包部署（PyInstaller / Docker / 源码）
- 源码部署更新或重启
- 端口变更（新增/删除/迁移实例）
- 数据库连接变更
- Supervisor / systemd 进程重启或配置变更
- 版本号更新

---

## 版本号管理

### Release 部署版本号递增

Release 部署使用 `--release` 参数：序号不变，追加/递增字母。

```bash
python deploy/maintenance/bump_version.py --release --base {大版本号}
# 示例：python deploy/maintenance/bump_version.py --release --base 8.0.4
# 首次部署：v8.0.4-0717-0007A
# 第二次部署：v8.0.4-0717-0007B
# 超过 26 次：v8.0.4-0717-0007AA
```

### 版本号规则

| 操作 | 参数 | 序号 | 字母 | 示例 |
| --- | --- | --- | --- | --- |
| Git 管理（multi-version-coordination） | `--git` | +1 | 清空 | `v8.0.4-0717-0008` |
| Release 部署（deploy-sync） | `--release` | 不变 | 追加/递增 | `v8.0.4-0717-0008A` |

> Git 管理后字母清空，下次 Release 从 A 开始。详见 `deploy/maintenance/bump_version.py`。

---

## deploy/ 目录结构地图

> 以下结构为通用规范，方括号 `{占位符}` 表示项目专属名称，需按实际项目替换。

```
deploy/
├── AGENTS.md                    ← 部署目录入口（AI 必读）
├── SKILLS_REPOSITORIES.md       ← Skills 仓库地址索引
├── sample.env                   ← 通用 .env 模板（占位符，不含真实密码）
│
├── .ssh/                        ← SSH 凭据（按服务器命名）
│   ├── {server-1}               ← 如 test1 / release1 / prod-1
│   ├── {server-2}               ← 如 test2 / release2 / prod-2
│   └── {server-3}               ← 命名规则：每个项目自定义，但需在此注释说明
│
├── maintenance/                 ← 版本号管理
│   ├── bump_version.py          ← 版本号生成脚本（全局递增序号，永不重置）
│   ├── version_counter.txt      ← 全局序号计数
│   └── README.md
│
├── env-templates/               ← 环境配置模板（按环境命名）
│   ├── {env-test}.env           ← 如 test.env
│   ├── {env-prod-1}.env         ← 如 deploy1.env / prod1.env
│   ├── {env-prod-2}.env         ← 如 deploy2.env / prod2.env
│   └── {env-prod-1}.env.example ← 占位符模板（不含真实密码）
│
├── pyinstaller/                 ← PyInstaller 打包配置
│   ├── entry_point.py           ← 入口脚本（通用，按项目修改 app 名）
│   └── {app-name}.spec          ← 打包配置（文件名按项目命名）
│
├── Server Info/                 ← 服务器状态管理
│   ├── SERVER_INFRASTRUCTURE.md ← 服务器总索引
│   ├── {server-2}-STATUS.md     ← 各服务器部署现状（按服务器命名）
│   ├── BAOTA_SUPERVISOR_GUIDE.md ← 宝塔 Supervisor 操作指南
│   └── DB_CONNECTION_GUIDE.md   ← 数据库连接指南
│
├── Release Server/              ← 发布部署记录
│   ├── DEPLOYMENT_GUIDE.md      ← 完整部署指南
│   ├── STANDARD_INSTALL.md       ← 标准一键安装指南
│   ├── RELEASE_GUIDE.md         ← Release 打包指南
│   ├── WEBSITE_UPDATE_GUIDE.md  ← Website 更新流程
│   ├── DEPLOY_RECORDS.md        ← 部署记录台账（端口/版本/状态）
│   └── release/
│       └── LATEST.md            ← 版本清单源文件
│
├── Skills/                      ← Skill 指导思想文档
│   ├── PROJECT_STRUCTURE.md     ← 项目结构约定
│   ├── deploy-sync.md           ← 本 Skill 指导思想
│   └── multi-version-coordination.md
│
├── docs/                        ← 历史/归档文档
│   └── (历史部署计划、构建报告等)
│
├── scripts/                     ← 部署脚本（按环境命名）
│   ├── install.sh               ← 通用安装脚本（可对外公开）
│   ├── install-{env-1}.sh       ← 环境专用脚本（如 install-prod1.sh）
│   ├── install-{env-2}.sh       ← 环境专用脚本（如 install-prod2.sh）
│   └── gen_status_json.sh       ← status.json 生成脚本（cron 运行）
│
├── event-templates/             ← 部署事件模板（发布通知、故障通报等）
│   └── (按需创建)
│
└── release/
    └── password.md              ← 密码汇总（不入 Git，仅本地保存）
```

> **通用性原则**：目录结构是通用的，文件名中的占位符 `{...}` 需按实际项目替换。`maintenance/`、`pyinstaller/`、`scripts/install.sh`、`gen_status_json.sh` 等是通用文件名，其他文件按项目实际情况命名。

---

## 信息查找规则

| 要找什么 | 去哪里找 |
| --- | --- |
| 服务器 IP/域名/SSH 密码 | `.ssh/{server-N}` |
| 各环境 .env 配置 | `env-templates/{env-*.env}` |
| 当前端口分配和版本 | `Server Info/{server-N}-STATUS.md` |
| 部署台账（历史记录） | `Release Server/DEPLOY_RECORDS.md` |
| 最新版本号 | 根目录 `VERSION` 文件 |
| 版本号递增 | `maintenance/bump_version.py --base {版本}` |
| 安装脚本 | `scripts/install.sh`（通用）/ `scripts/install-{env}.sh`（专用） |
| PyInstaller 打包 | `pyinstaller/{app-name}.spec` |
| 服务器总索引 | `Server Info/SERVER_INFRASTRUCTURE.md` |
| 部署后同步流程 | `Release Server/WEBSITE_UPDATE_GUIDE.md` |
| 部署事件模板 | `event-templates/` |

---

## deploy ↔ website 对应关系

> 以下为通用对应模式，实际文件名按项目调整。

| deploy/ 文件 | website/ 对应文件 | 关系 | 同步要求 |
| --- | --- | --- | --- |
| `Release Server/release/LATEST.md` | `website/release/LATEST.md` | 版本清单源 → Nginx 服务文件 | 每次发布后同步 |
| `Release Server/DEPLOY_RECORDS.md` | `website/deploy.html` | 部署台账 → 用户可见实例卡片 | 每次部署后同步 |
| `Server Info/{server}-STATUS.md` | `website/deploy.html` | 服务器状态 → 实例卡片信息 | 每次变更后同步 |
| `scripts/gen_status_json.sh` | `website/status.json` | 检测脚本 → 生成的状态数据 | ALL_PORTS 需与卡片一致 |
| `scripts/install.sh` | `website/install.sh` | 安装脚本源 → Nginx 对外提供 | 脚本更新时同步 |
| `scripts/install-{env}.sh` | `website/install-{env}.sh` | 环境专用脚本 → 对外提供 | 脚本更新时同步 |
| `env-templates/{env}.env` | `website/install.html` | 真实配置 → 对外说明（不含密码） | 配置变更时同步 |
| `Release Server/WEBSITE_UPDATE_GUIDE.md` | `website/README.md` | 同步流程 → 官网维护规范 | 流程更新时同步 |

### install.html（对外）vs deploy/（对内）

| 维度 | website/install.html | deploy/scripts/ + deploy/docs/ |
| --- | --- | --- |
| 受众 | 外部用户、运维人员 | 内部开发、AI |
| 内容 | 一键安装命令、参数说明、环境要求 | 详细部署步骤、脚本源码、错误排查 |
| 密码 | 不含 | 含真实凭据 |
| 访问方式 | Nginx 公开访问 | Git 仓库内部 |
| 联动 | install.html 的命令指向 scripts/install*.sh | scripts/install*.sh 是命令的源码 |

> **对齐规则**：install.html 中展示的安装命令和参数说明，必须与 `deploy/scripts/install*.sh` 的实际参数保持一致。脚本更新时，install.html 必须同步更新。

---

## Release 发布检查

每次 Release 前必须检查：

### 版本兼容性

| 检查项 | 检查方式 | 参考文件 |
| --- | --- | --- |
| 运行时版本（Python/Node 等） | 对比生产环境版本与代码要求 | `env-templates/{env-prod}.env` |
| 数据库类型和版本 | 确认数据库兼容性 | `Server Info/DB_CONNECTION_GUIDE.md` |
| 依赖库版本 | 检查 requirements 中的最低版本 | `{app-dir}/requirements.txt` |
| 前端构建要求 | Node.js / npm 版本 | `{app-dir}/frontend/package.json` |
| OS 兼容性（如 PyInstaller） | glibc 版本等 | `docs/BUILD_ENV_SUMMARY.md` |

### 配置一致性

| 检查项 | 参考文件 |
| --- | --- |
| .env 配置项完整 | `env-templates/{env-prod}.env` |
| CORS_ORIGINS 包含所有访问域名 | `env-templates/{env-prod}.env` |
| API Key 有效 | `env-templates/{env-prod}.env` |
| 数据库连接串正确 | `env-templates/{env-prod}.env` |
| JWT_SECRET 已设置 | `env-templates/{env-prod}.env` |

### 文档同步

| 检查项 | 目标文件 |
| --- | --- |
| DEPLOY_RECORDS.md 已更新 | `deploy/Release Server/DEPLOY_RECORDS.md` |
| {server}-STATUS.md 已更新 | `deploy/Server Info/` |
| deploy.html 卡片已更新 | `website/deploy.html` |
| 版本徽章已更新 | 所有 `website/*.html` |
| LATEST.md 已更新 | `deploy/Release Server/release/LATEST.md` + `website/release/LATEST.md` |
| gen_status_json.sh ALL_PORTS 已更新 | `deploy/scripts/gen_status_json.sh` |

---

## 部署后同步流程

### 1. 更新 `website/deploy.html`

对每个受影响的实例卡片，更新版本号、数据库信息、标题和 meta 描述。

**版本号格式**：
- 打包 Release：`v{大版本}-{MMDD}-{序号}`
- 源码部署：`v{大版本}-{MMDD} 源码`

**数据库格式**：`{数据库类型} {库名} @ {IP}:{端口}`

**新增/删除实例**：新增端口必须新增卡片，删除端口必须移除卡片。

### 2. 更新版本徽章

统一更新所有 HTML 页面的 `<span class="version-badge" data-version>` 文本。

### 3. 更新部署文档

- `deploy/Server Info/{server}-STATUS.md`：端口分配、部署概况、Supervisor 状态、.env 配置、部署历史
- `deploy/Server Info/SERVER_INFRASTRUCTURE.md`：如有端口分配或服务器配置变更则更新
- `deploy/Release Server/DEPLOY_RECORDS.md`：新增部署记录行
- `deploy/scripts/gen_status_json.sh`：如有端口变更则更新 ALL_PORTS 数组

### 4. 提交并推送

```bash
git add website/ deploy/
git commit -m "v{版本号}: deploy-sync 同步 deploy.html 和部署文档"
git push origin master
```

### 5. 服务器同步

对所有服务器执行 git pull，确保 website 文件同步：

```bash
ssh {user}@{IP} "cd {项目路径} && git stash && git pull origin master && git stash pop 2>/dev/null || true"
```

### 6. 验证同步

```bash
ssh {user}@{IP} "grep 'version-badge' {项目路径}/website/deploy.html"
```

确认所有服务器的 deploy.html 版本号一致。

---

## 检查清单

- [ ] deploy.html 受影响卡片的版本号已更新
- [ ] deploy.html 受影响卡片的数据库信息已更新
- [ ] 新增端口有对应卡片 / 删除端口已移除卡片
- [ ] 所有 HTML 页面版本徽章已更新
- [ ] {server}-STATUS.md 已更新
- [ ] SERVER_INFRASTRUCTURE.md 已更新（如需）
- [ ] DEPLOY_RECORDS.md 已新增记录
- [ ] gen_status_json.sh 已更新（如有端口变更）
- [ ] LATEST.md 已更新（deploy/ 和 website/）
- [ ] install.html 参数与 install*.sh 脚本一致（如脚本有变更）
- [ ] 已 git commit + push
- [ ] 所有服务器已 git pull
- [ ] 所有服务器 deploy.html 版本号已验证一致

---

## 注意事项

- 本 Skill 优先级高于任何之前的约定，每次部署都必须执行
- 不要跳过任何步骤，即使"只是重启"
- 部署多个实例时，所有受影响的卡片都要更新
- 所有服务器的 website 必须保持同步，新增服务器时也必须加入同步列表
- **通用性**：目录结构和流程是通用的，文件名中的占位符 `{...}` 需按实际项目替换
