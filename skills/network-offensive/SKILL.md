---
name: network-offensive
description: 网络渗透与资产测绘工具箱。需要枚举子域、扫端口、探存活、找目录、破参数、扫漏洞模板、搭隧道、做内网穿透时使用。覆盖 subfinder/httpx/naabu/nuclei/ffuf/gobuster/feroxbuster/dnsx/tlsx/asnmap/alterx/shuffledns/puredns/cdncheck/cloudlist/uncover/gau/katana/dalfox/interactsh/afrog/afrog 等。
---

# 网络攻防工具箱（AArch64 外挂二进制）

本 skill 面向**已授权**的渗透测试与资产测绘任务。所有工具都是 aarch64 静态 ELF，直接通过 Bash 调用，无需安装。

---

## 授权与边界（必读）

| 项 | 要求 |
|---|---|
| **目标范围** | 只测任务创建时声明的域名 / IP / CIDR。越界即违反纪律 |
| **爆破强度** | 登录面 ≤5 组默认口令失败即停；目录爆破先小字典，命中再扩大 |
| **生产系统** | 禁止大字典爆破、禁止并发拉满 |
| **payload** | SQLi 探测只读（level 2 / risk 1）；上传只验证能力不落地后门 |
| **证据** | 每条结论留可复现命令 + 关键输出 |

---

## 工具清单（按攻击面分组）

### 资产测绘 / 子域枚举

| 工具 | 用途 | 典型命令 |
|---|---|---|
| `subfinder` | 被动子域枚举 | `subfinder -d example.com -all -silent` |
| `amass` | 主动+被动子域（较重） | `amass enum -d example.com -passive` |
| `shuffledns` | 子域爆破（需 massdns 字典） | `shuffledns -d example.com -w words.txt -r resolvers.txt` |
| `puredns` | 子域爆破+解析校验 | `puredns bruteforce words.txt example.com` |
| `alterx` | 子域变形（基于已知模式） | `alterx -l subs.txt -o out.txt` |
| `asnmap` | ASN → CIDR 段 | `asnmap -a AS13335` |
| `cloudlist` | 云资产枚举（需凭证） | `cloudlist -provider aws` |
| `cdncheck` | 判断 IP 是否 CDN | `cdncheck -i ips.txt` |

### 存活探测 / 指纹

| 工具 | 用途 | 典型命令 |
|---|---|---|
| `httpx` | 批量 HTTP 探活+指纹 | `httpx -l urls.txt -title -tech-detect -status-code` |
| `tlsx` | TLS 证书信息 | `tlsx -l hosts.txt -san -cn -expired` |
| `dnsx` | DNS 解析/爆破/记录 | `dnsx -l domains.txt -a -resp -silent` |

### 目录 / 参数 / 内容发现

| 工具 | 用途 | 典型命令 |
|---|---|---|
| `ffuf` | 通用 fuzz（目录/参数/子域） | `ffuf -u https://t/FUZZ -w list.txt -mc 200,301,403` |
| `gobuster` | 目录/DNS/vhost 爆破 | `gobuster dir -u https://t -w list.txt` |
| `feroxbuster` | 递归目录爆破（需 glibc） | 见下方说明 |
| `katana` | Web 爬虫（爬路径与参数） | `katana -u https://t -jc -d 3 -silent` |
| `gau` | 被动 URL 收集（wayback） | `gau example.com` |
| `uncover` | Quake/Hunter/FOFA 聚合查询 | `uncover -q 'app:"nginx"' -e fofa` |

### 漏洞扫描

| 工具 | 用途 | 典型命令 |
|---|---|---|
| `nuclei` | 模板化漏洞扫描 | `nuclei -l urls.txt -severity critical,high -stats` |
| `afrog` | PoC 框架（中文生态） | `afrog -t https://target -o result.html` |
| `dalfox` | XSS 扫描 | `dalfox url https://t/?q=1 --deep-domxss` |
| `interactsh-client` | OOB 回连（配 nuclei OAST） | `interactsh-client -v` |

### 隧道 / 内网穿透 / 代理

| 工具 | 用途 | 典型命令 |
|---|---|---|
| `chisel` | TCP/UDP/SOCKS 隧道 | `chisel client http://ip:8080 R:socks` |
| `gost` | 多功能代理（SOCKS5/HTTP/中转） | `gost -L socks5://:1080` |
| `frp-frpc` | 内网穿透客户端 | `frpc -c frpc.toml` |
| `frp-frps` | 内网穿透服务端 | `frps -c frps.toml` |
| `npc` | nps 客户端 | `npc -server=ip:8024 -vkey=xxx` |
| `ligolo-agent` | 反向隧道 agent（内网侧） | `ligolo-agent -connect ip:11601 -ignore-cert` |
| `ligolo-proxy` | 反向隧道 proxy（攻击侧） | `ligolo-proxy -selfcert -laddr 0.0.0.0:11601` |

---

## 标准作业流程

### 1. 单目标快速侦察（3 分钟）

```bash
# 1) 子域
subfinder -d example.com -all -silent > subs.txt

# 2) 解析存活
dnsx -l subs.txt -a -resp -silent | awk '{print $1}' > alive.txt

# 3) HTTP 探活 + 指纹
httpx -l alive.txt -title -tech-detect -status-code -silent > web.txt

# 4) 关键路径爬取
katana -list alive.txt -jc -d 2 -silent > urls.txt

# 5) 高危模板扫描
nuclei -l urls.txt -severity critical,high -stats
```

### 2. 多目标批量（先排优先级）

