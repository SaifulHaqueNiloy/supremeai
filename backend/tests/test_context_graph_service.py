"""Tests for Context Graph Engine & Brain Visualizer Bridge (Milestone M5.2).

Verifies multi-hop reasoning, shortest-path BFS, graph export, and API router.
"""

from __future__ import annotations

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from api.routes.admin_brain import router
from fastapi import FastAPI
from memory.context_graph_service import (
    ContextGraphService,
    GraphEdge,
    GraphNode,
    MultiHopSubgraph,
    PathTraversalResult,
)


@pytest.fixture
def temp_graph_svc():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    svc = ContextGraphService(db_path=path)
    yield svc
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def test_add_and_get_node(temp_graph_svc: ContextGraphService):
    svc = temp_graph_svc
    node = svc.add_entity_node(
        node_id="user-101",
        node_type="User",
        label="Niloy (Admin)",
        metadata={"email": "admin@supremeai.test"},
        tenant_id="tenant-alpha",
    )
    assert node.id == "user-101"
    assert node.node_type == "User"
    assert node.label == "Niloy (Admin)"

    fetched = svc.get_node("user-101")
    assert fetched is not None
    assert fetched.label == "Niloy (Admin)"
    assert fetched.metadata["email"] == "admin@supremeai.test"


def test_create_relationship_and_neighbors(temp_graph_svc: ContextGraphService):
    svc = temp_graph_svc
    svc.add_entity_node("u1", "User", "User 1")
    svc.add_entity_node("s1", "Session", "Session 1")
    svc.add_entity_node("a1", "Agent", "Architect Agent")

    edge1 = svc.create_relationship("u1", "s1", "STARTS", weight=1.0)
    edge2 = svc.create_relationship("s1", "a1", "DISPATCHES", weight=0.95)

    assert edge1.source_id == "u1"
    assert edge1.target_id == "s1"
    assert edge2.relation_type == "DISPATCHES"

    # Neighbors of s1
    outgoing = svc.get_neighbors("s1", direction="out")
    assert len(outgoing) == 1
    assert outgoing[0]["node"]["id"] == "a1"

    incoming = svc.get_neighbors("s1", direction="in")
    assert len(incoming) == 1
    assert incoming[0]["node"]["id"] == "u1"

    both = svc.get_neighbors("s1", direction="both")
    assert len(both) == 2


def test_multi_hop_subgraph(temp_graph_svc: ContextGraphService):
    svc = temp_graph_svc
    # Build a chain: User -> Session -> Agent -> Skill -> File -> Memory
    nodes = [
        ("u_root", "User", "Root User"),
        ("sess_1", "Session", "Dev Session"),
        ("agt_1", "Agent", "CodeForge Agent"),
        ("sk_1", "Skill", "AST Refactor"),
        ("file_1", "File", "server.py"),
        ("mem_1", "Memory", "Vector Embedding #42"),
    ]
    for nid, ntype, lbl in nodes:
        svc.add_entity_node(nid, ntype, lbl)

    svc.create_relationship("u_root", "sess_1", "STARTS")
    svc.create_relationship("sess_1", "agt_1", "DISPATCHES")
    svc.create_relationship("agt_1", "sk_1", "USES_SKILL")
    svc.create_relationship("agt_1", "file_1", "MUTATES")
    svc.create_relationship("agt_1", "mem_1", "RECALLS")

    # Depth 1 from Session: should include User (depth 1) and Agent (depth 1)
    subgraph_d1 = svc.get_multi_hop_context("sess_1", max_depth=1)
    node_ids_d1 = {n["id"] for n in subgraph_d1.nodes}
    assert node_ids_d1 == {"sess_1", "u_root", "agt_1"}
    assert subgraph_d1.depth_map["sess_1"] == 0
    assert subgraph_d1.depth_map["agt_1"] == 1

    # Depth 2 from User: User -> Session -> Agent
    subgraph_d2 = svc.get_multi_hop_context("u_root", max_depth=2)
    node_ids_d2 = {n["id"] for n in subgraph_d2.nodes}
    assert node_ids_d2 == {"u_root", "sess_1", "agt_1"}

    # Depth 3 from User: User -> Session -> Agent -> (Skill, File, Memory)
    subgraph_d3 = svc.get_multi_hop_context("u_root", max_depth=3)
    node_ids_d3 = {n["id"] for n in subgraph_d3.nodes}
    assert "sk_1" in node_ids_d3
    assert "file_1" in node_ids_d3
    assert "mem_1" in node_ids_d3


