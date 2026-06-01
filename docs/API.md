# 接口文档

> Base URL: `http://123.57.110.129:8080`
> 所有接口统一返回 `{ "code": 0, "msg": "ok", "data": ... }`,`code != 0` 表示业务失败。
> 写操作需在 Header 加 `Authorization: Bearer <token>`。

---

## 鉴权

### POST /api/auth/login
登录获取 token。

请求:
```json
{ "username": "admin", "password": "xxx" }
```
响应:
```json
{ "code": 0, "msg": "ok", "data": { "token": "ey...", "username": "admin" } }
```

### GET /api/auth/me
**需登录**。校验 token 有效性。
```json
{ "code": 0, "msg": "ok", "data": { "username": "admin" } }
```

---

## 文档

### GET /api/docs
列表 + 搜索 + 分页(公开)。

Query:
| 参数      | 类型   | 默认 | 说明                       |
|-----------|--------|------|----------------------------|
| keyword   | string | -    | 模糊匹配 title/content/category |
| category  | string | -    | 精确匹配分类                |
| page      | int    | 1    | 页码                        |
| page_size | int    | 20   | 每页(最大 100)             |

响应:
```json
{
  "code": 0,
  "data": {
    "total": 12,
    "page": 1,
    "page_size": 20,
    "items": [
      { "id": 1, "title": "...", "category": "默认", "summary": "...", "created_at": "...", "updated_at": "..." }
    ]
  }
}
```

### GET /api/docs/categories
分类列表(公开)。
```json
{ "code": 0, "data": [ { "category": "默认", "n": 5 } ] }
```

### GET /api/docs/{id}
详情(公开)。返回完整 `content`。

### POST /api/docs
**需登录**。新建。
```json
{ "title": "标题", "category": "默认", "content": "# md..." }
```

### PUT /api/docs/{id}
**需登录**。全字段更新。

### DELETE /api/docs/{id}
**需登录**。删除。

---

## 上传

### POST /api/upload
**需登录**,`multipart/form-data`,字段名 `file`。

允许格式:`.png .jpg .jpeg .gif .webp .bmp`,默认上限 5 MB(`.env` `MAX_UPLOAD_BYTES` 可调)。

响应:
```json
{ "code": 0, "data": { "url": "/uploads/<hash>.png", "name": "<hash>.png", "size": 12345 } }
```

> 静态访问:`GET /uploads/<filename>` 由 Flask 直接吐文件。

---

## 金价

### GET /api/gold/latest
最新一条价格(公开)。
```json
{ "code": 0, "data": { "id": 12, "product_code": "Au99.99", "price": 612.55, "fetched_at": "..." } }
```

### GET /api/gold/history?range=24h
历史(公开)。`range ∈ {1h, 24h, 7d, 30d, all}`,默认 24h。
```json
{ "code": 0, "data": { "range": "24h", "items": [ { "id": 1, "price": 612.55, "fetched_at": "..." } ] } }
```

### GET /api/gold/config
当前监控配置(公开,只读)。
```json
{ "code": 0, "data": { "id": 1, "product_code": "Au99.99", "poll_interval_sec": 300, "enabled": 1, "updated_at": "..." } }
```

### PUT /api/gold/config
**需登录**。修改配置,监控进程在 60 秒内热更新。
```json
{ "product_code": "Au99.99", "poll_interval_sec": 300, "enabled": true }
```

### POST /api/gold/refresh
**需登录**。立刻同步触发一次拉取(适合调试)。
```json
{ "code": 0, "data": { "id": 13, "product_code": "Au99.99", "price": 612.78, "ts": "..." } }
```

---

## 健康检查

- `GET /api/health` 主服务健康
- `GET http://127.0.0.1:9000/health` 监控服务健康(仅本机访问)
