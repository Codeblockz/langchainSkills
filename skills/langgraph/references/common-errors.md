# Common Errors and Fixes

## Table of Contents
- [GRAPH_RECURSION_LIMIT](#graph_recursion_limit)
- [INVALID_GRAPH_NODE_RETURN_VALUE](#invalid_graph_node_return_value)
- [MISSING_CHECKPOINTER](#missing_checkpointer)
- [State Schema Errors](#state-schema-errors)
- [Message Handling Errors](#message-handling-errors)
- [Configuration Errors](#configuration-errors)

## GRAPH_RECURSION_LIMIT

**Error**: `GraphRecursionError: Recursion limit reached`

**Cause**: Graph executed more than `recursion_limit` steps (default: 25).

### Quick Fix

Increase the limit:

```python
# CORRECT - top-level config key
result = graph.invoke(inputs, {"recursion_limit": 50})

# WRONG - not inside configurable
result = graph.invoke(inputs, {"configurable": {"recursion_limit": 50}})
```

### Better Fix - Handle Gracefully

Use `RemainingSteps` to exit cleanly:

```python
from langgraph.managed.is_last_step import RemainingSteps

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: RemainingSteps  # Auto-managed

def should_continue(state: State):
    # Exit before hitting limit
    if state["remaining_steps"] <= 2:
        return END

    if state["messages"][-1].tool_calls:
        return "tools"
    return END
```

### Catch the Error

```python
from langgraph.errors import GraphRecursionError

try:
    result = graph.invoke(inputs, {"recursion_limit": 10})
except GraphRecursionError:
    print("Agent took too many steps - consider simplifying the task")
```

## INVALID_GRAPH_NODE_RETURN_VALUE

**Error**: `InvalidUpdateError: Expected dict, got ...`

**Cause**: Node returned wrong type.

### Fix

Nodes MUST return a dict with state keys:

```python
# WRONG
def my_node(state: State):
    return "done"  # Returns string

# WRONG
def my_node(state: State):
    return state["messages"]  # Returns list

# CORRECT
def my_node(state: State):
    return {"messages": [AIMessage(content="done")]}

# CORRECT - partial update
def my_node(state: State):
    return {"status": "complete"}  # Only update some keys
```

## MISSING_CHECKPOINTER

**Error**: `ValueError: Checkpointer required for interrupt`

**Cause**: Using `interrupt()` or HITL without checkpointer.

### Fix

Always add checkpointer for HITL:

```python
# WRONG
graph = builder.compile()

# CORRECT
from langgraph.checkpoint.memory import InMemorySaver
graph = builder.compile(checkpointer=InMemorySaver())
```

## State Schema Errors

### Using Pydantic Instead of TypedDict

**Error**: Various type errors or unexpected behavior

```python
# WRONG - Pydantic not supported
from pydantic import BaseModel

class State(BaseModel):
    messages: list[AnyMessage]

# CORRECT - Use TypedDict
from typing_extensions import TypedDict

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

### Missing Reducer for Lists

**Symptom**: List gets replaced instead of appended

```python
# WRONG - no reducer
class State(TypedDict):
    messages: list[AnyMessage]  # Replaces on each update!

# CORRECT - use add_messages
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

## Message Handling Errors

### INVALID_TOOL_RESULTS

**Error**: `InvalidToolResults: Tool message missing tool_call_id`

```python
# WRONG
return {"messages": [ToolMessage(content="result")]}

# CORRECT - include tool_call_id
return {"messages": [
    ToolMessage(content="result", tool_call_id=tool_call["id"])
]}
```

### MESSAGE_COERCION_FAILURE

**Error**: `MessageCoercionFailure: Cannot convert to message`

```python
# WRONG - raw string
return {"messages": ["Hello"]}

# CORRECT - proper message type
from langchain.messages import AIMessage
return {"messages": [AIMessage(content="Hello")]}
```

### INVALID_CHAT_HISTORY

**Error**: Messages in wrong order

```python
# WRONG - tool message without preceding AI message with tool_calls
messages = [
    HumanMessage(content="Hi"),
    ToolMessage(content="result", tool_call_id="123")  # No AI message before!
]

# CORRECT - AI message with tool_calls precedes ToolMessage
messages = [
    HumanMessage(content="Hi"),
    AIMessage(content="", tool_calls=[{"id": "123", "name": "search", "args": {}}]),
    ToolMessage(content="result", tool_call_id="123")
]
```

## Configuration Errors

### Thread ID Not Provided

**Symptom**: Conversation doesn't persist between calls

```python
# WRONG - no thread_id
result = graph.invoke(inputs)

# CORRECT
result = graph.invoke(
    inputs,
    {"configurable": {"thread_id": "user-123"}}
)
```

### Reusing Thread ID Incorrectly

**Symptom**: Unexpected state from previous conversation

```python
# Each new conversation needs a new thread_id
import uuid

# New conversation
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# Continue same conversation - reuse thread_id
# Start new conversation - generate new thread_id
```

## Interrupt Errors

### Reordering Interrupts

**Error**: Wrong values returned from interrupt

```python
# WRONG - conditional interrupt order
def my_node(state: State):
    if state["check_a"]:
        a = interrupt("Get A")  # Index 0 sometimes
    b = interrupt("Get B")      # Index 0 or 1 depending on condition
    return {"a": a, "b": b}

# CORRECT - consistent order
def my_node(state: State):
    a = interrupt("Get A") if state["check_a"] else None
    b = interrupt("Get B")
    return {"a": a, "b": b}
```

## Debug Tips

### Visualize Graph

```python
from IPython.display import Image, display

display(Image(graph.get_graph().draw_mermaid_png()))
```

### Enable Debug Streaming

```python
for chunk in graph.stream(inputs, stream_mode="debug"):
    print(chunk)
```

### Check State at Any Point

```python
# Get current state for a thread
state = graph.get_state({"configurable": {"thread_id": "123"}})
print(state.values)
print(state.next)  # Next nodes to execute
```
