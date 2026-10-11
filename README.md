# 🚀 免费节点自动测活订阅池 (含真实家宽/住宅IP甄选)

> 👤 **定制规范命名**: 所有订阅节点均重命名为 `国旗 地区 序号 (家宽)`
> ⚡ **真实可用保障**: 所有节点由 `sing-box vv1.14.0` 内核建立实际代理隧道, 完成真实 HTTPS 双向传输握手 + 出口 IP 穿透验证 + Cloudflare 限速下载断流检测 + TLS 证书校验 (MITM 劫持识别), 拒绝虚假通畅、断流节点与高危劫持节点。
> 🛡️ **全协议支持**: VLESS (Reality/Vision) · VMESS · Trojan · Shadowsocks · Hysteria2 · TUIC · AnyTLS

---

## 📌 全部节点总订阅链接

| 客户端 / 格式类型 | 节点总数 | 免翻 CDN 订阅直链 (国内直连) | 官方原生 Raw 直链 (开启代理) |
| :--- | :---: | :--- | :--- |
| 🚀 **Clash (YAML 格式)** | `3` | [免翻 CDN 直链](https://cdn.jsdelivr.net/gh/hzjnet/freesub@main/output/clash.yaml) | [官方 Raw 直链](https://raw.githubusercontent.com/hzjnet/freesub/main/output/clash.yaml) |
| ⚡ **V2RayN (Base64 格式)** | `3` | [免翻 CDN 直链](https://cdn.jsdelivr.net/gh/hzjnet/freesub@main/output/v2ray.txt) | [官方 Raw 直链](https://raw.githubusercontent.com/hzjnet/freesub/main/output/v2ray.txt) |
| 📦 **sing-box (JSON 格式)** | `3` | [免翻 CDN 直链](https://cdn.jsdelivr.net/gh/hzjnet/freesub@main/output/singbox.json) | [官方 Raw 直链](https://raw.githubusercontent.com/hzjnet/freesub/main/output/singbox.json) |

---

## 🏠 按照家宽分类节点订阅 (住宅 IP 专区)

> 家宽判定六重信号: ① ip-api.com `hosting` 字段 ② `mobile` 移动网络字段 ③ Cloudflare/主流 CDN Anycast 网段比对 ④ MaxMind GeoLite2 ASN 白/黑名单 (覆盖 60+ 国家主流民用运营商) ⑤ rDNS/ISP 名称特征 ⑥ Scamalytics 风控评分复核 (fraud ≥75 降级、≥90 剔除)。排除所有云主机/数据中心/CDN 任播, 保留真实民用宽带与移动网络。

| 家宽地区 | 节点数 | V2RayN 专属订阅 | Clash 专属订阅 | sing-box 专属订阅 |
| :--- | :---: | :---: | :---: | :---: |
| 暂无可用节点 | 0 | - | - | - |

---

## 🗺️ 按照国家分类节点订阅 (非家宽/数据中心节点)

| 地区/国家 | 节点数 | V2RayN 专属订阅 | Clash 专属订阅 | sing-box 专属订阅 |
| :--- | :---: | :---: | :---: | :---: |
| 🇺🇸 美国 (United States) | 2 | [CDN 直链](https://cdn.jsdelivr.net/gh/hzjnet/freesub@main/output/by-country/US.txt) · [Raw 直链](https://raw.githubusercontent.com/hzjnet/freesub/main/output/by-country/US.txt) | [CDN 直链](https://cdn.jsdelivr.net/gh/hzjnet/freesub@main/output/by-country/clash-US.yaml) · [Raw 直链](https://raw.githubusercontent.com/hzjnet/freesub/main/output/by-country/clash-US.yaml) | [CDN 直链](https://cdn.jsdelivr.net/gh/hzjnet/freesub@main/output/by-country/singbox-US.json) · [Raw 直链](https://raw.githubusercontent.com/hzjnet/freesub/main/output/by-country/singbox-US.json) |
| 🇹🇭 泰国 (Thailand) | 1 | [CDN 直链](https://cdn.jsdelivr.net/gh/hzjnet/freesub@main/output/by-country/TH.txt) · [Raw 直链](https://raw.githubusercontent.com/hzjnet/freesub/main/output/by-country/TH.txt) | [CDN 直链](https://cdn.jsdelivr.net/gh/hzjnet/freesub@main/output/by-country/clash-TH.yaml) · [Raw 直链](https://raw.githubusercontent.com/hzjnet/freesub/main/output/by-country/clash-TH.yaml) | [CDN 直链](https://cdn.jsdelivr.net/gh/hzjnet/freesub@main/output/by-country/singbox-TH.json) · [Raw 直链](https://raw.githubusercontent.com/hzjnet/freesub/main/output/by-country/singbox-TH.json) |

---

## 🔒 私有仓库（Private）无感免翻订阅方案 (基于 Cloudflare Workers)

> 如果你希望将本 GitHub 仓库设置为 **Private (私有仓库)** 保护节点资产，外部客户端无法直接拉取原生 Raw 或公共 CDN 链接，可以通过以下 Cloudflare Worker 搭建轻量级私密网关反代：

### 1. 获取 GitHub 永久个人令牌 (PAT)
1. 进入 GitHub -> **Settings** -> **Developer Settings** -> **Personal access tokens (classic)**。
2. 点击 **Generate new token (classic)**，勾选 `repo` 权限，有效期设为 `No expiration`（永不过期）。
3. 复制保存生成的以 `ghp_` 开头的 Token。

### 2. 部署 Cloudflare Worker
登录 Cloudflare Dashboard，创建一个新的 Worker，复制以下脚本粘贴并部署（把 `OWNER`/`REPO`/`GITHUB_TOKEN` 改成你自己的）：

```javascript
export default {
  async fetch(request) {
    const GITHUB_TOKEN = "ghp_你的GitHub永久访问令牌";
    const OWNER = "hzjnet";
    const REPO = "freesub";
    const BRANCH = "main";

    const url = new URL(request.url);
    const filePath = "output" + url.pathname;
    const ghUrl = "https://raw.githubusercontent.com/" + OWNER + "/" + REPO + "/" + BRANCH + "/" + filePath;

    const res = await fetch(ghUrl, {
      headers: {
        "Authorization": "token " + GITHUB_TOKEN,
        "User-Agent": "Cloudflare-Worker"
      }
    });

    if (!res.ok) {
      return new Response("Not Found", { status: 404 });
    }

    return new Response(await res.text(), {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache"
      }
    });
  }
}
```

### 3. 私有订阅链接映射方式
部署后 Worker 会分配一个专属域名（例如 `my-sub.yourname.workers.dev`），你的客户端可以直接无感订阅：
* **总 V2RayN 订阅**: `https://你的域名.workers.dev/v2ray.txt`
* **总 Clash 订阅**: `https://你的域名.workers.dev/clash.yaml`
* **总 sing-box 订阅**: `https://你的域名.workers.dev/singbox.json`
* **台湾家宽 V2RayN**: `https://你的域名.workers.dev/residential-by-country/TW.txt`
* **香港家宽 Clash**: `https://你的域名.workers.dev/residential-by-country/clash-HK.yaml`
* **日本家宽 sing-box**: `https://你的域名.workers.dev/residential-by-country/singbox-JP.json`

---

## ⭐ 项目热度

[![Star History Chart](https://api.star-history.com/svg?repos=hzjnet/freesub&type=Date)](https://star-history.com/#hzjnet/freesub&Date)

---

## 🛠️ 项目使用说明
1. **自动更新机制**：GitHub Actions 每天北京时间 06:00、12:00、18:00 自动运行，也支持手动触发。
2. **来源配置**：编辑 `config/sources.yml` 可手动添加结果订阅 URL 或 GitHub 仓库；配置的仓库会自动扫描节点文件，并跟随 README/网页与 JSON 清单中的订阅链接。OgdenThomas/freesub 结果池在其它来源之后导入并合并。
3. **四川 DNS RTT 筛选**：通过每个候选节点的代理隧道查询 `61.139.2.69`，失败时改用 `61.139.2.1`；RTT 高于 800ms 或无法完成查询的节点不入库。
4. **测活标准**：节点必须通过端口预检、sing-box 实际隧道、出口 IP 穿透、限速下载与 TLS 证书校验后方可入库。
5. **多客户端兼容**：Clash / v2rayN / sing-box 全格式订阅；订阅地址固定，不随每次更新改变。
