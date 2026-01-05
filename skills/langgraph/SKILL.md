---
name: langgraph
description: Build AI agents with LangGraph using best practices. Use when creating agents, workflows, tool-calling systems, or multi-agent architectures in Python. Covers create_agent (simple) and StateGraph (custom) APIs with state management, persistence, streaming, and human-in-the-loop patterns.
---

# LangGraph Agent Builder

## Quick Decision: Which API?

| Use `create_agent` when... | Use `StateGraph` when... |
|---------------------------|-------------------------|
| Building standard tool-calling agents | Need custom node logic or routing |
| Want middleware (HITL, guardrails) | Building multi-agent systems |
| Prefer minimal boilerplate | Need fine-grained state control |
| Standard ReAct pattern suffices | Complex conditional workflows |

## create_agent Quick Start

```python
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[search],
    system_prompt="You are a helpful assistant.",
    checkpointer=InMemorySaver(),  # Required for memory/HITL
)

# Invoke with thread_id for conversation memory
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Search for LangGraph docs"}]},
    config={"configurable": {"thread_id": "user-123"}}
)
```

## StateGraph Quick Start

```python
from typing import Annotated
from typing_extensions import TypedDict
from langchain.messages import AnyMessage
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

# 1. Define state - MUST be TypedDict
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]  # Reducer appends

# 2. Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

tools = [multiply]
model = init_chat_model("claude-sonnet-4-5-20250929").bind_tools(tools)

# 3. Define nodes
def call_model(state: State):
    return {"messages": [model.invoke(state["messages"])]}

def call_tools(state: State):
    from langchain.messages import ToolMessage
    last = state["messages"][-1]
    results = []
    for tc in last.tool_calls:
        tool_fn = {t.name: t for t in tools}[tc["name"]]
        results.append(ToolMessage(content=str(tool_fn.invoke(tc["args"])), tool_call_id=tc["id"]))
    return {"messages": results}

# 4. Define routing
def should_continue(state: State):
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

# 5. Build graph
graph = (
    StateGraph(State)
    .add_node("model", call_model)
    .add_node("tools", call_tools)
    .add_edge(START, "model")
    .add_conditional_edges("model", should_continue, ["tools", END])
    .add_edge("tools", "model")
    .compile(checkpointer=InMemorySaver())
)
```

## Critical Rules

1. **State MUST be TypedDict** - Pydantic and dataclasses are NOT supported
2. **Use `Annotated` with reducers** for list fields or they'll be replaced, not appended
3. **Always add checkpointer** for HITL, memory, or persistence
4. **Always provide `thread_id`** in config for multi-turn conversations
5. **Nodes must return dict** matching state keys (partial updates OK)
6. **`recursion_limit` is a top-level config key**, not inside `configurable`

## Common Gotchas

### Messages get replaced instead of appended
```python
# WRONG - no reducer
class State(TypedDict):
    messages: list[AnyMessage]  # Each update replaces!

# CORRECT - use add_messages reducer
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

### Forgetting checkpointer for HITL
```python
# WRONG - interrupt() will fail
graph = builder.compile()

# CORRECT
graph = builder.compile(checkpointer=InMemorySaver())
```

### Wrong recursion_limit placement
```python
# WRONG
graph.invoke(inputs, {"configurable": {"recursion_limit": 50}})

# CORRECT - top-level config key
graph.invoke(inputs, {"recursion_limit": 50})
```

### Using Pydantic for state
```python
# WRONG - not supported
class State(BaseModel):
    messages: list[AnyMessage]

# CORRECT - use TypedDict
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

## Checkpointer Selection

| Checkpointer | Use Case |
|--------------|----------|
| `InMemorySaver` | Development, testing |
| `SqliteSaver` | Local persistence, prototypes |
| `PostgresSaver` | Production deployments |

```python
# Development
from langgraph.checkpoint.memory import InMemorySaver
checkpointer = InMemorySaver()

# Production
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string("postgresql://...")
```

## Reference Documentation

Read these for detailed patterns:

- **[state-patterns.md](references/state-patterns.md)** - State schemas, reducers, MessagesState
- **[agent-patterns.md](references/agent-patterns.md)** - Tool binding, middleware, subgraphs
- **[hitl-patterns.md](references/hitl-patterns.md)** - Interrupts, approvals, resuming
- **[streaming-patterns.md](references/streaming-patterns.md)** - Stream modes, custom events
- **[common-errors.md](references/common-errors.md)** - Error codes and fixes
