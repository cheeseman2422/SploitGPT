"""
SploitGPT Agent

The core AI agent that:
1. Understands natural language tasks
2. Plans using MITRE ATT&CK techniques
3. Asks clarifying questions when needed
4. Executes commands and parses output
5. Chains tools together
"""

import asyncio
import json
from typing import AsyncGenerator

import httpx

from sploitgpt.agent.response import AgentResponse
from sploitgpt.core.boot import BootContext
from sploitgpt.core.config import get_settings
from sploitgpt.tools import TOOLS, execute_tool


SYSTEM_PROMPT = """You are SploitGPT, an autonomous penetration testing AI agent.

## Your Environment
You are running inside a Kali Linux container with full access to security tools.
You have Metasploit, nmap, sqlmap, gobuster, hydra, and 100+ other tools available.

## Rules
1. EXECUTE commands - don't just describe what you would do
2. When multiple attack paths exist, ASK the user which to pursue
3. Save all output to /app/loot/ directory
4. Parse command output and continue based on findings
5. Use MITRE ATT&CK technique IDs when explaining your approach

## Available Tools
You have these tools available via function calling:

- terminal(command): Run any shell command
- ask_user(question, options): Ask user to choose between options
- msf_search(query): Search Metasploit modules
- msf_use(module, options): Run a Metasploit module
- finish(summary): Complete the task with a summary

## Methodology
1. RECON: Discover hosts, ports, services
2. ENUMERATE: Gather detailed service info
3. ANALYZE: Identify vulnerabilities
4. EXPLOIT: Gain access
5. POST-EXPLOIT: Escalate, persist, loot

## Important
- Always explain what you're doing briefly
- If a command fails, try alternatives
- Ask the user when you need clarification
- Never make assumptions about scope - ask if unclear
"""


class Agent:
    """The SploitGPT AI Agent."""
    
    def __init__(self, context: BootContext):
        self.context = context
        self.settings = get_settings()
        self.conversation: list[dict] = []
        self.http_client = httpx.AsyncClient(timeout=120)
    
    async def process(self, user_input: str) -> AsyncGenerator[AgentResponse, None]:
        """Process user input and yield responses."""
        
        # Add user message to conversation
        self.conversation.append({
            "role": "user",
            "content": user_input
        })
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            *self.conversation
        ]
        
        # Call LLM
        try:
            response = await self._call_llm(messages)
        except Exception as e:
            yield AgentResponse(type="error", content=str(e))
            return
        
        # Process response
        async for agent_response in self._process_llm_response(response):
            yield agent_response
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with current context."""
        context_info = f"""
## Current Context
- Hostname: {self.context.hostname}
- User: {self.context.username}
- Known hosts: {', '.join(self.context.known_hosts) if self.context.known_hosts else 'None'}
- Available tools: {len(self.context.available_tools)} tools ready
- Metasploit: {'Connected' if self.context.msf_connected else 'Not available'}
"""
        return SYSTEM_PROMPT + context_info
    
    async def _call_llm(self, messages: list[dict]) -> dict:
        """Call the Ollama LLM."""
        url = f"{self.settings.ollama_host}/api/chat"
        
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "stream": False,
            "tools": self._get_tool_definitions()
        }
        
        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def _get_tool_definitions(self) -> list[dict]:
        """Get tool definitions for function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "terminal",
                    "description": "Run a shell command in the Kali Linux environment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The shell command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ask_user",
                    "description": "Ask the user to choose between multiple options",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question to ask"
                            },
                            "options": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of options for the user to choose from"
                            }
                        },
                        "required": ["question", "options"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "msf_search",
                    "description": "Search Metasploit for exploit modules",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (e.g., 'apache', 'CVE-2021-44228')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "finish",
                    "description": "Complete the task and provide a summary",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "Summary of what was accomplished"
                            }
                        },
                        "required": ["summary"]
                    }
                }
            }
        ]
    
    async def _process_llm_response(self, response: dict) -> AsyncGenerator[AgentResponse, None]:
        """Process the LLM response and execute any tool calls."""
        
        message = response.get("message", {})
        content = message.get("content", "")
        tool_calls = message.get("tool_calls", [])
        
        # Add assistant message to conversation
        self.conversation.append({
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls if tool_calls else None
        })
        
        # Yield any text content
        if content:
            yield AgentResponse(type="message", content=content)
        
        # Execute tool calls
        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            name = function.get("name", "")
            args = function.get("arguments", {})
            
            # Parse args if string
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            
            if name == "terminal":
                command = args.get("command", "")
                yield AgentResponse(type="command", content=command)
                
                # Execute command
                result = await execute_tool("terminal", {"command": command})
                yield AgentResponse(type="result", content=result)
                
                # Add tool result to conversation
                self.conversation.append({
                    "role": "tool",
                    "content": result,
                    "name": "terminal"
                })
                
            elif name == "ask_user":
                question = args.get("question", "")
                options = args.get("options", [])
                yield AgentResponse(
                    type="choice",
                    question=question,
                    options=options
                )
                # Note: Need to wait for user response here
                
            elif name == "msf_search":
                query = args.get("query", "")
                yield AgentResponse(type="command", content=f"searchsploit {query}")
                result = await execute_tool("msf_search", {"query": query})
                yield AgentResponse(type="result", content=result)
                
            elif name == "finish":
                summary = args.get("summary", "")
                yield AgentResponse(type="done", content=summary)
                return
        
        # If there were tool calls, continue the conversation
        if tool_calls:
            messages = [
                {"role": "system", "content": self._build_system_prompt()},
                *self.conversation
            ]
            
            try:
                next_response = await self._call_llm(messages)
                async for agent_response in self._process_llm_response(next_response):
                    yield agent_response
            except Exception as e:
                yield AgentResponse(type="error", content=str(e))
