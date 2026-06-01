# 使用说明

## 登录

打开 `http://123.57.110.129:8080`,右上角点击「登录」。
默认账号写在服务器 `backend/.env` 的 `ADMIN_USERNAME` / `ADMIN_PASSWORD`,首次启动会用这两个值初始化数据库。

> 部署后请第一时间修改 `.env` 并参考 [DEPLOY.md](DEPLOY.md) 第三节同步修改数据库。

---

## 知识文档

- **列表页**:支持关键词搜索(标题/正文/分类)、分类下拉过滤、分页(每页 12)
- **新建/编辑**:仅登录后可见。Markdown 编辑器(md-editor-v3),左编辑右预览
- **图片上传**:在编辑器工具栏点 🖼️ 或直接拖拽/粘贴,会调用 `/api/upload` 上传到服务器 `backend/uploads/`,自动插入 `![](/uploads/xxx.png)`
- **删除**:列表卡片右下角图标,二次确认

数据存放:
- 文档正文:`backend/data.db` (SQLite)
- 图片文件:`backend/uploads/<uuid>.<ext>`

---

## 金价监控

打开「金价监控」菜单。

### 顶部展示
- 左卡片:最新价格(Au99.99 元/克) + 抓取时间
- 右卡片:折线图(可切 1 小时 / 24 小时 / 7 天 / 30 天 / 全部),支持鼠标拖动缩放

### 配置面板(需登录)
| 字段          | 说明                                                       |
|---------------|------------------------------------------------------------|
| 品类代码      | 京东金融 productSku,默认 `Au99.99`                        |
| 拉取间隔(秒) | 30 ~ 86400,改后 1 分钟内监控进程自动重新调度              |
| 启用          | 关闭后定时拉取暂停,手动触发仍可用                          |
| 立即拉取      | 同步触发一次,常用于排查或刚改完配置想立刻看到一条新数据    |

数据存放:`gold_price` 表;每条原始 JSON 也保留在 `raw_json` 字段,便于排查。

---

## 京东金融金价 API 说明

调用接口:
```
GET https://ms.jr.jd.com/gw/generic/hj/h5/m/latestPrice
```
- 无需 key、无需 cookie
- 返回所有品类一次性吐回,本项目仅取 `resultData.datas["Au99.99"].price`
- 项目用 `services/jd_gold.py` 封装,自带浏览器 UA + Referer

返回示例片段(节选):
```json
{
  "resultCode": 0,
  "resultData": {
    "datas": {
      "Au99.99": {
        "productSku": "Au99.99",
        "price": "612.55",
        "yesterdayPrice": "612.00",
        "demode": "0.55",
        "time": "2026-06-01 10:30:00"
      },
      "Au100g": { "...": "..." }
    }
  }
}
```

> 京东接口偶发 502/超时是正常现象,监控进程已在 `try/except` 中吞下异常并写日志,下一周期继续。

---

## NapCat / OneBot 对接说明

> 当前版本的金价监控**未启用**告警推送,仅做数据抓取与展示。
> 以下说明保留,方便后续启用。

### 流程
1. 服务器装 NapCat:[官方文档](https://napneko.github.io/) — 推荐 systemd 守护
2. NapCat 启用 HTTP 服务器,例:`http://127.0.0.1:3000`,设置 `access_token`
3. 调用示例:
```bash
curl -X POST http://127.0.0.1:3000/send_private_msg \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 12345678, "message": "金价提醒:612.55 元/克"}'
```

### 启用步骤(需要时)
1. 在 `gold_config` 表新增字段:`upper_threshold REAL, lower_threshold REAL, qq_targets TEXT, napcat_url TEXT, napcat_token TEXT`
2. 在 `services/` 下新增 `qq_bot.py` 封装 `send_private_msg`
3. 在 `monitor.py` 的 `_do_fetch` 内,拉取后比较 `last price` 与阈值,触发时调用 `qq_bot.send`
4. 写一个 `gold_alert_log` 表去重 + 留痕

需要时告诉我,我可以补这套代码,按"模块化 + 默认禁用"的方式加进去,不影响当前已部署服务。

---

## 浏览器兼容

- Chrome / Edge / Safari / Firefox 最近 2 版均可用
- 移动端断点 768px 自适应:导航栏隐藏用户名标签,卡片单列展示

---

## 常见问题

**Q1:访问 8080 没反应?**
- 阿里云安全组是否开放 8080?(控制台 → 安全组 → 入方向)
- 服务器 firewalld 是否开放?`firewall-cmd --list-ports`
- `systemctl status personal-site.service` 是否 active

**Q2:登录提示"用户名或密码错误"?**
- 默认账号在 `backend/.env`。改了 .env 后没改数据库:走 [DEPLOY.md](DEPLOY.md) 第三节

**Q3:金价图表为空?**
- 监控服务可能未启动:`systemctl status gold-monitor.service`
- 或还没到第一个采集周期:登录后点「立即拉取」

**Q4:Markdown 图片上传失败?**
- 未登录(/api/upload 需 token)
- 文件 > 5MB:在 `.env` 改 `MAX_UPLOAD_BYTES`
- `backend/uploads` 无写权限:`chown www:www /opt/personal-site/backend/uploads`
