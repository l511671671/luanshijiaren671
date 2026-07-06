"""Tests for connectors.email_connector."""

from connectors.email_connector import EmailConnector


def test_email_stub_when_not_configured():
    conn = EmailConnector({})
    result = conn.run()
    assert result.success
    assert "配置不完整" in result.output
