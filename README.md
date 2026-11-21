# artex-mobile-tools

ARTEX Android 版的外挂工具源。27 个 AArch64 静态 ELF，供 APP 内「下载工具」直接拉取。

---

## 给 APP 用的入口

**`tools.json`** 是唯一入口。APP 只读这一个文件，拿到清单后再按 `url` 逐个下载。

```json
{
  "version": 1,
  "updated": "2026-11-21",
  "tools": [
    {
      "name": "nuclei",
      "version": "3.11.1",
      "description": "模板化漏洞扫描",
      "category": "scan",
      "size": 131891200,
      "sha256": "f27098e0...",
      "url": "https://github.com/Srysfu/artex-mobile-tools/releases/download/tools-v1/nuclei"
    }
  ]
}
```

字段说明：

| 字段 | 用途 |
|---|---|
| `name` | 导入后的命令名，也是保存的文件名 |
| `version` | 展示用 |
| `description` | 列表里的一行说明 |
| `category` | 分组：`recon` / `probe` / `discover` / `scan` / `tunnel` / `util` |
| `size` | 下载前显示体积，也用于校验 |
| `sha256` | **下载后必须校验**，防篡改 |
| `url` | Release 资产直链 |

---

## 为什么用 Release 而不是仓库文件

`cloudlist` 152.9MB、`nuclei` 125.8MB 都超过 GitHub 单文件 100MB 限制。
Release 资产没有这个限制，而且走 CDN，下载更快。

---

## 工具清单（27 个，888 MB）

### 资产测绘 recon（8）

| 工具 | 版本 | 大小 | 用途 |
|---|---|---|---|
| subfinder | 2.17.0 | 27.4M | 被动子域枚举 |
| shuffledns | 1.2.1 | 23.9M | 子域爆破 |
| puredns | 2.1.1 | 7.1M | 子域爆破 + 校验 |
| alterx | 0.1.0 | 18.3M | 子域变形 |
| asnmap | 1.2.0 | 22.9M | ASN → CIDR |
| cloudlist | 1.5.1 | 152.9M | 云资产枚举 |
| cdncheck | 1.4.0 | 21.4M | CDN 判定 |
| uncover | 1.2.1 | 27.6M | 测绘引擎聚合 |

### 探测指纹 probe（4）

| 工具 | 版本 | 大小 | 用途 |
|---|---|---|---|
| httpx | 1.12.0 | 49.6M | 批量 HTTP 探活 + 指纹 |
| dnsx | 1.3.1 | 25.8M | DNS 解析 / 爆破 |
| tlsx | 1.5.0 | 28.6M | TLS 证书信息 |
| gau | 2.2.4 | 7.9M | 被动 URL 收集 |

### 内容发现 discover（4）

| 工具 | 版本 | 大小 | 用途 |
|---|---|---|---|
| katana | 1.8.0 | 62.2M | Web 爬虫 |
| ffuf | 2.3.0 | 9.4M | 通用 fuzz |
| gobuster | 3.8.2 | 8.6M | 目录 / DNS 爆破 |
| dalfox | 3.3.0 | 13.2M | XSS 扫描 |

### 漏洞扫描 scan（4）

| 工具 | 版本 | 大小 | 用途 |
|---|---|---|---|
| nuclei | 3.11.1 | 125.8M | 模板化漏洞扫描 |
| afrog | 3.5.11 | 82.2M | PoC 框架 |
| interactsh-client | 1.4.1 | 24.1M | OOB 回连 |
| gitleaks | 8.30.1 | 19.8M | 密钥泄漏扫描 |

### 隧道 tunnel（6）

| 工具 | 版本 | 大小 | 用途 |
|---|---|---|---|
| gost | 3.3.3 | 43.4M | 多功能代理 |
| frp-frpc | 0.72.0 | 14.8M | frp 客户端 |
| frp-frps | 0.72.0 | 18.2M | frp 服务端 |
| ligolo-agent | 0.9.2 | 6.4M | ligolo 内网 agent |
| ligolo-proxy | 0.9.2 | 19.1M | ligolo 攻击侧 proxy |
| npc | 0.26.10 | 10.4M | nps 客户端 |

### 其他 util（1）

| 工具 | 版本 | 大小 | 用途 |
|---|---|---|---|
| notify | 1.0.7 | 16.8M | 外带通知 |

---

## 全部为 AArch64 静态 ELF

Android 用 **bionic** libc，不提供 glibc 的 `ld-linux-aarch64.so.1` 和 `libc.so.6`。
动态链接的 glibc 程序在 Android 上必然报 `no such file or directory`。

每个文件都验证过：

```
e_machine   = 0xB7  (AArch64)
PT_INTERP   = 无
PT_DYNAMIC  = 无
```

**已排除的工具**：

| 工具 | 原因 |
|---|---|
| feroxbuster | 官方 aarch64 包是 glibc 动态链接，没有 musl 版 |
| nmap / masscan | 需要 root + raw socket |
| sqlmap | Python + PCRE 依赖 |
| hakrawler / waybackurls / massdns / wpscan | 无 arm64 release |
| msfconsole / apktool / jadx | 需要 Ruby / JVM |

---

## skill

`skills/` 下两个方法论 skill，拷到 ARTEX 后端的 skills 目录即可生效：

- `network-offensive` —— 资产测绘到漏洞扫描的完整链路
- `tunnel-pivot` —— 五种隧道方案的选择与配置

---

## 发布 Release

```bash
# 打 tag
git tag tools-v1
git push origin tools-v1

# 建 Release 并上传全部二进制
gh release create tools-v1 bin/* \
  --title "工具集 v1" \
  --notes "27 个 AArch64 静态 ELF"
```

或者网页上手动建 Release，把 `bin/` 里 27 个文件拖进去。

**Release tag 必须是 `tools-v1`**——`tools.json` 里的 url 写死了这个 tag。

---

## 更新工具

1. 替换 `bin/` 下的文件
2. 重跑 `scripts/gen_catalog.py` 生成新的 `tools.json`
3. 建新 tag（如 `tools-v2`），上传
4. 改 `tools.json` 里的 url tag，提交

APP 下次拉 `tools.json` 就会看到新版本。

---

## 授权

这些工具只应在**明确授权**的目标上使用。使用者须自行遵守所在地法律法规。
