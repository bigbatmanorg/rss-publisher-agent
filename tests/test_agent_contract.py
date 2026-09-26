from pathlib import Path
import yaml


def test_agent_has_only_private_publisher_mcp_toolset():
    config = yaml.safe_load((Path(__file__).parents[1] / "agent.yaml").read_text())
    agent = config["agents"]["root"]
    assert len(agent["toolsets"]) == 1
    tool = agent["toolsets"][0]
    assert tool["type"] == "mcp"
    assert tool["remote"]["url"] == "${env.RSS_PUBLISHER_INTERNAL_MCP_URL}"
    assert tool["allow_private_ips"] is True


def test_instruction_forbids_research_and_requires_identity_resolution():
    config = yaml.safe_load((Path(__file__).parents[1] / "agent.yaml").read_text())
    instruction = config["agents"]["root"]["instruction"]
    assert "MUST NOT browse" in instruction
    assert "find_similar_active_entries" in instruction
    assert "If uncertain, prefer a separate new entry" in instruction
    assert "/api/v1/assets" in instruction


def test_agent_uses_current_config_version():
    config = yaml.safe_load((Path(__file__).parents[1] / "agent.yaml").read_text())
    assert config["version"] == "16"
