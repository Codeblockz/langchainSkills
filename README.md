# LangGraph Plugin for Claude Code

Build AI agents with LangGraph using best practices. This plugin provides guidance, scaffolding, and validation for creating LangGraph agents in Python.

## Features

- **Skill**: Comprehensive guidance on LangGraph patterns (state management, tools, HITL, streaming, error prevention)
- **Commands**: Scaffold new agents and add tools with best practices baked in
- **Agent**: Proactive code reviewer that catches common LangGraph mistakes

## Installation

```bash
claude --plugin-dir /path/to/langgraph
```

Or copy to your project's `.claude-plugin/` directory.

## Commands

### `/langgraph:new-agent`
Scaffold a new LangGraph agent with your choice of:
- `create_agent` (high-level, simple)
- `StateGraph` (low-level, full control)

### `/langgraph:add-tool`
Add a new tool to an existing agent with proper typing and docstrings.

## Skill Triggers

The langgraph skill activates when you:
- Ask to build an agent with LangGraph
- Work with LangGraph state management
- Need help with human-in-the-loop patterns
- Want streaming or persistence guidance

## Agent

The `langgraph-reviewer` agent:
- **Proactively** reviews LangGraph code after you write it
- Can be **explicitly invoked** to review existing code
- Checks for: missing checkpointers, wrong state types, missing reducers, recursion issues

## Requirements

- Python 3.9+
- `langgraph` package (`pip install langgraph`)
- `langchain` package (`pip install langchain`)
