# **SmartMeet-DS 团队开发指南**

## **1\. 项目背景**

本项目基于开源项目 MeetSpot 进行二次开发。  
原项目特性： 依赖高德 API 进行 POI 搜索和路径规划。  
本项目目标： 针对数据结构课程大作业，实现“去 API 化”。在特定场景（如校园、园区）下，使用本地实现的图 (Graph)、树 (Tree) 和 堆 (Heap) 算法来替代 API 功能。

## **2\. 团队分工表**

| 角色                                   | 成员       | 核心职责                                                     | 涉及文件                                                     |
| :------------------------------------- | :--------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
| **Backend & Integration** (架构与逻辑) | **成员 A** | 1\. **业务流改造：** 修改 meetspot\_recommender.py，接入本地算法。 2\. **模式切换：** 实现 API 模式与本地算法模式的自动切换。 3\. **接口适配：** 将成员 B 的算法输出转换为前端可用的 JSON 格式。 | app/tool/meetspot\_recommender.py app/ds/adapter.py          |
| **Algorithm Core** (核心算法)          | **成员 B** | 1\. **图算法：** 实现邻接表建图、Dijkstra/Floyd 算法。 2\. **空间索引：** 实现 K-D Tree 的构建与范围查询 (Range Search)。 3\. **堆排序：** 实现用于 Top-K 推荐的 Min-Heap。 | app/ds/graph\_engine.py app/ds/spatial\_index.py app/ds/ranking.py |
| **Frontend & Data** (数据与展示)       | **成员 C** | 1\. **数据工程：** 构造/采集校园地图数据 (GeoJSON/JSON)。 2\. **可视化：** 修改前端模板，在地图上绘制本地计算出的路径。 3\. **性能面板：** 在前端展示算法运行耗时等调试信息。 | data/campus/\*.json templates/js\_src/ app/design\_tokens.py |

## **3\. 开发流程规范**

### **3.1 分支管理**

为了避免冲突，请遵循以下分支策略：

* main (Upstream): 保留原作者代码，用于同步上游修复。  
* dev (Team Root): 我们的主开发分支。  
  * feat/algo-structure (成员 B): 算法开发专用。  
  * feat/backend-logic (成员 A): 业务逻辑整合专用。  
  * feat/data-ui (成员 C): 数据与界面专用。

### **3.2 协作模式**

1. **接口先行 (Interface First):**  
   * 成员 A 和 B 先商定好 Python 类的调用方式。  
   * *Example:* graph.get\_shortest\_path(start\_id, end\_id) 返回 List\[Tuple\[float, float\]\] (坐标列表)。  
2. **数据先行 (Data First):**  
   * 成员 C 在 Day 1 提供一份简单的 nodes.json 和 edges.json 样例数据，供 B 写算法测试使用。  
3. **防冲突 (Conflict Prevention):**  
   * 成员 B **严禁** 修改 app/tool/ 下的原始文件。  
   * 成员 A **严禁** 修改 app/ds/ 下的算法内部实现。

## **4\. 改造技术细节**

### **4.1 数据结构模块 (app/ds/)**

这是本项目的核心得分点，必须**手写**，不能直接调库（如 networkx）。

* **Graph Engine:**  
  * 使用字典模拟邻接表: self.adj \= {node\_id: \[(neighbor\_id, weight), ...\]}  
  * 输入：校园路网数据。  
  * 输出：两点间距离、路径坐标序列。  
* **Spatial Index (K-D Tree):**  
  * 节点结构: class Node: {point, left, right, axis, data}  
  * 功能：替代 API 的 place/around 接口。  
  * 输入：中心坐标、半径。  
  * 输出：范围内的店铺列表。

### **4.2 推荐器改造 (meetspot\_recommender.py)**

成员 A 需要修改 execute 方法：

\# 伪代码逻辑  
async def execute(self, locations, ...):  
    \# 1\. 检查坐标是否在校园范围内  
    if self.\_is\_in\_campus(center\_point):  
        \# \--- 进入本地算法模式 \---  
        \# A. 使用 KD-Tree 查找附近店铺 (Member B's code)  
        nearby\_shops \= self.kdtree.search(center\_point, radius=500)  
          

        \# B. 使用 Graph 计算真实步行距离 (Member B's code)  
        for shop in nearby\_shops:  
            dist, path \= self.graph.dijkstra(center\_point, shop\['coords'\])  
            shop\['\_distance'\] \= dist  
            shop\['\_path\_geometry'\] \= path \# 传给前端画线用  
              
        \# C. 使用 Heap 进行 Top-K 排序  
        recommended \= self.heap\_ranker.get\_top\_k(nearby\_shops, k=5)  
    else:  
        \# \--- 保持原有高德 API 逻辑 \---  
        recommended \= await self.\_search\_pois(...)

## **5\. 数据文件格式约定 (由成员 C 负责)**

**1\. 节点数据 (data/campus/nodes.json)**

$$
  {"id": 1, "name": "北门", "lat": 39.991, "lng": 116.331},  
  {"id": 2, "name": "图书馆", "lat": 39.992, "lng": 116.332}  
$$

**2\. 边数据 (data/campus/edges.json)**

$$
  {"u": 1, "v": 2, "weight": 150}, // 150米  
  {"u": 2, "v": 3, "weight": 80}  
$$

**3\. POI 数据 (data/campus/pois.json)**

$$
{"id": 101, "name": "瑞幸咖啡", "type": "cafe", "lat": 39.993, "lng": 116.333, "rating": 4.8}
$$