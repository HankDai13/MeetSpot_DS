"""
K-D Tree Spatial Index - Hand-written Implementation

Implements a K-D Tree for efficient 2D spatial queries on POI data.
Supports range search with pruning optimization.

This module intentionally avoids sklearn to demonstrate 
data structure fundamentals for course assignment.
"""

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


# Approximate conversion for pruning (degrees to meters at Beijing latitude ~40°N)
# 1 degree latitude ≈ 111km, 1 degree longitude ≈ 85km at 40°N
METERS_PER_LAT_DEGREE = 111000
METERS_PER_LNG_DEGREE = 85000  # cos(40°) * 111000 ≈ 85000


class KDTreeNode:
    """
    Node in a K-D Tree.
    
    Attributes:
        poi: The POI data stored at this node
        axis: The splitting axis (0 for lat, 1 for lng)
        left: Left child (values less than split point)
        right: Right child (values greater than split point)
    """
    
    def __init__(self, poi: Dict, axis: int):
        """
        Initialize a K-D Tree node.
        
        Args:
            poi: POI dictionary with at least 'lat' and 'lng' keys
            axis: Splitting axis (0=lat, 1=lng)
        """
        self.poi = poi
        self.axis = axis  # 0 = lat, 1 = lng
        self.left: Optional['KDTreeNode'] = None
        self.right: Optional['KDTreeNode'] = None
    
    def get_axis_value(self) -> float:
        """Get the coordinate value for the current splitting axis."""
        return self.poi["lat"] if self.axis == 0 else self.poi["lng"]
    
    def __repr__(self) -> str:
        return f"KDTreeNode(poi={self.poi.get('name', 'unknown')}, axis={'lat' if self.axis == 0 else 'lng'})"


