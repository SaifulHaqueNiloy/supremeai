"""Tests for tools/graph_service.py — Knowledge graph service."""
import pytest
from tools.graph_service import GraphService


class TestGraphService:
    def test_init(self):
        svc = GraphService()
        assert svc is not None

    def test_add_node(self):
        svc = GraphService()
        svc.add_node("node-1", {"type": "concept"})
        assert svc.has_node("node-1")

    def test_add_edge(self):
        svc = GraphService()
        svc.add_node("a", {})
        svc.add_node("b", {})
        svc.add_edge("a", "b", {"relation": "related"})
        assert svc.has_edge("a", "b")

    def test_get_node(self):
        svc = GraphService()
        svc.add_node("n1", {"data": "test"})
        node = svc.get_node("n1")
        assert node is not None
        assert node.get("data") == "test"

    def test_get_neighbors(self):
        svc = GraphService()
        svc.add_node("a", {})
        svc.add_node("b", {})
        svc.add_node("c", {})
        svc.add_edge("a", "b", {})
        svc.add_edge("a", "c", {})
        neighbors = svc.get_neighbors("a")
        assert "b" in neighbors and "c" in neighbors

    def test_remove_node(self):
        svc = GraphService()
        svc.add_node("n1", {})
        svc.remove_node("n1")
        assert not svc.has_node("n1")