def test_find_shortest_path(temp_graph_svc: ContextGraphService):
    svc = temp_graph_svc
    svc.add_entity_node("A", "Session", "A")
    svc.add_entity_node("B", "Agent", "B")
    svc.add_entity_node("C", "Skill", "C")
    svc.add_entity_node("D", "File", "D")

    # A -> B -> C -> D
    # A -> D (direct shortcut)
    svc.create_relationship("A", "B", "DISPATCHES", weight=1.0)
    svc.create_relationship("B", "C", "USES_SKILL", weight=1.0)
    svc.create_relationship("C", "D", "MUTATES", weight=1.0)
    svc.create_relationship("A", "D", "RELIES_ON", weight=0.5)

    # Shortest path in hops from A to D should find the direct link A -> D
    res = svc.find_shortest_path("A", "D")
    assert res.found is True
    assert res.path == ["A", "D"]
    assert len(res.edges) == 1

    # Path from B to D
    res_bd = svc.find_shortest_path("B", "D")
    assert res_bd.found is True
    assert res_bd.path == ["B", "C", "D"]
    assert len(res_bd.edges) == 2


def test_export_for_visualizer(temp_graph_svc: ContextGraphService):
    svc = temp_graph_svc
    svc.add_entity_node("agt-alpha", "Agent", "Architect Agent", {"summary": "Core Architect", "importance": 0.95})
    svc.add_entity_node("mem-1", "Memory", "Vector Node 1", {"summary": "Zero cost policy", "importance": 0.92})
    svc.create_relationship("agt-alpha", "mem-1", "RECALLS", weight=0.88)

    export = svc.export_for_visualizer(tenant_id="ALL")
    assert "nodes" in export
    assert "links" in export
    assert "clusters" in export
    assert "stats" in export
    assert len(export["nodes"]) == 2
    assert len(export["links"]) == 1
    assert export["stats"]["total_memories"] == 2
    assert export["stats"]["total_synapses"] == 1


def test_api_graph_endpoints():
    from api.routes.admin_auth import admin_rate_limit, require_admin_token

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_admin_token] = lambda: {"uid": "admin", "role": "admin"}
    app.dependency_overrides[admin_rate_limit] = lambda: None

    client = TestClient(app)

    # 1. Add Node via API
    res = client.post(
        "/admin-api/brain/nodes",
        json={
            "id": "test-node-1",
            "node_type": "Skill",
            "label": "CodeAnalyzer",
            "metadata": {"version": "2.0"},
            "tenant_id": "default",
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    # 2. Add Target Node
    client.post(
        "/admin-api/brain/nodes",
        json={
            "id": "test-node-2",
            "node_type": "File",
            "label": "main.py",
            "metadata": {"lines": 150},
            "tenant_id": "default",
        },
    )

    # 3. Add Edge
    res_edge = client.post(
        "/admin-api/brain/edges",
        json={
            "source_id": "test-node-1",
            "target_id": "test-node-2",
            "relation_type": "MUTATES",
            "weight": 0.95,
        },
    )
    assert res_edge.status_code == 200

    # 4. Traverse
    res_trav = client.post(
        "/admin-api/brain/traverse",
        json={"source_id": "test-node-1", "target_id": "test-node-2"},
    )
    assert res_trav.status_code == 200
    trav_data = res_trav.json()
    assert trav_data["found"] is True
    assert trav_data["hop_count"] == 1
    assert trav_data["path"] == ["test-node-1", "test-node-2"]

    # 5. Neighbors
    res_nbr = client.get("/admin-api/brain/nodes/test-node-1/neighbors")
    assert res_nbr.status_code == 200
    assert res_nbr.json()["neighbors_count"] >= 1

    # 6. Subgraph (Multi-Hop)
    res_sub = client.get("/admin-api/brain/nodes/test-node-1/subgraph?max_depth=2")
    assert res_sub.status_code == 200
    assert res_sub.json()["nodes_count"] >= 2

    # 7. Graph export
    res_graph = client.get("/admin-api/brain/graph")
    assert res_graph.status_code == 200
    assert "nodes" in res_graph.json()
