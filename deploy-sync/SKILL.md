---
name: "deploy-sync"
description: "部署后同步 deploy.html 和部署文档。每次服务器部署、更新、重启、端口变更后必须触发。Invoke when deploying, updating, restarting, or modifying any TeachSeek server instance."
---

# Deploy Sync — 部署同步

## 触发条件

执行以下任一操作后，**必须**触发本 Skill：

- PyInstaller Release 部署
- 源码部署更新或重启
- 端口变更（新增/删除/迁移实例）
- 数据库连接变更
- Supervisor 进程重启或配置变更
- 版本号更新

---

## 执行步骤

### 1. 更新 `website/deploy.html`

对每个受影响的实例卡片，更新版本号、数据库信息、标题和 meta 描述：

```html
<div class="instance-card" data-port="8003" data-host="8.130.133.217">
  <h3>v8.0.4 Release 版</h3>
  <p class="instance-meta">端口 8003 · PyInstaller 打包 · MySQL teach</p>
  <div class="instance-version">
    <span class="version-tag">版本</span>
    <span class="version-number">v8.0.4-0712-0003</span>
  </div>
  <div class="instance-db">
    <span class="db-tag">数据库</span>
    <span class="db-name">MySQL teach @ 8.138.245.105:3306</span>
  </div>
</div>
```

**版本号格式**：
- PyInstaller Release：`v{大版本}-{MMDD}-{序号}`
- 源码部署：`v{大版本}-{MMDD} 源码`

**数据库格式**：
- MySQL：`MySQL {库名} @ {IP}:{端口}`
- 达梦：`达梦 DM8 @ localhost:5236 (Docker)`

**新增/删除实例**：新增端口必须新增卡片，删除端口必须移除卡片。

### 2. 更新版本徽章

统一更新所有 HTML 页面的 `<span class="version-badge" data-version>` 文本：

- `website/index.html`
- `website/deploy.html`
- `website/features.html`
- `website/install.html`

### 3. 更新部署文档

- `deploy/RELEASE2_STATUS.md`：端口分配、部署概况、Supervisor 状态、.env 配置、部署历史
- `deploy/SERVER_INFRASTRUCTURE.md`：如有端口分配或服务器配置变更则更新
- `deploy/gen_status_json.sh`：如有端口变更则更新 `ALL_PORTS` 数组

### 4. 提交并推送

```bash
git add website/ deploy/RELEASE2_STATUS.md deploy/SERVER_INFRASTRUCTURE.md deploy/gen_status_json.sh
git commit -m "v{版本号}: deploy-sync 同步 deploy.html 和部署文档"
git push origin master
```

### 5. 服务器同步 website

对所有 Release 服务器执行 git pull，确保 website 文件同步：

```bash
# 每台服务器
ssh {user}@{IP} "cd /www/git_code/teachSeek && git stash && git pull origin master && git stash pop 2>/dev/null || true"
```

> `website/status.json` 已加入 `.gitignore`，由服务器 cron 生成，不会被覆盖。

### 6. 验证同步

```bash
ssh {user}@{IP} "grep 'version-badge' /www/git_code/teachSeek/website/deploy.html"
```

确认所有服务器的 deploy.html 版本号一致。

---

## 检查清单

- [ ] deploy.html 受影响卡片的版本号已更新
- [ ] deploy.html 受影响卡片的数据库信息已更新
- [ ] 新增端口有对应卡片 / 删除端口已移除卡片
- [ ] 所有 HTML 页面版本徽章已更新
- [ ] RELEASE2_STATUS.md 已更新
- [ ] SERVER_INFRASTRUCTURE.md 已更新（如需）
- [ ] gen_status_json.sh 已更新（如有端口变更）
- [ ] 已 git commit + push
- [ ] 所有 Release 服务器已 git pull
- [ ] 所有服务器 deploy.html 版本号已验证一致

---

## 注意事项

- 本 Skill 优先级高于任何之前的约定，每次部署都必须执行
- 不要跳过任何步骤，即使"只是重启"
- 部署多个实例时，所有受影响的卡片都要更新
- 所有 Release 服务器的 website 必须保持同步，新增服务器时也必须加入同步列表
