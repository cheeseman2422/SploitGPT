"""
Test configuration
"""

import pytest


@pytest.fixture
def mock_context():
    """Create a mock boot context."""
    from sploitgpt.core.boot import BootContext
    
    return BootContext(
        hostname="test-host",
        username="root",
        interfaces=[{"name": "eth0", "state": "UP", "addr": "10.0.0.100/24"}],
        available_tools=["nmap", "msfconsole", "sqlmap"],
        missing_tools=[],
        known_hosts=["10.0.0.1", "10.0.0.5"],
        open_ports={"10.0.0.1": [22, 80, 443]},
        msf_connected=True,
        ollama_connected=True,
        model_loaded=True
    )
