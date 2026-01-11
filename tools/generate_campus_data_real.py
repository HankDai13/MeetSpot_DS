#!/usr/bin/env python3
"""
Campus Data Generator with Real Amap API Data

Fetches real POI data from Amap API for Xiamen University campuses:
- 思明校区 (Siming Campus)
- 翔安校区 (Xiang'an Campus)

Uses LLM to classify POIs into categories (Café, Library, Canteen).

Usage:
    python tools/generate_campus_data_real.py

Requires:
    - AMAP_API_KEY in config/config.toml or environment variable
"""

import asyncio
import json
import math
import os
import sys
from collections import deque
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import aiohttp

# Web service API key for server-side requests
# The config file api_key is web-only, so we use the web service key directly
AMAP_API_KEY = os.getenv("AMAP_WEB_SERVICE_KEY", "c652c6974305500cae8c408d1cfcc161")


async def geocode_location(session: aiohttp.ClientSession, address: str) -> Optional[Tuple[float, float]]:
    """Get coordinates for an address using Amap geocoding API."""
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": AMAP_API_KEY,
        "address": address,
        "output": "json"
    }
    
    try:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if data.get("status") == "1" and data.get("geocodes"):
                location = data["geocodes"][0]["location"]
                lng, lat = location.split(",")
                return (float(lat), float(lng))
    except Exception as e:
        print(f"Geocoding error for '{address}': {e}")
    
    return None


async def search_pois(
    session: aiohttp.ClientSession,
    center: Tuple[float, float],
    radius: int = 2000,
    types: str = "",
    keywords: str = ""
) -> List[Dict]:
    """Search POIs around a location using Amap API."""
    url = "https://restapi.amap.com/v3/place/around"
    all_pois = []
    
    # Paginate through results
    for page in range(1, 4):  # Max 3 pages (60 POIs)
        params = {
            "key": AMAP_API_KEY,
            "location": f"{center[1]},{center[0]}",  # lng,lat format
            "radius": radius,
            "offset": 25,
            "page": page,
            "output": "json",
            "extensions": "all"
        }
        
        if types:
            params["types"] = types
        if keywords:
            params["keywords"] = keywords
        
        # Rate limiting: 3 QPS limit -> sleep 0.4s
        await asyncio.sleep(0.4)
        
        try:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                status = data.get("status")
                info = data.get("info", "")
                
                if status != "1":
                    print(f"    API Error: status={status}, info={info}")
                    # If rate limited, wait longer and retry once
                    if "LIMIT" in str(info):
                        print("    ⚠️ Rate limit hit, waiting 2s...")
                        await asyncio.sleep(2.0)
                        continue
                    break
                
                pois = data.get("pois", [])
                if pois:
                    all_pois.extend(pois)
                    count = int(data.get("count", 0))
                    if len(all_pois) >= count:
                        break
                else:
                    break
        except Exception as e:
            print(f"    POI search error: {e}")
            break
    
    return all_pois


def classify_poi(poi: Dict) -> str:
    """Classify a POI into our categories based on type and name."""
    type_code = poi.get("typecode", "")
    name = poi.get("name", "").lower()
    poi_type = poi.get("type", "").lower()
    
    # Café detection
    cafe_keywords = ["咖啡", "coffee", "café", "星巴克", "瑞幸", "costa", "茶", "奶茶", "书咖"]
    if any(kw in name or kw in poi_type for kw in cafe_keywords):
        return "Café"
    
    # Library detection
    library_keywords = ["图书馆", "图书室", "阅览室", "自习", "library", "资料室", "书店"]
    if any(kw in name or kw in poi_type for kw in library_keywords):
        return "Library"
    
    # Canteen detection
    canteen_keywords = ["食堂", "餐厅", "餐饮", "饭堂", "美食", "小吃", "快餐", "canteen"]
    if any(kw in name or kw in poi_type for kw in canteen_keywords):
        return "Canteen"
    
    # Type code based classification
    if type_code.startswith("050"):  # 餐饮服务
        return "Canteen"
    if type_code.startswith("14"):  # 科教文化
        return "Library"
    
    return "Other"


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in meters."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def generate_nodes_from_pois(pois: List[Dict], campus: str) -> List[Dict]:
    """Generate road nodes from POI locations."""
    nodes = []
    seen_locations = set()
    node_id = 1 if campus == "思明" else 100
    
    for poi in pois:
        location = poi.get("location", "")
        if not location or location in seen_locations:
            continue
        
        try:
            lng, lat = map(float, location.split(","))
            # Round to create a grid-like structure
            grid_lat = round(lat, 4)
            grid_lng = round(lng, 4)
            grid_key = f"{grid_lat},{grid_lng}"
            
            if grid_key in seen_locations:
                continue
            seen_locations.add(grid_key)
            
            nodes.append({
                "id": f"N{node_id:03d}",
                "lat": grid_lat,
                "lng": grid_lng,
                "name": poi.get("name", f"{campus}路口{node_id}"),
                "campus": campus
            })
            node_id += 1
            
        except (ValueError, AttributeError):
            continue
    
    return nodes


