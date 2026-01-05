# State Patterns

## Table of Contents
- [TypedDict State Schema](#typeddict-state-schema)
- [Reducers](#reducers)
- [Built-in MessagesState](#built-in-messagesstate)
- [Custom Reducers](#custom-reducers)
- [Overwrite Type](#overwrite-type)
- [Multiple State Keys](#multiple-state-keys)

## TypedDict State Schema

State MUST be a TypedDict. Pydantic models and dataclasses are NOT supported.

```python
from typing import Annotated
from typing_extensions import TypedDict
from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: str
    step_count: int
```

## Reducers

Reducers control how state updates are applied. Without a reducer, updates **replace** the value.

```python
import operator
from typing import Annotated
from typing_extensions import TypedDict

class State(TypedDict):
    # With reducer - appends to list
    items: Annotated[list[str], operator.add]

    # Without reducer - replaces entire value
    current_item: str
```

### Common Reducers

| Reducer | Behavior |
|---------|----------|
| `operator.add` | Concatenate lists/strings |
| `add_messages` | Smart message merging (handles IDs) |
| Custom function | `def reducer(old, new): return ...` |

### add_messages Reducer

Use `add_messages` for message lists - it handles deduplication by message ID:

```python
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

## Built-in MessagesState

For simple agents, use the prebuilt MessagesState:

```python
from langgraph.graph import MessagesState, StateGraph

# MessagesState already has: messages: Annotated[list[AnyMessage], add_messages]
graph = StateGraph(MessagesState)
```

To extend it:

```python
from langgraph.graph import MessagesState

class MyState(MessagesState):
    user_id: str
    metadata: dict
```

## Custom Reducers

Create custom reducers for complex merging logic:

```python
def merge_dicts(old: dict, new: dict) -> dict:
    """Merge new dict into old, preserving old keys not in new."""
    result = old.copy()
    result.update(new)
    return result

class State(TypedDict):
    config: Annotated[dict, merge_dicts]
```

### Counter Reducer Example

```python
def increment(old: int, new: int) -> int:
    return old + new

class State(TypedDict):
    call_count: Annotated[int, increment]

# Node returns {"call_count": 1} each time
# State accumulates: 1, 2, 3, ...
```

## Overwrite Type

Bypass a reducer to directly replace state:

```python
from langgraph.types import Overwrite

def reset_node(state: State):
    # Bypass add_messages reducer, replace entire list
    return {"messages": Overwrite([SystemMessage(content="Reset")])}
```

## Multiple State Keys

Nodes can update any subset of state keys:

```python
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    step: int
    result: str

def step_one(state: State):
    # Only update step and messages
    return {
        "step": 1,
        "messages": [AIMessage(content="Step 1 complete")]
    }

def step_two(state: State):
    # Only update result
    return {"result": "done"}
```

## State with Defaults

TypedDict doesn't support defaults directly. Use `total=False` for optional keys:

```python
class State(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: str  # Optional - may not be present

# Or use Required for specific keys
from typing import Required

class State(TypedDict, total=False):
    messages: Required[Annotated[list[AnyMessage], add_messages]]  # Required
    user_id: str  # Optional
```

## RemainingSteps for Recursion Control

Track steps remaining before recursion limit:

```python
from langgraph.managed.is_last_step import RemainingSteps

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: RemainingSteps  # Auto-managed

def route(state: State):
    if state["remaining_steps"] <= 2:
        return END
    return "continue"
```
