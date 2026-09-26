"""
backend/external_agents
=======================
ISSUE-1572 (Part 3): External Agents core layer — data contracts, the
durable asynchronous task state machine and the non-blocking Job API.

Layout:
    contracts/     Pydantic schemas (TaskContract + planning/architecture/code artifacts)
    control/       AgentStateManager (QUEUED→…→COMPLETED) + ExternalAgentJobAPI
"""
