# Human-in-the-Loop Patterns

## Table of Contents
- [Overview](#overview)
- [create_agent with HITL Middleware](#create_agent-with-hitl-middleware)
- [StateGraph with interrupt()](#stategraph-with-interrupt)
- [Resuming Execution](#resuming-execution)
- [Validation Loops](#validation-loops)
- [Tool Approval Patterns](#tool-approval-patterns)

## Overview

Human-in-the-loop (HITL) pauses graph execution for human review. **Requires a checkpointer** to persist state.

```python
# CRITICAL: Always include checkpointer for HITL
from langgraph.checkpoint.memory import InMemorySaver
graph = builder.compile(checkpointer=InMemorySaver())
```

## create_agent with HITL Middleware

Easiest way to add approval workflows:

```python
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[delete_file, read_file, send_email],
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "delete_file": True,  # All decisions allowed
                "read_file": False,   # No approval needed
                "send_email": {
                    "allowed_decisions": ["approve", "reject"],
                    # No editing allowed
                },
            }
        ),
    ],
    checkpointer=InMemorySaver(),
)
```

### Handling Interrupts

```python
config = {"configurable": {"thread_id": "user-123"}}

# Run until interrupt
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Delete old files"}]},
    config=config
)

# Check for interrupt
if "__interrupt__" in result:
    interrupt = result["__interrupt__"][0]
    print(f"Approval needed: {interrupt.value}")

    # Resume with decision
    from langgraph.types import Command
    result = agent.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=config  # Same thread_id
    )
```

## StateGraph with interrupt()

For custom interrupt logic:

```python
from langgraph.types import interrupt

def approval_node(state: State):
    # Get the pending action
    action = state["pending_action"]

    # Interrupt and wait for human input
    decision = interrupt({
        "action": action,
        "message": f"Approve action: {action}?"
    })

    if decision["approved"]:
        return {"status": "approved"}
    else:
        return {"status": "rejected", "reason": decision.get("reason")}
```

### Building the Graph

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

builder = StateGraph(State)
builder.add_node("plan", plan_node)
builder.add_node("approve", approval_node)
builder.add_node("execute", execute_node)

builder.add_edge(START, "plan")
builder.add_edge("plan", "approve")
builder.add_conditional_edges(
    "approve",
    lambda s: "execute" if s["status"] == "approved" else END,
    ["execute", END]
)
builder.add_edge("execute", END)

graph = builder.compile(checkpointer=InMemorySaver())
```

## Resuming Execution

Always use the same `thread_id` to resume:

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": "user-123"}}

# Initial run - will pause at interrupt
result = graph.invoke({"query": "Delete everything"}, config)

# Result contains __interrupt__ with the interrupt value
if "__interrupt__" in result:
    # Human reviews and decides
    human_decision = {"approved": True}

    # Resume with Command
    result = graph.invoke(
        Command(resume=human_decision),
        config  # Same thread_id!
    )
```

### Streaming with HITL

```python
config = {"configurable": {"thread_id": "user-123"}}

for chunk in graph.stream(
    {"messages": [HumanMessage(content="Send email to team")]},
    config,
    stream_mode="updates"
):
    if "__interrupt__" in chunk:
        print("Interrupt:", chunk["__interrupt__"])
        break

# Resume streaming
for chunk in graph.stream(
    Command(resume={"decisions": [{"type": "approve"}]}),
    config,
    stream_mode="updates"
):
    print(chunk)
```

## Validation Loops

Validate human input within interrupt:

```python
from langgraph.types import interrupt

def get_validated_input(state: State):
    prompt = "Enter a positive number:"

    while True:
        answer = interrupt(prompt)

        # Validate
        if isinstance(answer, int) and answer > 0:
            return {"value": answer}

        # Invalid - ask again
        prompt = f"'{answer}' is not valid. Enter a positive number:"
```

**Important**: Don't reorder interrupt calls within a node. LangGraph matches interrupts by index.

## Tool Approval Patterns

### Pre-execution Approval

```python
def tool_with_approval(state: State):
    tool_call = state["pending_tool_call"]

    # Show user what will happen
    decision = interrupt({
        "tool": tool_call["name"],
        "args": tool_call["args"],
        "message": "Approve this tool call?"
    })

    if decision["type"] == "approve":
        result = execute_tool(tool_call)
        return {"messages": [ToolMessage(content=result, tool_call_id=tool_call["id"])]}

    elif decision["type"] == "edit":
        # Use edited args
        edited_call = {**tool_call, "args": decision["args"]}
        result = execute_tool(edited_call)
        return {"messages": [ToolMessage(content=result, tool_call_id=tool_call["id"])]}

    else:  # reject
        return {"messages": [ToolMessage(
            content=f"Tool rejected: {decision.get('reason', 'No reason')}",
            tool_call_id=tool_call["id"]
        )]}
```

### Batch Approval

```python
def batch_approval_node(state: State):
    pending_tools = state["pending_tool_calls"]

    decisions = interrupt({
        "tools": [
            {"name": t["name"], "args": t["args"]}
            for t in pending_tools
        ],
        "message": "Review all pending tool calls"
    })

    results = []
    for tool_call, decision in zip(pending_tools, decisions):
        if decision["approved"]:
            result = execute_tool(tool_call)
            results.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

    return {"messages": results}
```

## Checkpointer Requirements

| Feature | Requires Checkpointer |
|---------|----------------------|
| `interrupt()` | Yes |
| Multi-turn memory | Yes |
| Time travel | Yes |
| `HumanInTheLoopMiddleware` | Yes |
| Basic invoke/stream | No |

Production checkpointers:
```python
# Development
from langgraph.checkpoint.memory import InMemorySaver

# Local persistence
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# Production
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string("postgresql://...")
```
