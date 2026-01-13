# MeetSpot Campus Edition

> 厦门大学人工智能系《数据结构》大作业  
> Course project based on the open-source MeetSpot.

## Project Overview
This repository adapts the open-source MeetSpot system for Xiamen University campus scenarios. We added a local campus map, data-structure-based routing, and spatial search to support a full campus mode while keeping AMap as an off-campus fallback.

## Features
- Multi-person meeting point recommendation
- Campus mode (XMU): local graph routing + KDTree POI search
- AMap mode: geocoding and POI search for non-campus locations
- Interactive HTML result page with map, markers, and local routes

## Data Structures & Algorithms
- Graph (adjacency list) built from `data/campus/nodes.json` and `data/campus/edges.json`
- Dijkstra shortest path for campus walking distances
- KDTree spatial range search for campus POIs from `data/campus/pois.json`
- Center point calculation: spherical midpoint for 2 points, centroid for 3+ points

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Configure keys (AMap)
# Web service key for backend requests
export AMAP_WEB_SERVICE_KEY=your_web_service_key
# JS key for map rendering
export AMAP_JS_API_KEY=your_js_key
# Optional: JS security code if enabled in AMap console
export AMAP_SECURITY_JS_CODE=your_security_code

# Run
python web_server.py
```
Open http://127.0.0.1:8000

## Campus Mode Trigger
If all input locations are XMU-related keywords ("厦大", "厦门大学", "思明", "翔安"), the system switches to campus mode.

Example request:
```json
{
  "locations": ["厦门大学翔安校区竞丰餐厅", "厦门大学德旺图书馆"],
  "keywords": "咖啡馆"
}
```

## Project Structure (Relevant)
```
MeetSpot/
├── api/                       # FastAPI entry
├── app/                       # Core logic
│   ├── ds/                    # Graph + KDTree implementations
│   └── tool/meetspot_recommender.py
├── data/campus/               # Campus nodes/edges/POIs
├── public/                    # Frontend assets
└── workspace/js_src/          # Generated HTML (runtime cache)
```

## Course Submission Notes
- This is the **Xiamen University AI Department Data Structures course project**.
- `workspace/js_src/` contains generated HTML and should not be committed.
- Do not commit `.env` or API keys; keep secrets local.

## Acknowledgements
Based on the open-source project: https://github.com/JasonRobertDestiny/MeetSpot
