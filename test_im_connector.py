"""Tests for connectors.im_connector."""

from connectors.im_connector import IMConnector


def test_im_stub_when_not_configured():
    conn = IMConnector({})
    result = conn.run()
    assert result.success
    assert "未配置" in result.output
