# 阿里云部署教程

> 目标:把 `personal-site` 部署到阿里云 Linux 服务器(公网 IP `123.57.110.129`),
> 实现 8080 主站、9000 金价监控,systemd 守护、开机自启。

---

## 一、阿里云安全组(必须在控制台操作)

阿里云的"安全组"控制了公网能否访问对应端口,这是云防火墙,与服务器自身的 firewalld 是两层。

1. 控制台 → ECS → 实例 → 安全组 → 配置规则 → 入方向 → 手动添加
2. 添加规则:

| 方向 | 协议 | 端口范围 | 授权对象     | 说明                |
|------|------|----------|--------------|---------------------|
| 入   | TCP  | 8080/8080 | 0.0.0.0/0    | 网站主服务(必填)  |
| 入   | TCP  | 22/22     | 你的 IP/0.0.0.0/0 | SSH(默认应已开)   |
| 入   | TCP  | 80/80     | 0.0.0.0/0    | (可选,Nginx 反代)  |
| 入   | TCP  | 443/443   | 0.0.0.0/0    | (可选,HTTPS)        |

> 9000 端口仅本机使用,**不要**对外开放。

---

## 二、首次部署(SSH 到服务器)

```bash
ssh root@123.57.110.129
mkdir -p /opt && cd /opt
# 拉代码(把 <your-repo> 换成你的仓库)
git clone https://github.com/JiaoWoFeiFeiYa/<your-repo>.git personal-site
cd personal-site
# 一键安装
sudo bash deploy/install.sh
```

`install.sh` 会做这些事:

1. `dnf/yum` 安装 python3、nodejs 18、git、firewalld
2. 创建 `www` 系统用户与 `/var/log/personal-site` 目录
3. `backend/.venv` 安装 Python 依赖
4. `frontend/` `npm install && npm run build` 生成 `dist/`
5. 部署 `personal-site.service` 与 `gold-monitor.service` 到 `/etc/systemd/system/`,启用并 `start`
6. `firewall-cmd --permanent --add-port=8080/tcp` 放行端口

完成后访问:`http://123.57.110.129:8080`

---

## 三、修改环境变量(关键!)

```bash
sudo vi /opt/personal-site/backend/.env
```

至少修改:
- `ADMIN_PASSWORD`:管理员密码
- `JWT_SECRET`:用 `openssl rand -hex 32` 生成长字符串

修改后重启:

```bash
sudo systemctl restart personal-site.service gold-monitor.service
```

> 首次启动后改 `ADMIN_PASSWORD`/`ADMIN_USERNAME` 不会自动同步到数据库(数据库已写入老值)。
> 改密两种方式:
> 1. 删库重建:`rm /opt/personal-site/backend/data.db && systemctl restart personal-site.service`
> 2. 进入 sqlite3 手动 UPDATE:
> ```bash
> cd /opt/personal-site/backend
> source .venv/bin/activate
> python -c "from werkzeug.security import generate_password_hash as h; print(h('新密码'))"
> sqlite3 data.db "UPDATE admin SET password_hash='<上一步输出>';"
> ```

---

## 四、防火墙(系统层)

`install.sh` 已配 firewalld。手动检查:

```bash
sudo firewall-cmd --list-ports
# 应看到 8080/tcp
# 如缺少:
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

> 如服务器使用 `iptables` 而非 firewalld:
> ```bash
> iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
> service iptables save
> ```

---

## 五、进程守护与开机自启(systemd)

`install.sh` 已自动 `systemctl enable --now`。常用命令:

```bash
# 状态
systemctl status personal-site.service
systemctl status gold-monitor.service

# 重启
sudo systemctl restart personal-site.service
sudo systemctl restart gold-monitor.service

# 看日志
journalctl -u personal-site.service -n 200 -f
journalctl -u gold-monitor.service -n 200 -f
# 或
tail -f /var/log/personal-site/error.log
tail -f /var/log/personal-site/monitor.log

# 关闭/启用开机自启
sudo systemctl disable personal-site.service
sudo systemctl enable  personal-site.service
```

`Restart=always` 已写入 unit,任何崩溃 3-5 秒内拉起。

---

## 六、更新部署(后续迭代)

```bash
cd /opt/personal-site
git pull
# 后端依赖变更
sudo -u www ./backend/.venv/bin/pip install -r backend/requirements.txt
# 前端代码变更
cd frontend && sudo -u www npm install && sudo -u www npm run build && cd ..
# 重启
sudo systemctl restart personal-site.service gold-monitor.service
```

---

## 七、Nginx 反代(可选,推荐绑定域名后启用)

```bash
sudo dnf install -y nginx
sudo cp /opt/personal-site/deploy/nginx.conf.optional /etc/nginx/conf.d/personal-site.conf
sudo vi /etc/nginx/conf.d/personal-site.conf  # 修改 server_name
sudo systemctl enable --now nginx
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload
```

阿里云安全组同步放行 80。这样访问 `http://123.57.110.129/` 即可,不再需要 `:8080`。

HTTPS:推荐用 [acme.sh](https://github.com/acmesh-official/acme.sh) 申请免费证书,然后在 server 块里加 `listen 443 ssl;` 与证书路径。

---

## 八、回滚 / 卸载

```bash
sudo systemctl disable --now personal-site.service gold-monitor.service
sudo rm /etc/systemd/system/{personal-site,gold-monitor}.service
sudo systemctl daemon-reload
sudo rm -rf /opt/personal-site
sudo userdel www      # 谨慎
```
