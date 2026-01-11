"""
Campus Data Structure Module for SmartMeet-DS

This module provides hand-written implementations of:
- CampusGraph: Graph with Dijkstra's shortest path algorithm
- KDTree: Spatial index for efficient range queries

Note: This module intentionally avoids using networkx or sklearn
to demonstrate data structure fundamentals.
"""

from app.ds.graph_engine import CampusGraph
from app.ds.spatial_index import KDTree

__all__ = ["CampusGraph", "KDTree"]
