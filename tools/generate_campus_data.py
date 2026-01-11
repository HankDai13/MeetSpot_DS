#!/usr/bin/env python3
"""
Campus Data Generator for SmartMeet-DS - Xiamen University Edition

Generates simulated campus road network and POI data for local algorithm testing.
Covers both Xiamen University campuses:
- 思明校区 (Siming Campus): Main campus near the beach
- 翔安校区 (Xiang'an Campus): New campus in Xiang'an District

Output files:
- data/campus/nodes.json: Road intersection nodes
- data/campus/edges.json: Road connections with distance weights
- data/campus/pois.json: Points of Interest (cafes, libraries, canteens)
"""

import json
import math
import os
import random
from collections import deque
from typing import Dict, List, Set, Tuple

# ========== Xiamen University Campus Coordinates (GCJ-02) ==========
# 思明校区 (Siming Campus) - 靠近海边的老校区
SIMING_CENTER_LAT = 24.4380
SIMING_CENTER_LNG = 118.0950

# 翔安校区 (Xiang'an Campus) - 位于翔安区的新校区
XIANGAN_CENTER_LAT = 24.6200
XIANGAN_CENTER_LNG = 118.2870

# Grid parameters for each campus
GRID_ROWS = 6
GRID_COLS = 6
GRID_SPACING_LAT = 0.0015  # ~160m between rows
GRID_SPACING_LNG = 0.0018  # ~160m between cols
NOISE_FACTOR = 0.0003  # Random offset for natural feel


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance between two points using Haversine formula.
    Returns distance in meters.
    """
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def generate_campus_nodes(campus_name: str, center_lat: float, center_lng: float, 
                          node_offset: int, landmarks: Dict) -> List[Dict]:
    """
    Generate road intersection nodes for a single campus in a grid pattern.
    """
    nodes = []
    node_id = node_offset
    
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            # Base position
            lat = center_lat + (row - GRID_ROWS / 2) * GRID_SPACING_LAT
            lng = center_lng + (col - GRID_COLS / 2) * GRID_SPACING_LNG
            
            # Add random noise for natural feel
            lat += random.uniform(-NOISE_FACTOR, NOISE_FACTOR)
            lng += random.uniform(-NOISE_FACTOR, NOISE_FACTOR)
            
            # Get name or generate default
            name = landmarks.get((row, col), f"{campus_name}路口{node_id:02d}")
            
            nodes.append({
                "id": f"N{node_id:03d}",
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "name": name,
                "campus": campus_name,
                "grid_pos": [row, col]  # For edge generation
            })
            node_id += 1
    
    return nodes


def generate_nodes() -> List[Dict]:
    """
    Generate road intersection nodes for both Xiamen University campuses.
    """
    # 思明校区 landmarks
    siming_landmarks = {
        (0, 0): "思明南门",
        (0, 5): "思明西门",
        (5, 0): "思明北门",
        (5, 5): "思明东门",
        (2, 2): "芙蓉湖畔",
        (2, 3): "颂恩楼",
        (3, 2): "建南大礼堂",
        (3, 3): "图书馆",
        (1, 4): "群贤楼群",
        (4, 1): "嘉庚楼群",
        (2, 5): "演武场",
        (4, 4): "勤业餐厅",
    }
    
    # 翔安校区 landmarks
    xiangan_landmarks = {
        (0, 0): "翔安西门",
        (0, 5): "翔安南门",
        (5, 0): "翔安北门",
        (5, 5): "翔安东门",
        (2, 2): "翔安图书馆",
        (2, 3): "翔安主楼",
        (3, 2): "学生活动中心",
        (3, 3): "竞丰餐厅",
        (1, 4): "翔安医院",
        (4, 1): "翔安体育馆",
        (2, 5): "坤銮楼",
        (4, 4): "翔安食堂",
    }
    
    # Generate nodes for both campuses
    siming_nodes = generate_campus_nodes("思明", SIMING_CENTER_LAT, SIMING_CENTER_LNG, 1, siming_landmarks)
    xiangan_nodes = generate_campus_nodes("翔安", XIANGAN_CENTER_LAT, XIANGAN_CENTER_LNG, 37, xiangan_landmarks)
    
    return siming_nodes + xiangan_nodes


def generate_edges(nodes: List[Dict]) -> List[Dict]:
    """
    Generate road edges connecting adjacent nodes within each campus.
    Does NOT connect the two campuses (they are ~25km apart).
    """
    edges = []
    node_map = {n["id"]: n for n in nodes}
    
    # Separate nodes by campus
    siming_nodes = [n for n in nodes if n["campus"] == "思明"]
    xiangan_nodes = [n for n in nodes if n["campus"] == "翔安"]
    
    # Generate edges for each campus separately
    for campus_nodes in [siming_nodes, xiangan_nodes]:
        grid_to_node = {(n["grid_pos"][0], n["grid_pos"][1]): n["id"] for n in campus_nodes}
        
        for node in campus_nodes:
            row, col = node["grid_pos"]
            
            # Right neighbor
            if col < GRID_COLS - 1:
                neighbor_id = grid_to_node.get((row, col + 1))
                if neighbor_id and random.random() < 0.95:
                    _add_edge(edges, node, node_map[neighbor_id])
            
            # Bottom neighbor
            if row < GRID_ROWS - 1:
                neighbor_id = grid_to_node.get((row + 1, col))
                if neighbor_id and random.random() < 0.95:
                    _add_edge(edges, node, node_map[neighbor_id])
            
            # Diagonal (bottom-right) - less common
            if row < GRID_ROWS - 1 and col < GRID_COLS - 1:
                neighbor_id = grid_to_node.get((row + 1, col + 1))
                if neighbor_id and random.random() < 0.3:
                    _add_edge(edges, node, node_map[neighbor_id])
    
    # Ensure each campus is connected internally
    edges = _ensure_campus_connectivity(nodes, edges)
    
    return edges


def _add_edge(edges: List[Dict], node1: Dict, node2: Dict) -> None:
    """Add an edge between two nodes with calculated distance."""
    distance = haversine_distance(
        node1["lat"], node1["lng"],
        node2["lat"], node2["lng"]
    )
    
    edges.append({
        "from": node1["id"],
        "to": node2["id"],
        "weight": round(distance, 1)
    })


def _ensure_campus_connectivity(nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
    """
    Ensure each campus's graph is internally connected using BFS.
    """
    node_map = {n["id"]: n for n in nodes}
    
    for campus_name in ["思明", "翔安"]:
        campus_nodes = [n for n in nodes if n["campus"] == campus_name]
        campus_node_ids = {n["id"] for n in campus_nodes}
        
        # Build adjacency list for this campus
        adj = {nid: set() for nid in campus_node_ids}
        for edge in edges:
            if edge["from"] in campus_node_ids and edge["to"] in campus_node_ids:
                adj[edge["from"]].add(edge["to"])
                adj[edge["to"]].add(edge["from"])
        
        # Find connected components using BFS
        visited = set()
        components = []
        
        for start in campus_node_ids:
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
        
        # Connect components if more than one
        if len(components) > 1:
            print(f"[{campus_name}校区] Found {len(components)} disconnected components, connecting...")
            
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


def generate_pois(nodes: List[Dict]) -> List[Dict]:
    """
    Generate Points of Interest for both campuses.
    """
    pois = []
    poi_id = 1
    
    # 思明校区 POIs
    siming_pois = [
        # Cafés
        {"name": "芙蓉咖啡", "type": "Café", "rating": 4.6},
        {"name": "南光咖啡", "type": "Café", "rating": 4.5},
        {"name": "嘉庚书咖", "type": "Café", "rating": 4.4},
        {"name": "群贤咖啡角", "type": "Café", "rating": 4.3},
        {"name": "演武厅咖啡", "type": "Café", "rating": 4.7},
        # Libraries
        {"name": "厦大图书馆总馆", "type": "Library", "rating": 4.9},
        {"name": "法学院资料室", "type": "Library", "rating": 4.5},
        {"name": "经济学院自习室", "type": "Library", "rating": 4.6},
        # Canteens
        {"name": "勤业餐厅", "type": "Canteen", "rating": 4.4},
        {"name": "芙蓉餐厅", "type": "Canteen", "rating": 4.3},
        {"name": "南光餐厅", "type": "Canteen", "rating": 4.2},
        {"name": "东苑餐厅", "type": "Canteen", "rating": 4.5},
    ]
    
    # 翔安校区 POIs
    xiangan_pois = [
        # Cafés
        {"name": "翔安湖畔咖啡", "type": "Café", "rating": 4.5},
        {"name": "竞丰咖啡角", "type": "Café", "rating": 4.3},
        {"name": "坤銮书咖", "type": "Café", "rating": 4.6},
        {"name": "翔安图书馆咖啡", "type": "Café", "rating": 4.4},
        # Libraries
        {"name": "翔安图书馆", "type": "Library", "rating": 4.8},
        {"name": "翔安自习中心", "type": "Library", "rating": 4.6},
        {"name": "医学院资料室", "type": "Library", "rating": 4.5},
        # Canteens
        {"name": "竞丰餐厅", "type": "Canteen", "rating": 4.5},
        {"name": "丰庭餐厅", "type": "Canteen", "rating": 4.4},
        {"name": "翔安学生食堂", "type": "Canteen", "rating": 4.3},
    ]
    
    # Get nodes for each campus
    siming_nodes = [n for n in nodes if n["campus"] == "思明"]
    xiangan_nodes = [n for n in nodes if n["campus"] == "翔安"]
    
    # Place 思明 POIs
    selected_siming = random.sample(siming_nodes, min(len(siming_pois), len(siming_nodes)))
    for i, template in enumerate(siming_pois):
        base_node = selected_siming[i % len(selected_siming)]
        poi = _create_poi(poi_id, template, base_node, "思明")
        pois.append(poi)
        poi_id += 1
    
    # Place 翔安 POIs
    selected_xiangan = random.sample(xiangan_nodes, min(len(xiangan_pois), len(xiangan_nodes)))
    for i, template in enumerate(xiangan_pois):
        base_node = selected_xiangan[i % len(selected_xiangan)]
        poi = _create_poi(poi_id, template, base_node, "翔安")
        pois.append(poi)
        poi_id += 1
    
    return pois


def _create_poi(poi_id: int, template: Dict, base_node: Dict, campus: str) -> Dict:
    """Create a single POI near a node."""
    lat = base_node["lat"] + random.uniform(-0.0002, 0.0002)
    lng = base_node["lng"] + random.uniform(-0.0002, 0.0002)
    
    rating = template["rating"] + random.uniform(-0.2, 0.2)
    rating = round(max(3.5, min(5.0, rating)), 1)
    
    return {
        "id": f"P{poi_id:03d}",
        "name": template["name"],
        "type": template["type"],
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "rating": rating,
        "nearest_node": base_node["id"],
        "campus": campus
    }


def save_data(nodes: List[Dict], edges: List[Dict], pois: List[Dict], output_dir: str) -> None:
    """Save generated data to JSON files."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Remove grid_pos from nodes (only needed for edge generation)
    clean_nodes = [{k: v for k, v in n.items() if k != "grid_pos"} for n in nodes]
    
    # Save nodes
    nodes_path = os.path.join(output_dir, "nodes.json")
    with open(nodes_path, "w", encoding="utf-8") as f:
        json.dump({"nodes": clean_nodes}, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved {len(clean_nodes)} nodes to {nodes_path}")
    
    # Save edges
    edges_path = os.path.join(output_dir, "edges.json")
    with open(edges_path, "w", encoding="utf-8") as f:
        json.dump({"edges": edges}, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved {len(edges)} edges to {edges_path}")
    
    # Save POIs
    pois_path = os.path.join(output_dir, "pois.json")
    with open(pois_path, "w", encoding="utf-8") as f:
        json.dump({"pois": pois}, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved {len(pois)} POIs to {pois_path}")
    
    # Save campus metadata
    meta_path = os.path.join(output_dir, "campuses.json")
    campus_meta = {
        "campuses": [
            {
                "name": "思明校区",
                "short_name": "思明",
                "center_lat": SIMING_CENTER_LAT,
                "center_lng": SIMING_CENTER_LNG,
                "keywords": ["思明", "厦大思明", "厦门大学思明", "本部"]
            },
            {
                "name": "翔安校区",
                "short_name": "翔安",
                "center_lat": XIANGAN_CENTER_LAT,
                "center_lng": XIANGAN_CENTER_LNG,
                "keywords": ["翔安", "厦大翔安", "厦门大学翔安"]
            }
        ],
        "trigger_keywords": ["厦大", "厦门大学", "XMU", "xmu", "Campus", "校园"]
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(campus_meta, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved campus metadata to {meta_path}")


def print_stats(nodes: List[Dict], edges: List[Dict], pois: List[Dict]) -> None:
    """Print statistics about generated data."""
    print("\n" + "=" * 50)
    print("厦门大学 Campus Data Generation Complete!")
    print("=" * 50)
    
    for campus_name in ["思明", "翔安"]:
        campus_nodes = [n for n in nodes if n["campus"] == campus_name]
        campus_pois = [p for p in pois if p["campus"] == campus_name]
        print(f"\n{campus_name}校区:")
        print(f"  - Nodes: {len(campus_nodes)}")
        print(f"  - POIs:  {len(campus_pois)}")
    
    print(f"\nTotal: {len(nodes)} nodes, {len(edges)} edges, {len(pois)} POIs")
    
    # POI type breakdown
    poi_types = {}
    for poi in pois:
        poi_types[poi["type"]] = poi_types.get(poi["type"], 0) + 1
    print("\nPOI Distribution:")
    for poi_type, count in sorted(poi_types.items()):
        print(f"  - {poi_type}: {count}")
    
    # Distance stats
    distances = [e["weight"] for e in edges]
    print(f"\nEdge Distances:")
    print(f"  - Min: {min(distances):.1f}m")
    print(f"  - Max: {max(distances):.1f}m")
    print(f"  - Avg: {sum(distances)/len(distances):.1f}m")
    
    # Campus distance
    campus_dist = haversine_distance(
        SIMING_CENTER_LAT, SIMING_CENTER_LNG,
        XIANGAN_CENTER_LAT, XIANGAN_CENTER_LNG
    )
    print(f"\nDistance between campuses: {campus_dist/1000:.1f} km")


def main():
    """Main entry point."""
    random.seed(42)  # For reproducibility
    
    print("Generating Xiamen University campus data...")
    print(f"思明校区: ({SIMING_CENTER_LAT}, {SIMING_CENTER_LNG})")
    print(f"翔安校区: ({XIANGAN_CENTER_LAT}, {XIANGAN_CENTER_LNG})")
    print()
    
    # Generate data
    nodes = generate_nodes()
    edges = generate_edges(nodes)
    pois = generate_pois(nodes)
    
    # Save to files
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "campus")
    output_dir = os.path.abspath(output_dir)
    save_data(nodes, edges, pois, output_dir)
    
    # Print statistics
    print_stats(nodes, edges, pois)


if __name__ == "__main__":
    main()
