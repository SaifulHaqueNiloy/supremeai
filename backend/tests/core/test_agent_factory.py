from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.agent_factory import DynamicAgentFactory


@pytest.mark.asyncio
async def test_agent_factory_creates_and_saves_agent():
    """এজেন্ট ফ্যাক্টরি এআই রেসপন্স থেকে স্ক্রিপ্ট বানিয়ে ডাটাবেজে সেভ করে তা নিশ্চিত করে।"""
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    factory = DynamicAgentFactory(mock_db)

    # Mock LLMGateway.acompletion to return our expected JSON string
    mock_res = {
        "text": '{"agent_name": "AmazonTracker", "description": "Track prices", "execution_steps": [{"action": "click"}]}'
    }

    with patch(
        "core.llm.llm_gateway.LLMGateway.acompletion",
        new_callable=AsyncMock,
        return_value=mock_res,
    ):
        config = await factory.create_specialized_agent("Track prices on Amazon")
        assert config["agent_name"] == "AmazonTracker"
        assert config["execution_steps"] == [{"action": "click"}]
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