```bash
# CDN 剔除（扫 CDN 后 IP 没意义）
cdncheck -l ips.txt -silent | grep -v '^\[cdn\]' > origin.txt

# 只对非 CDN 做端口扫描
naabu -list origin.txt -top-ports 1000 -silent > ports.txt
```

### 3. 目录爆破（低强度起步）

```bash
# 先 1 万以内的小字典确认有东西
ffuf -u https://target/FUZZ -w small.txt -mc 200,204,301,302,401,403 \
     -rate 30 -t 10 -o ffuf.json -of json

# 命中率正常再换大字典，并发不要超过 40
```

### 4. 建立内网出口

```bash
# 本机开 SOCKS5（供其他工具走）
gost -L socks5://127.0.0.1:1080 &

# 工具接入
curl --socks5-hostname 127.0.0.1:1080 http://internal/
ffuf -u http://internal/FUZZ -w list.txt -x socks5://127.0.0.1:1080
```

---

## nuclei 使用要点

**模板位置**：`~/.config/nuclei/`（首次运行会自动下载）

```bash
# 更新模板（需要联网）
nuclei -update-templates

# 只跑指定分类
nuclei -l urls.txt -tags cve,rce -severity critical

# 指定单模板
nuclei -l urls.txt -t ~/.config/nuclei/http/cves/2024/CVE-2024-xxxx.yaml

# 输出 JSON 便于后续处理
nuclei -l urls.txt -json -o out.jsonl

# 限速（避免打挂目标）
nuclei -l urls.txt -rate-limit 50 -bulk-size 10
```

**注意**：`nuclei` 默认会做很多探测请求。对生产系统先 `-rate-limit 20` 起步。

---

## ffuf 常用模式

```bash
# 目录
ffuf -u https://t/FUZZ -w dirs.txt -mc 200,403

# 参数名
ffuf -u 'https://t/api?FUZZ=1' -w params.txt -fs 1234   # 按响应大小过滤

# vhost
ffuf -u https://t/ -H 'Host: FUZZ.example.com' -w subs.txt -fs 4242

# POST body
ffuf -u https://t/login -X POST -d 'user=admin&pass=FUZZ' -w pass.txt -fr 'invalid'

# 带认证
ffuf -u https://t/FUZZ -w dirs.txt -H 'Cookie: session=xxx'
```

**过滤技巧**：
- `-mc` 匹配状态码
- `-fs` 过滤响应大小（相同大小的是默认页）
- `-fr` 过滤响应内容正则
- `-fc` 过滤状态码

---

## 隧道方案选择

| 场景 | 推荐 | 理由 |
|---|---|---|
| **只需 SOCKS 出口** | `gost -L socks5://:1080` | 最简单，单文件 |
| **需要正向/反向隧道** | `chisel` | 单二进制，支持 SOCKS |
| **目标出网受限** | `ligolo-ng` | 走 TUN，不依赖代理 |
| **有公网中转机** | `frp` | 成熟稳定，支持多协议 |
| **需要 Web 管理** | `nps/npc` | 带 Web 面板 |

### ligolo-ng 完整流程

```bash
# 攻击侧：起 proxy
ligolo-proxy -selfcert -laddr 0.0.0.0:11601

# 内网侧：起 agent（需要上传到目标）
./ligolo-agent -connect <攻击IP>:11601 -ignore-cert

# 回到 proxy 控制台
session                    # 选会话
ifconfig                   # 看内网网卡
start                      # 起 tun（需要 root 建 tun 设备）
# 之后 ip route add <内网段> dev ligolo
```

**注意**：`ligolo` 的 `start` 需要 root 建 TUN 设备。Android 非 root 环境只能起 agent，proxy 侧要在 PC 上跑。

---

## 输出与证据

**统一约定**：所有扫描结果写到任务工作目录，不要写 `/tmp`。

```bash
# 建立工作目录
mkdir -p recon && cd recon

# 每步落盘
subfinder -d example.com -o subs.txt
httpx -l subs.txt -o web.txt
nuclei -l web.txt -o nuclei.txt
```

**证据留存**：发现漏洞时保留

```bash
# 原始响应
curl -isS 'https://t/vuln?id=1' > proof.txt

# 或 nuclei 的 JSON 输出
nuclei -l web.txt -json -o nuclei.jsonl
```

---

## 常见坑

| 问题 | 原因 | 解决 |
|---|---|---|
| `nuclei` 报缺模板 | 首次运行未下载 | `nuclei -update-templates`（需联网） |
| `ffuf` 全部返回相同大小 | 命中默认页 | 加 `-fs <大小>` 过滤 |
| `subfinder` 无结果 | 需要 API key | 配 `~/.config/subfinder/provider-config.yaml` |
| `naabu` 扫不到端口 | 非 root 无法 SYN 扫描 | 改用 `-s connect` |
| `ligolo` start 失败 | 无法建 TUN | 需 root；非 root 只能当 agent |
| `cloudlist` 报错 | 缺云凭证 | 配 `~/.config/cloudlist/config.yaml` |
| `feroxbuster` 无法运行 | 是 glibc 动态链接 | **不可用**，改用 `ffuf` 或 `gobuster` |

---

## 工具安装状态

本 skill 依赖的 16 个二进制已导入到 `data/tools/ext/`：

```
afrog  alterx  asnmap  cdncheck  cloudlist  ffuf  frp-frpc  frp-frps
gobuster  gost  ligolo-agent  ligolo-proxy  npc  puredns  shuffledns  uncover
```

另有 11 个常用工具同样已就位：

```
nuclei  httpx  subfinder  katana  dnsx  tlsx  gau  dalfox
interactsh-client  notify  gitleaks
```

**总计 27 个工具可直接调用。**
