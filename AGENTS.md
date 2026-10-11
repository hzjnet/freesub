# freesub 项目规范

## 定位与说明
免费节点自动测活订阅池。定期（GitHub Actions）抓取公开节点源，通过 sing-box 内核建立实际代理隧道进行真测活、过滤断流与劫持，按家宽/机房及国家分类导出 Clash / v2rayN / sing-box 订阅。

## 运行与验证
- 云端运行：GitHub Actions `.github/workflows/update.yml`（北京时间每天 06:00、12:00、18:00 或手动 dispatch）。
- 本地调试：`python -X utf8 scripts/main_v2.py`
- 回归测试：`python -X utf8 -m unittest discover -s scripts -p "test_*.py" -v`
- 依赖安装：`pip install -r scripts/requirements.txt`

## 关键目录与文件
- `scripts/main_v2.py`: 核心探测与订阅生成脚本
- `scripts/requirements.txt`: Python 依赖
- `config/sources.yml`: 手动订阅 URL、自动扫描的结果仓库/源码仓库、最后合并的上游结果池及候选地区排除规则
- `.github/workflows/update.yml`: GitHub Actions 工作流
- `output/`: 测活结果订阅文件输出目录（由 Actions 自动提交）
- `README.md`: 包含订阅链接与统计表格的主文档（由脚本自动生成覆盖）

## 测活筛选
- 节点经代理隧道查询四川 DNS `61.139.2.69`，UDP 查询失败时回退 DNS/TCP；主地址不可用或 RTT 超过 800ms 时再测网关 `61.139.2.1`；仅保留有效 RTT 不超过 800ms 的节点。
- 测活前按 `candidate_region_exclusions` 和入口服务器 IP 国家归属预筛；未知位置保留。

## 红线
- 不要在脚本中硬编码个人敏感 Token 或密码。
- 修改 `scripts/main_v2.py` 时保持输出格式与兼容性。
