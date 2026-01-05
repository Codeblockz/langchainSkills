# Agent Patterns

## Table of Contents
- [create_agent API](#create_agent-api)
- [StateGraph API](#stategraph-api)
- [Tool Definition](#tool-definition)
- [Middleware](#middleware)
- [Subgraphs](#subgraphs)
- [Multi-Agent Patterns](#multi-agent-patterns)

## create_agent API

High-level agent creation with built-in tool loop:

```python
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny, 72F"

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_weather],
    system_prompt="You are a weather assistant.",
    checkpointer=InMemorySaver(),
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in NYC?"}]},
    config={"configurable": {"thread_id": "user-123"}}
)
```

### With Custom State

```python
from langchain.agents import AgentState

class CustomState(AgentState):
    user_name: str

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[greet_tool],
    state_schema=CustomState,
)
```

## StateGraph API

Full control over graph structure:

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(State)

# Add nodes
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)

# Add edges
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, ["tools", END])
builder.add_edge("tools", "agent")

graph = builder.compile(checkpointer=InMemorySaver())
```

### Conditional Edges

```python
from typing import Literal

def route_decision(state: State) -> Literal["tools", "summarize", "__end__"]:
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"
    elif state.get("needs_summary"):
        return "summarize"
    return END

builder.add_conditional_edges(
    "agent",
    route_decision,
    ["tools", "summarize", END]  # Possible destinations
)
```

## Tool Definition

### Basic Tool

```python
from langchain.tools import tool

@tool
def search(query: str) -> str:
    """Search for information.

    Args:
        query: The search query
    """
    return f"Results for: {query}"
```

### Tool with Complex Args

```python
from langchain.tools import tool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="Search query")
    max_results: int = Field(default=10, description="Max results")

@tool(args_schema=SearchInput)
def search(query: str, max_results: int = 10) -> str:
    """Search with pagination."""
    return f"Top {max_results} results for: {query}"
```

### Binding Tools to Model

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("claude-sonnet-4-5-20250929")
model_with_tools = model.bind_tools([search, get_weather])
```

### Tool Node Pattern

```python
from langchain.messages import ToolMessage

def tool_node(state: State):
    last_message = state["messages"][-1]
    results = []

    for tool_call in last_message.tool_calls:
        tool = tools_by_name[tool_call["name"]]
        result = tool.invoke(tool_call["args"])
        results.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            )
        )

    return {"messages": results}
```

## Middleware

Middleware wraps agent behavior for cross-cutting concerns:

```python
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[dangerous_tool, safe_tool],
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "dangerous_tool": True,
                "safe_tool": False,
            }
        ),
    ],
    checkpointer=InMemorySaver(),
)
```

### Custom Middleware

```python
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse

class LoggingMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler
    ) -> ModelResponse:
        print(f"Calling model with {len(request.messages)} messages")
        response = handler(request)
        print(f"Got response: {response.message.content[:50]}...")
        return response
```

## Subgraphs

Compose graphs from smaller graphs:

```python
# Define subgraph
subgraph_builder = StateGraph(State)
subgraph_builder.add_node("process", process_node)
subgraph_builder.add_edge(START, "process")
subgraph = subgraph_builder.compile()

# Use as node in parent
parent_builder = StateGraph(State)
parent_builder.add_node("main", main_node)
parent_builder.add_node("sub", subgraph)  # Subgraph as node
parent_builder.add_edge(START, "main")
parent_builder.add_edge("main", "sub")

# Checkpointer propagates automatically
parent = parent_builder.compile(checkpointer=InMemorySaver())
```

### Subgraph with Own Memory

```python
# Subgraph maintains its own state history
subgraph = subgraph_builder.compile(checkpointer=True)
```

## Multi-Agent Patterns

### Supervisor Pattern

```python
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    next_agent: str

def supervisor(state: State):
    # Decide which agent should act next
    response = supervisor_model.invoke(state["messages"])
    return {"next_agent": response.content}

def route_to_agent(state: State):
    return state["next_agent"]

builder = StateGraph(State)
builder.add_node("supervisor", supervisor)
builder.add_node("researcher", researcher_agent)
builder.add_node("writer", writer_agent)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges(
    "supervisor",
    route_to_agent,
    ["researcher", "writer", END]
)
builder.add_edge("researcher", "supervisor")
builder.add_edge("writer", "supervisor")
```

### Handoff Pattern

```python
def agent_with_handoff(state: State):
    response = model.invoke(state["messages"])

    # Check for handoff
    if "HANDOFF:" in response.content:
        target = response.content.split("HANDOFF:")[1].strip()
        return {"messages": [response], "next_agent": target}

    return {"messages": [response], "next_agent": END}
```
