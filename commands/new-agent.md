---
name: new-agent
description: Scaffold a new LangGraph agent with best practices
allowed-tools:
  - Read
  - Write
  - AskUserQuestion
argument-hint: "[filename]"
---

# New LangGraph Agent Command

Create a new LangGraph agent file with best practices baked in.

## Workflow

1. **Ask the user** which agent type they want:
   - `create_agent` - High-level API, simpler, uses middleware
   - `StateGraph` - Low-level API, full control, custom routing

2. **Get filename** from argument or ask user (default: `agent.py`)

3. **Generate the agent file** using the appropriate template below

4. **Inform user** about next steps (install dependencies, customize tools)

## Templates

### create_agent Template

```python
"""
LangGraph Agent using create_agent API

Install: pip install langchain langgraph
"""
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver


# Define your tools
@tool
def search(query: str) -> str:
    """Search for information.

    Args:
        query: The search query
    """
    # TODO: Implement search logic
    return f"Results for: {query}"


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: Math expression to evaluate
    """
    # TODO: Implement safely
    return str(eval(expression))


# Create the agent
agent = create_agent(
    model="claude-sonnet-4-5-20250929",  # or "gpt-4o"
    tools=[search, calculate],
    system_prompt="You are a helpful assistant.",
    checkpointer=InMemorySaver(),  # Required for memory/HITL
)


def main():
    # Invoke with thread_id for conversation memory
    config = {"configurable": {"thread_id": "user-123"}}

    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Hello!"}]},
        config=config
    )

    for msg in result["messages"]:
        print(f"{msg.type}: {msg.content}")


if __name__ == "__main__":
    main()
```

### StateGraph Template

```python
"""
LangGraph Agent using StateGraph API

Install: pip install langchain langgraph
"""
from typing import Annotated, Literal
from typing_extensions import TypedDict

from langchain.messages import AnyMessage, HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver


# 1. Define state - MUST be TypedDict
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]  # Reducer appends messages


# 2. Define tools
@tool
def search(query: str) -> str:
    """Search for information.

    Args:
        query: The search query
    """
    # TODO: Implement search logic
    return f"Results for: {query}"


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: Math expression to evaluate
    """
    # TODO: Implement safely
    return str(eval(expression))


# 3. Setup model with tools
tools = [search, calculate]
tools_by_name = {t.name: t for t in tools}
model = init_chat_model("claude-sonnet-4-5-20250929").bind_tools(tools)


# 4. Define nodes
def call_model(state: State) -> dict:
    """Call the model and return response."""
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        *state["messages"]
    ]
    response = model.invoke(messages)
    return {"messages": [response]}


def call_tools(state: State) -> dict:
    """Execute tool calls from the last message."""
    from langchain.messages import ToolMessage

    last_message = state["messages"][-1]
    results = []

    for tool_call in last_message.tool_calls:
        tool_fn = tools_by_name[tool_call["name"]]
        result = tool_fn.invoke(tool_call["args"])
        results.append(
            ToolMessage(content=str(result), tool_call_id=tool_call["id"])
        )

    return {"messages": results}


# 5. Define routing
def should_continue(state: State) -> Literal["tools", "__end__"]:
    """Route to tools or end based on last message."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


# 6. Build and compile graph
builder = StateGraph(State)
builder.add_node("model", call_model)
builder.add_node("tools", call_tools)
builder.add_edge(START, "model")
builder.add_conditional_edges("model", should_continue, ["tools", END])
builder.add_edge("tools", "model")

# Compile with checkpointer for memory/HITL
graph = builder.compile(checkpointer=InMemorySaver())


def main():
    # Use thread_id for conversation persistence
    config = {"configurable": {"thread_id": "user-123"}}

    result = graph.invoke(
        {"messages": [HumanMessage(content="Hello!")]},
        config=config
    )

    for msg in result["messages"]:
        print(f"{msg.type}: {msg.content}")


if __name__ == "__main__":
    main()
```

## After Generation

Tell the user:
1. Install dependencies: `pip install langchain langgraph`
2. Replace placeholder tool implementations
3. Update the model name if needed
4. Run with: `python <filename>`
