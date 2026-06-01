# 个人站(知识文档 + 金价监控)

Vue3 + Element Plus + Flask + SQLite 一体化个人站,可一键部署到阿里云 Linux。

## 公网信息

- 服务器公网 IP: `123.57.110.129`
- 主服务端口: `8080`
- 金价监控健康检查: `9000`

## 功能

- **知识文档**:Markdown 编辑、图片上传、关键词搜索、分类、响应式列表
- **金价监控**:每 N 秒拉取京东金融 Au99.99 价格,ECharts 折线图展示历史走势,支持时间范围切换、间隔/启停热更新

## 文档目录

- [DEPLOY.md](docs/DEPLOY.md) — 阿里云分步部署教程(安全组 / firewalld / systemd / 开机自启)
- [API.md](docs/API.md) — 后端接口文档
- [USAGE.md](docs/USAGE.md) — 使用说明 / 京东金融 API 与 NapCat 对接说明

## 项目结构

```
personal-site/
├── backend/                # Flask 主服务 + 金价监控独立进程
│   ├── app.py              # 8080 主入口
│   ├── monitor.py          # 9000 金价监控
│   ├── config.py db.py auth.py init_db.py
│   ├── routes/             # auth/docs/gold/upload
│   ├── services/jd_gold.py # 京东金融 API 封装
│   ├── requirements.txt
│   └── .env.example
├── frontend/               # Vue3 + ElementPlus + md-editor-v3 + ECharts
│   ├── src/{api,router,store,views,styles}
│   ├── vite.config.js
│   └── package.json
├── deploy/                 # systemd / 一键安装 / Nginx 可选
└── docs/                   # 部署 / 接口 / 使用 文档
```

## 开发

```bash
# 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py             # 主服务 :8080
python monitor.py         # 金价监控 :9000(独立终端)

# 前端
cd ../frontend
npm install
npm run dev               # :5173,自动代理 /api 到 :8080
```

## 推送到 GitHub

代码生成在本地,需自行推送到你的 GitHub 仓库 `JiaoWoFeiFeiYa/<repo>`:

```bash
cd /Users/didi/personal-site
git init
git add .
git commit -m "feat: initial commit - personal site"
git branch -M main
git remote add origin git@github.com:JiaoWoFeiFeiYa/<your-repo>.git
git push -u origin main
```

> Claude 无法直接写入第三方 GitHub 仓库,上述命令请在本地终端执行。
