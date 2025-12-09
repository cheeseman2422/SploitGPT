"""
Test tools module
"""

import pytest
from sploitgpt.tools import terminal, execute_tool


@pytest.mark.asyncio
async def test_terminal_echo():
    """Test terminal can run simple commands."""
    result = await terminal("echo 'hello world'")
    assert "hello world" in result


@pytest.mark.asyncio
async def test_terminal_timeout():
    """Test terminal handles timeouts."""
    result = await terminal("sleep 5", timeout=1)
    assert "timed out" in result.lower()


@pytest.mark.asyncio
async def test_execute_tool():
    """Test execute_tool routing."""
    result = await execute_tool("terminal", {"command": "whoami"})
    assert result  # Should return something


@pytest.mark.asyncio
async def test_unknown_tool():
    """Test unknown tool returns error."""
    result = await execute_tool("nonexistent_tool", {})
    assert "Unknown tool" in result
