# MeetSpot 校园版

> **厦门大学人工智能系《数据结构》大作业**  
> 基于开源项目 MeetSpot 的校园模式改造与算法实现。

## 项目概述
本项目在开源 MeetSpot 的基础上，针对厦门大学校园场景进行改造，增加本地校园地图、路网最短路径与空间索引，实现“校园模式 + 高德模式”的双通路推荐。

## 核心功能
- 多人会面点推荐
- 校园模式（厦大）：本地路网 + KDTree 空间搜索
- 高德模式：非校园地址的地理编码与 POI 检索
- HTML 结果页：地图标注、推荐列表、Dijkstra 路径展示

## 数据结构与算法
- 图结构（邻接表）：`data/campus/nodes.json` + `data/campus/edges.json`
- Dijkstra 最短路径：计算校园步行距离
- KDTree 空间索引：在校园 POI 中做半径搜索
- 中心点计算：两点使用球面中点，多点使用质心

## 快速运行
```bash
# 安装依赖
pip install -r requirements.txt

# 配置高德 Key
export AMAP_WEB_SERVICE_KEY=你的Web服务Key
export AMAP_JS_API_KEY=你的JS Key
export AMAP_SECURITY_JS_CODE=你的安全密钥(如已开启)

# 启动服务
python web_server.py
```
浏览器访问 http://127.0.0.1:8000

## 校园模式触发条件
当所有输入地址包含“厦大/厦门大学/思明/翔安”等关键词时，自动切换为校园模式。

示例请求：
```json
{
  "locations": ["厦门大学翔安校区竞丰餐厅", "厦门大学德旺图书馆"],
  "keywords": "咖啡馆"
}
```

## 目录结构（关键部分）
```
MeetSpot/
├── api/                       # FastAPI 入口
├── app/                       # 核心逻辑
│   ├── ds/                    # 图结构与 KDTree
│   └── tool/meetspot_recommender.py
├── data/campus/               # 校园节点/边/POI 数据
├── public/                    # 前端静态资源
└── workspace/js_src/          # 运行时生成 HTML（勿提交）
```

## 大作业提交说明
- 本项目为 **厦门大学人工智能系《数据结构》大作业**。
- `workspace/js_src/` 为运行缓存，不应提交。
- `.env` 与 API Key 不应提交至仓库。

## 致谢
开源基线项目： https://github.com/JasonRobertDestiny/MeetSpot
