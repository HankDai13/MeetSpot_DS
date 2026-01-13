# 大作业仓库说明

本仓库为 **厦门大学人工智能系《数据结构》大作业** 的代码与文档集合。

## 目录结构（关键部分）
- `app/ds/`：图结构与 KDTree 等数据结构实现
- `app/tool/meetspot_recommender.py`：推荐主流程与校园模式逻辑
- `data/campus/`：校园路网与 POI 数据（nodes / edges / pois）
- `public/` / `static/`：前端静态资源
- `workspace/js_src/`：运行时生成的 HTML 结果页（不要提交）

## 运行方式
- Python 3.11
- 启动：`python web_server.py`
- 高德 Key：
  - `AMAP_WEB_SERVICE_KEY` 用于后端接口调用
  - `AMAP_JS_API_KEY` 用于地图渲染
  - `AMAP_SECURITY_JS_CODE`（如控制台开启安全密钥）

## 算法说明（课程重点）
- **图结构 + Dijkstra**：在校园路网中计算最短路径距离
- **KDTree**：校园 POI 的范围搜索与候选集筛选
- **中心点计算**：两点球面中点，多点质心

## 提交与协作注意事项
- 不提交 `workspace/js_src/` 的生成文件
- 不提交 `.env` 与任何密钥信息
- 保持 `data/campus/` 数据与算法实现一致

---
本仓库说明用于课程大作业整理与提交。若需补充团队成员与分工，可在 README 中新增“成员信息”章节。