class KDTree:
    """
    K-D Tree for 2D spatial indexing of POI data.
    
    A K-D Tree is a binary search tree where each level alternates
    between splitting on latitude and longitude. This allows for
    efficient range queries with O(sqrt(n) + k) average time complexity.
    
    Data Structure:
    - Binary tree with alternating split axes
    - Each node contains one POI
    - Left subtree: points with smaller axis value
    - Right subtree: points with larger axis value
    
    Time Complexity:
    - build: O(n log n) with median selection
    - search_nearby: O(sqrt(n) + k) average case with pruning
    
    Space Complexity: O(n)
    """
    
    def __init__(self):
        """Initialize an empty K-D Tree."""
        self.root: Optional[KDTreeNode] = None
        self.size = 0
    
    def build(self, pois: List[Dict]) -> None:
        """
        Build a balanced K-D Tree from a list of POIs.
        
        Uses median selection at each level for a balanced tree.
        Alternates between lat (axis 0) and lng (axis 1) for splitting.
        
        Args:
            pois: List of POI dictionaries, each with 'lat' and 'lng' keys
        """
        self.size = len(pois)
        self.root = self._build_recursive(pois, depth=0)
    
    def _build_recursive(self, pois: List[Dict], depth: int) -> Optional[KDTreeNode]:
        """
        Recursively build the K-D Tree.
        
        Algorithm:
        1. Select splitting axis based on depth (depth % 2)
        2. Sort POIs by the axis value
        3. Choose median as split point
        4. Recursively build left and right subtrees
        
        Args:
            pois: List of POIs for this subtree
            depth: Current depth in the tree
        
        Returns:
            Root node of the subtree, or None if empty
        """
        if not pois:
            return None
        
        # Alternate between lat (0) and lng (1)
        axis = depth % 2
        axis_key = "lat" if axis == 0 else "lng"
        
        # Sort by the current axis
        sorted_pois = sorted(pois, key=lambda p: p[axis_key])
        
        # Find median index
        median_idx = len(sorted_pois) // 2
        
        # Create node with median POI
        node = KDTreeNode(sorted_pois[median_idx], axis)
        
        # Recursively build subtrees
        node.left = self._build_recursive(sorted_pois[:median_idx], depth + 1)
        node.right = self._build_recursive(sorted_pois[median_idx + 1:], depth + 1)
        
        return node
    
    def search_nearby(self, center: Tuple[float, float], radius: float) -> List[Dict]:
        """
        Find all POIs within a given radius of the center point.
        
        Uses tree traversal with pruning to skip subtrees that
        cannot contain any points within the search radius.
        
        Pruning Logic:
        - If the split plane is entirely outside the search circle,
          we can skip the subtree on that side
        - This provides O(sqrt(n) + k) average case complexity
        
        Args:
            center: (lat, lng) tuple of the center point
            radius: Search radius in meters
        
        Returns:
            List of POI dictionaries within the radius
        """
        results: List[Dict] = []
        
        if self.root is None:
            return results
        
        self._search_recursive(self.root, center, radius, results)
        return results
    
    def _search_recursive(
        self, 
        node: Optional[KDTreeNode], 
        center: Tuple[float, float], 
        radius: float, 
        results: List[Dict]
    ) -> None:
        """
        Recursively search the tree with pruning.
        
        Pruning Strategy:
        1. Calculate distance from center to split plane
        2. If distance > radius, we can prune one subtree
        3. Always check the node itself against the circle
        
        Args:
            node: Current node to search
            center: (lat, lng) center of search
            radius: Search radius in meters
            results: Accumulator list for results
        """
        if node is None:
            return
        
        center_lat, center_lng = center
        poi_lat = node.poi["lat"]
        poi_lng = node.poi["lng"]
        
        # Check if this POI is within the radius
        distance = haversine_distance(center_lat, center_lng, poi_lat, poi_lng)
        if distance <= radius:
            results.append(node.poi)
        
        # Determine which side of the split plane the center is on
        if node.axis == 0:  # Splitting on latitude
            center_axis_value = center_lat
            node_axis_value = poi_lat
            meters_per_degree = METERS_PER_LAT_DEGREE
        else:  # Splitting on longitude
            center_axis_value = center_lng
            node_axis_value = poi_lng
            meters_per_degree = METERS_PER_LNG_DEGREE
        
        # Distance from center to split plane (in meters, approximately)
        split_distance = abs(center_axis_value - node_axis_value) * meters_per_degree
        
        # Decide which subtrees to search
        if center_axis_value < node_axis_value:
            # Center is on the left side
            # Always search left subtree
            self._search_recursive(node.left, center, radius, results)
            
            # Only search right if the circle crosses the split plane
            if split_distance <= radius:
                self._search_recursive(node.right, center, radius, results)
        else:
            # Center is on the right side
            # Always search right subtree
            self._search_recursive(node.right, center, radius, results)
            
            # Only search left if the circle crosses the split plane
            if split_distance <= radius:
                self._search_recursive(node.left, center, radius, results)
    
    def load_from_file(self, pois_file: str) -> bool:
        """
        Load POIs from a JSON file and build the tree.
        
        Args:
            pois_file: Path to pois.json
        
        Returns:
            True if loading succeeded, False otherwise
        """
        try:
            with open(pois_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            pois = data.get("pois", [])
            self.build(pois)
            return True
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading POI data: {e}")
            return False
    
    def find_nearest(self, point: Tuple[float, float]) -> Optional[Dict]:
        """
        Find the nearest POI to a given point.
        
        Note: This is a simple implementation that searches all nearby
        POIs within a reasonable radius. For production, implement
        true nearest neighbor search with tree traversal.
        
        Args:
            point: (lat, lng) tuple
        
        Returns:
            Nearest POI dictionary, or None if tree is empty
        """
        if self.root is None:
            return None
        
        # Start with a small radius and expand if needed
        for radius in [100, 500, 1000, 5000, 10000]:
            nearby = self.search_nearby(point, radius)
            if nearby:
                # Return the closest one
                lat, lng = point
                return min(nearby, key=lambda p: haversine_distance(lat, lng, p["lat"], p["lng"]))
        
        return None
    
    def get_tree_height(self) -> int:
        """Calculate the height of the tree (for debugging)."""
        def height(node: Optional[KDTreeNode]) -> int:
            if node is None:
                return 0
            return 1 + max(height(node.left), height(node.right))
        return height(self.root)
    
    def __len__(self) -> int:
        """Return the number of POIs in the tree."""
        return self.size
    
    def __repr__(self) -> str:
        return f"KDTree(size={self.size}, height={self.get_tree_height()})"