def generate_edges(nodes: List[Dict], max_distance: float = 500) -> List[Dict]:
    """Generate edges between nearby nodes."""
    edges = []
    
    for i, node1 in enumerate(nodes):
        for node2 in nodes[i+1:]:
            # Only connect nodes in the same campus
            if node1.get("campus") != node2.get("campus"):
                continue
            
            dist = haversine_distance(
                node1["lat"], node1["lng"],
                node2["lat"], node2["lng"]
            )
            
            if dist <= max_distance:
                edges.append({
                    "from": node1["id"],
                    "to": node2["id"],
                    "weight": round(dist, 1)
                })
    
    return edges


def ensure_connectivity(nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
    """Ensure the graph is connected within each campus."""
    for campus in ["思明", "翔安"]:
        campus_nodes = [n for n in nodes if n.get("campus") == campus]
        if len(campus_nodes) < 2:
            continue
        
        node_ids = {n["id"] for n in campus_nodes}
        node_map = {n["id"]: n for n in campus_nodes}
        
        # Build adjacency
        adj = {nid: set() for nid in node_ids}
        for edge in edges:
            if edge["from"] in node_ids and edge["to"] in node_ids:
                adj[edge["from"]].add(edge["to"])
                adj[edge["to"]].add(edge["from"])
        
        # Find components
        visited = set()
        components = []
        
        for start in node_ids:
            if start in visited:
                continue
            component = set()
            queue = deque([start])
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        queue.append(neighbor)
            components.append(component)
        
        # Connect components
        for i in range(len(components) - 1):
            min_dist = float('inf')
            best_pair = None
            
            for n1 in components[i]:
                for n2 in components[i + 1]:
                    dist = haversine_distance(
                        node_map[n1]["lat"], node_map[n1]["lng"],
                        node_map[n2]["lat"], node_map[n2]["lng"]
                    )
                    if dist < min_dist:
                        min_dist = dist
                        best_pair = (n1, n2)
            
            if best_pair:
                edges.append({
                    "from": best_pair[0],
                    "to": best_pair[1],
                    "weight": round(min_dist, 1)
                })
    
    return edges


async def main():
    """Main entry point."""
    print("=" * 60)
    print("厦门大学校园数据生成器 (Amap API)")
    print("=" * 60)
    print(f"API Key: {AMAP_API_KEY[:8]}...{AMAP_API_KEY[-4:]}")
    print()
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Geocode campus locations
        print("📍 获取校区坐标...")
        
        siming_coords = await geocode_location(session, "厦门大学思明校区")
        xiangan_coords = await geocode_location(session, "厦门大学翔安校区")
        
        if not siming_coords:
            siming_coords = (24.436084, 118.101683)
        print(f"  ✅ 思明校区: {siming_coords}")
        
        if not xiangan_coords:
            xiangan_coords = (24.608429, 118.309669)
        print(f"  ✅ 翔安校区: {xiangan_coords}")
        
        # Step 2: Search POIs
        all_pois = []
        
        # --- 翔安校区全面搜索 (Grid Search) ---
        print(f"\n🔍 搜索 翔安校区 POI (全面模式)...")
        xiangan_pois = []
        seen_ids = set()
        
        # Grid definition for Xiangan (roughly 2km x 2km box around center)
        # Center: 24.608429, 118.309669
        # Delta ~0.01 degrees is roughly 1km
        grid_points = []
        base_lat, base_lng = xiangan_coords
        for lat_offset in [-0.008, 0, 0.008]:
            for lng_offset in [-0.008, 0, 0.008]:
                grid_points.append((base_lat + lat_offset, base_lng + lng_offset))
        
        # Keywords for comprehensive building search
        xiangan_keywords = [
            # Functional
            "餐厅", "食堂", "咖啡", "图书馆", "超市", "便利店", "打印",
            # Academic & Buildings
            "楼", "学院", "中心", "实验室", "研究院", "学生活动中心",
            # Living
            "宿舍", "公寓", "园区", "体育馆", "运动场", "游泳馆"
        ]
        
        total_grids = len(grid_points)
        for i, grid_center in enumerate(grid_points):
            print(f"  Grid {i+1}/{total_grids}: {grid_center}")
            # Search broadly in each grid
            for kw in xiangan_keywords:
                pois = await search_pois(session, grid_center, radius=1000, keywords=kw)
                new_count = 0
                for poi in pois:
                    poi_id = poi.get("id")
                    if poi_id and poi_id not in seen_ids:
                        # Filter to ensure it's actually XMU related (optional, but good for noise reduction)
                        name = poi.get("name", "")
                        # Simple spatial filtering check (is it roughly near campus?)
                        # But for now rely on Amap's proximity
                        seen_ids.add(poi_id)
                        poi["_campus"] = "翔安"
                        xiangan_pois.append(poi)
                        new_count += 1
                # print(f"    + {kw}: {new_count}")

        print(f"  翔安校区总计找到 {len(xiangan_pois)} 个 POI")
        all_pois.extend(xiangan_pois)


        # --- 思明校区标准搜索 ---
        print(f"\n🔍 搜索 思明校区 POI...")
        siming_pois = []
        search_configs = [
            ("", ""),         # All POIs
            ("", "咖啡"),
            ("", "餐厅"),
            ("", "食堂"),
            ("", "图书馆"),
        ]
        
        for types, keywords in search_configs:
            pois = await search_pois(session, siming_coords, radius=1500, types=types, keywords=keywords)
            for poi in pois:
                poi_id = poi.get("id")
                if poi_id and poi_id not in seen_ids:
                    seen_ids.add(poi_id)
                    poi["_campus"] = "思明"
                    siming_pois.append(poi)
                    all_pois.append(poi)
        
        print(f"  思明校区找到 {len(siming_pois)} 个 POI")
        
        # Step 3: Classify POIs
        print(f"\n🏷️ 分类 POI...")
        classified_pois = []
        category_counts = {"Café": 0, "Library": 0, "Canteen": 0, "Building": 0, "Other": 0}
        
        for poi in all_pois:
            # Enhanced classification
            name = poi.get("name", "").lower()
            poi_type = poi.get("type", "").lower()
            category = "Other"
            
            # 1. Café
            if any(kw in name or kw in poi_type for kw in ["咖啡", "coffee", "café", "星巴克", "瑞幸", "茶", "饮品"]):
                category = "Café"
            # 2. Library/Study
            elif any(kw in name or kw in poi_type for kw in ["图书馆", "阅览室", "自习", "书店"]):
                category = "Library"
            # 3. Canteen/Food
            elif any(kw in name or kw in poi_type for kw in ["食堂", "餐厅", "餐饮", "美食", "小吃"]):
                category = "Canteen"
            # 4. Academic/Dorm Buildings (New)
            elif any(kw in name for kw in ["楼", "学院", "中心", "实验室", "宿舍", "公寓", "园区", "体育馆"]):
                category = "Building"
            
            if category != "Other":
                category_counts[category] += 1
                try:
                    lng, lat = map(float, poi["location"].split(","))
                    classified_pois.append({
                        "id": f"P{len(classified_pois)+1:03d}",
                        "name": poi["name"],
                        "type": category,  # Canteen/Library/Café/Building
                        "lat": lat,
                        "lng": lng,
                        "rating": float(poi.get("biz_ext", {}).get("rating", 4.0) or 4.0),
                        "campus": poi["_campus"],
                        "address": poi.get("address", ""),
                        "tel": poi.get("tel", "")
                    })
                except (ValueError, AttributeError):
                    continue
            else:
                # Also add buildings that didn't match specific keywords but have 'Building' type
                pass
        
        print(f"  分布: {category_counts}")
        
        # Step 4: Generate road network
        print(f"\n🛤️ 生成路网...")
        nodes = []
        for campus_name, coords in [("思明", siming_coords), ("翔安", xiangan_coords)]:
            campus_pois_for_nodes = [p for p in classified_pois if p["campus"] == campus_name]
            campus_nodes = generate_nodes_from_pois(
                [{"name": p["name"], "location": f"{p['lng']},{p['lat']}"} for p in campus_pois_for_nodes],
                campus_name
            )
            nodes.extend(campus_nodes)
        
        edges = generate_edges(nodes, max_distance=500) # Increased connection distance
        edges = ensure_connectivity(nodes, edges)
        
        # Link POIs to nearest nodes
        for poi in classified_pois:
            min_dist = float('inf')
            nearest = None
            for node in nodes:
                if node["campus"] == poi["campus"]:
                    dist = haversine_distance(poi["lat"], poi["lng"], node["lat"], node["lng"])
                    if dist < min_dist:
                        min_dist = dist
                        nearest = node["id"]
            poi["nearest_node"] = nearest
        
        print(f"  Nodes: {len(nodes)}, Edges: {len(edges)}")
        
        # Step 5: Save data
        print(f"\n💾 保存数据...")
        output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "campus")
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        # Remove internal fields before saving
        clean_nodes = [{k: v for k, v in n.items()} for n in nodes]
        clean_pois = [{k: v for k, v in p.items() if not k.startswith("_")} for p in classified_pois]
        
        with open(os.path.join(output_dir, "nodes.json"), "w", encoding="utf-8") as f:
            json.dump({"nodes": clean_nodes}, f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(output_dir, "edges.json"), "w", encoding="utf-8") as f:
            json.dump({"edges": edges}, f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(output_dir, "pois.json"), "w", encoding="utf-8") as f:
            json.dump({"pois": clean_pois}, f, ensure_ascii=False, indent=2)
        
        # Save campus metadata
        with open(os.path.join(output_dir, "campuses.json"), "w", encoding="utf-8") as f:
            json.dump({
                "campuses": [
                    {"name": "思明校区", "lat": siming_coords[0], "lng": siming_coords[1]},
                    {"name": "翔安校区", "lat": xiangan_coords[0], "lng": xiangan_coords[1]}
                ]
            }, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ 数据已保存到 {output_dir}")
        print(f"  POIs: {len(classified_pois)} (翔安: {len([p for p in classified_pois if p['campus'] == '翔安'])})")

if __name__ == "__main__":
    asyncio.run(main())
