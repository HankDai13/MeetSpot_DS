"""
Campus Graph Engine - Hand-written Graph Algorithms

Implements a weighted graph using adjacency list representation
with Dijkstra's shortest path algorithm optimized with heapq.

This module intentionally avoids networkx to demonstrate 
data structure fundamentals for course assignment.
"""

import heapq
import json
import math
from typing import Dict, List, Optional, Tuple


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance between two points using Haversine formula.
    
    Args:
        lat1, lng1: Coordinates of first point (degrees)
        lat2, lng2: Coordinates of second point (degrees)
    
    Returns:
        Distance in meters
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


class CampusGraph:
    """
    Campus road network graph using adjacency list representation.
    
    Data Structure:
    - adjacency_list: Dict[node_id -> List[(neighbor_id, weight)]]
    - nodes: Dict[node_id -> {id, lat, lng, name}]
    
    Time Complexity:
    - load_data: O(V + E)
    - dijkstra: O((V + E) log V) with heapq
    - get_nearest_node: O(V) linear search
    
    Space Complexity: O(V + E)
    """
    
    def __init__(self):
        """Initialize an empty graph."""
        self.adjacency_list: Dict[str, List[Tuple[str, float]]] = {}
        self.nodes: Dict[str, Dict] = {}
        self._loaded = False
        # Edge sanity filters to avoid cross-campus and long-jump artifacts.
        self.max_edge_distance_m = 5000.0
        self.min_weight_ratio = 0.1

    def _node_in_campuses(self, node_id: str, campuses: Optional[set]) -> bool:
        if not campuses:
            return True
        node = self.nodes.get(node_id)
        if not node:
            return False
        campus = node.get("campus")
        return campus in campuses
    
    def load_data(self, nodes_file: str, edges_file: str) -> bool:
        """
        Load graph data from JSON files.
        
        Args:
            nodes_file: Path to nodes.json
            edges_file: Path to edges.json
        
        Returns:
            True if loading succeeded, False otherwise
        """
        try:
            # Load nodes
            with open(nodes_file, "r", encoding="utf-8") as f:
                nodes_data = json.load(f)
            
            for node in nodes_data.get("nodes", []):
                node_id = node["id"]
                self.nodes[node_id] = {
                    "id": node_id,
                    "lat": node["lat"],
                    "lng": node["lng"],
                    "name": node.get("name", node_id),
                    "campus": node.get("campus")
                }
                self.adjacency_list[node_id] = []
            
            # Load edges (undirected graph)
            with open(edges_file, "r", encoding="utf-8") as f:
                edges_data = json.load(f)
            
            for edge in edges_data.get("edges", []):
                from_node = edge["from"]
                to_node = edge["to"]
                weight = edge["weight"]
                from_data = self.nodes.get(from_node)
                to_data = self.nodes.get(to_node)
                if not from_data or not to_data:
                    continue

                # Drop cross-campus edges when campus info is available.
                from_campus = from_data.get("campus")
                to_campus = to_data.get("campus")
                if from_campus and to_campus and from_campus != to_campus:
                    continue

                # Drop abnormal long-jump edges or broken weights.
                distance = haversine_distance(
                    from_data["lat"], from_data["lng"],
                    to_data["lat"], to_data["lng"]
                )
                if distance > self.max_edge_distance_m:
                    continue
                if distance > 0 and weight is not None:
                    ratio = weight / distance if weight > 0 else 0
                    if ratio < self.min_weight_ratio:
                        continue
                
                # Add both directions for undirected graph
                if from_node in self.adjacency_list:
                    self.adjacency_list[from_node].append((to_node, weight))
                if to_node in self.adjacency_list:
                    self.adjacency_list[to_node].append((from_node, weight))
            
            self._loaded = True
            return True
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Error loading graph data: {e}")
            return False
    
    def dijkstra(
        self,
        start: str,
        end: str,
        campuses: Optional[set] = None
    ) -> Tuple[float, List[str]]:
        """
        Find the shortest path between two nodes using Dijkstra's algorithm.
        
        Uses a min-heap (priority queue) for O((V+E) log V) time complexity.
        
        Algorithm:
        1. Initialize distances to infinity, start node to 0
        2. Use min-heap with (distance, node) tuples
        3. For each node, relax all neighbors
        4. Track predecessors for path reconstruction
        
        Args:
            start: Starting node ID
            end: Ending node ID
        
        Returns:
            Tuple of (total_distance, path_nodes_list)
            Returns (inf, []) if no path exists
        """
        if not self._loaded:
            return (float('inf'), [])
        
        if start not in self.nodes or end not in self.nodes:
            return (float('inf'), [])
        if not self._node_in_campuses(start, campuses) or not self._node_in_campuses(end, campuses):
            return (float('inf'), [])
        
        # Distance from start to each node
        distances: Dict[str, float] = {node: float('inf') for node in self.nodes}
        distances[start] = 0
        
        # Predecessor for path reconstruction
        predecessors: Dict[str, Optional[str]] = {node: None for node in self.nodes}
        
        # Min-heap: (distance, node_id)
        # Using heapq which is a min-heap implementation
        heap: List[Tuple[float, str]] = [(0, start)]
        
        # Set for visited nodes
        visited: set = set()
        
        while heap:
            # Pop the node with minimum distance
            current_dist, current_node = heapq.heappop(heap)
            
            # Skip if already visited (we may have duplicates in heap)
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            # Early termination if we reached the destination
            if current_node == end:
                break
            
            # Skip if current distance is outdated (larger than recorded)
            if current_dist > distances[current_node]:
                continue
            
            # Relax all neighbors
            for neighbor, weight in self.adjacency_list[current_node]:
                if neighbor in visited:
                    continue
                if not self._node_in_campuses(neighbor, campuses):
                    continue
                
                new_distance = current_dist + weight
                
                # Found a shorter path
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = current_node
                    heapq.heappush(heap, (new_distance, neighbor))
        
        # Reconstruct path
        if distances[end] == float('inf'):
            return (float('inf'), [])
        
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = predecessors[current]
        
        path.reverse()
        
        return (distances[end], path)
    
    def get_nearest_node(
        self,
        lat: float,
        lng: float,
        campuses: Optional[set] = None
    ) -> Optional[str]:
        """
        Find the nearest graph node to given coordinates.
        
        Uses linear search with Haversine distance.
        Time Complexity: O(V)
        
        Args:
            lat: Latitude in degrees
            lng: Longitude in degrees
        
        Returns:
            Node ID of the nearest node, or None if graph is empty
        """
        if not self._loaded or not self.nodes:
            return None
        
        min_distance = float('inf')
        nearest_node = None
        
        for node_id, node_data in self.nodes.items():
            if campuses and node_data.get("campus") not in campuses:
                continue
            distance = haversine_distance(
                lat, lng,
                node_data["lat"], node_data["lng"]
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_node = node_id
        
        return nearest_node
    
    def get_path_coords(self, path: List[str]) -> List[Tuple[float, float]]:
        """
        Convert a node path to a list of coordinates for map rendering.
        
        Args:
            path: List of node IDs representing the path
        
        Returns:
            List of (longitude, latitude) tuples for polyline drawing
            Note: Returns (lng, lat) order for compatibility with AMap
        """
        coords = []
        for node_id in path:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                # AMap uses (lng, lat) order
                coords.append((node["lng"], node["lat"]))
        return coords
    
    def get_all_distances_from(self, start: str) -> Dict[str, float]:
        """
        Compute distances from a start node to all other nodes.
        
        Uses Dijkstra's algorithm without early termination.
        Useful for computing distances to multiple destinations.
        
        Args:
            start: Starting node ID
        
        Returns:
            Dict mapping node_id to distance from start
        """
        if not self._loaded or start not in self.nodes:
            return {}
        
        distances: Dict[str, float] = {node: float('inf') for node in self.nodes}
        distances[start] = 0
        
        heap: List[Tuple[float, str]] = [(0, start)]
        visited: set = set()
        
        while heap:
            current_dist, current_node = heapq.heappop(heap)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            if current_dist > distances[current_node]:
                continue
            
            for neighbor, weight in self.adjacency_list[current_node]:
                if neighbor in visited:
                    continue
                
                new_distance = current_dist + weight
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    heapq.heappush(heap, (new_distance, neighbor))
        
        return distances
    
    @property
    def node_count(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self.nodes)
    
    @property
    def edge_count(self) -> int:
        """Return the number of edges in the graph (counting each direction)."""
        return sum(len(neighbors) for neighbors in self.adjacency_list.values())
    
    def __repr__(self) -> str:
        return f"CampusGraph(nodes={self.node_count}, edges={self.edge_count // 2})"
