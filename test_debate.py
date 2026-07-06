"""Tests for multi_agent/debate."""

from multi_agent.debate import DebateOrchestrator, EchoBackend, CodeBuddyBackend


def test_echo_backend():
    backend = EchoBackend()
    assert "echo" in backend.generate("hello world")


def test_debate_orchestrator():
    orch = DebateOrchestrator()
    result = orch.run("test prompt", draft="initial draft", rounds=1)
    assert result["prompt"] == "test prompt"
    assert result["rounds"] == 1
    assert any(t["role"] == "Critic" for t in result["transcript"])
    assert any(t["role"] == "Synthesizer" for t in result["transcript"])
