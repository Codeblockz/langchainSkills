# Streaming Patterns

## Table of Contents
- [Stream Modes](#stream-modes)
- [Basic Streaming](#basic-streaming)
- [Multiple Stream Modes](#multiple-stream-modes)
- [Custom Data Streaming](#custom-data-streaming)
- [LLM Token Streaming](#llm-token-streaming)
- [Async Considerations](#async-considerations)

## Stream Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `values` | Full state after each step | Debug, state inspection |
| `updates` | State deltas after each step | Efficient progress tracking |
| `messages` | LLM tokens + metadata | Chat UIs |
| `custom` | User-defined data | Progress bars, logs |
| `debug` | Detailed execution trace | Debugging |

## Basic Streaming

### Stream State Updates

```python
for chunk in graph.stream(
    {"messages": [HumanMessage(content="Hello")]},
    stream_mode="updates"
):
    print(chunk)
# Output: {"node_name": {"messages": [...]}}
```

### Stream Full State

```python
for chunk in graph.stream(
    {"messages": [HumanMessage(content="Hello")]},
    stream_mode="values"
):
    print(chunk)
# Output: {"messages": [...all messages...], "other_state": ...}
```

## Multiple Stream Modes

Combine modes for comprehensive streaming:

```python
for mode, chunk in graph.stream(
    {"messages": [HumanMessage(content="Hello")]},
    stream_mode=["updates", "messages", "custom"]
):
    if mode == "updates":
        print(f"State update: {chunk}")
    elif mode == "messages":
        token, metadata = chunk
        print(f"Token: {token.content}")
    elif mode == "custom":
        print(f"Custom: {chunk}")
```

## Custom Data Streaming

Send arbitrary data from nodes:

```python
from langgraph.config import get_stream_writer

def processing_node(state: State):
    writer = get_stream_writer()

    # Stream progress updates
    writer({"status": "Starting processing..."})

    # Do work
    for i, item in enumerate(state["items"]):
        process(item)
        writer({"progress": f"{i+1}/{len(state['items'])}"})

    writer({"status": "Complete!"})
    return {"result": "done"}
```

### Receiving Custom Data

```python
for mode, chunk in graph.stream(
    inputs,
    stream_mode=["updates", "custom"]
):
    if mode == "custom":
        if "progress" in chunk:
            print(f"Progress: {chunk['progress']}")
        elif "status" in chunk:
            print(f"Status: {chunk['status']}")
```

### Custom Data from Tools

```python
from langchain.tools import tool
from langgraph.config import get_stream_writer

@tool
def long_running_search(query: str) -> str:
    """Search with progress updates."""
    writer = get_stream_writer()

    writer(f"Searching for: {query}")
    results = []

    for source in ["web", "database", "cache"]:
        writer(f"Checking {source}...")
        results.extend(search_source(source, query))

    writer(f"Found {len(results)} results")
    return str(results)
```

## LLM Token Streaming

Stream tokens as they're generated:

```python
for mode, chunk in graph.stream(
    {"messages": [HumanMessage(content="Write a poem")]},
    stream_mode=["messages"]
):
    token, metadata = chunk
    if token.content:
        print(token.content, end="", flush=True)
```

### Messages Mode Metadata

```python
for mode, chunk in graph.stream(inputs, stream_mode=["messages"]):
    token, metadata = chunk
    # metadata includes:
    # - langgraph_node: which node generated this
    # - langgraph_triggers: what triggered the node
    # - langgraph_step: step number
    print(f"From node: {metadata.get('langgraph_node')}")
```

## Async Considerations

### Python 3.11+

```python
async for chunk in graph.astream(inputs, stream_mode="updates"):
    print(chunk)
```

### Python < 3.11

`get_stream_writer()` doesn't work in async code. Use `StreamWriter` parameter:

```python
from langgraph.types import StreamWriter

@entrypoint(checkpointer=checkpointer)
async def main(inputs: dict, writer: StreamWriter):
    writer({"status": "Starting..."})
    # ... rest of logic
    return result
```

For nodes:

```python
from langgraph.types import StreamWriter

async def my_node(state: State, writer: StreamWriter):
    writer({"progress": "Working..."})
    result = await do_work()
    return {"result": result}

# Register with writer support
builder.add_node("my_node", my_node)
```

## Stream Events (Advanced)

For fine-grained control, use `astream_events`:

```python
async for event in graph.astream_events(inputs, version="v2"):
    kind = event["event"]

    if kind == "on_chat_model_start":
        print("LLM starting...")
    elif kind == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="")
    elif kind == "on_chat_model_end":
        print("\nLLM complete")
    elif kind == "on_tool_start":
        print(f"Tool: {event['name']}")
```

## Streaming with HITL

Handle interrupts while streaming:

```python
config = {"configurable": {"thread_id": "123"}}

for mode, chunk in graph.stream(
    {"messages": [HumanMessage(content="Delete files")]},
    config,
    stream_mode=["updates", "messages"]
):
    if mode == "updates" and "__interrupt__" in chunk:
        print("Interrupt:", chunk["__interrupt__"])
        break
    elif mode == "messages":
        token, _ = chunk
        print(token.content, end="")

# Resume after approval
from langgraph.types import Command

for mode, chunk in graph.stream(
    Command(resume={"approved": True}),
    config,
    stream_mode=["updates", "messages"]
):
    # Continue processing
    pass
```

## Disable Streaming for Specific Calls

Use `nostream` tag to exclude from message streaming:

```python
# This won't appear in messages stream mode
response = model.with_config({"tags": ["nostream"]}).invoke(messages)
```
