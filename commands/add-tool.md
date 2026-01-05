---
name: add-tool
description: Add a new tool to an existing LangGraph agent
allowed-tools:
  - Read
  - Edit
  - AskUserQuestion
argument-hint: "<tool-name> [file]"
---

# Add Tool Command

Add a new tool function to an existing LangGraph agent file.

## Workflow

1. **Parse arguments**:
   - First argument: tool name (required)
   - Second argument: file path (optional, will search for agent files)

2. **If no file specified**, search for likely agent files:
   - `agent.py`, `graph.py`, `main.py`
   - Files containing `StateGraph` or `create_agent`

3. **Read the target file** to understand its structure

4. **Ask user** what the tool should do (unless obvious from name)

5. **Generate tool code** following this pattern:

```python
@tool
def tool_name(param1: str, param2: int = 10) -> str:
    """Brief description of what the tool does.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
    """
    # Implementation
    return result
```

6. **Insert the tool** in the appropriate location:
   - After existing tool definitions
   - Before the model/graph setup

7. **Update tool registration**:
   - For `create_agent`: Add to `tools=[...]` list
   - For `StateGraph`: Add to `tools = [...]` and `tools_by_name = {...}`

## Tool Template

```python
@tool
def {tool_name}({parameters}) -> {return_type}:
    """{description}

    Args:
        {arg_docs}
    """
    {implementation}
    return {result}
```

## Best Practices to Apply

1. **Always include docstring** with Args section - LLMs use this
2. **Use type hints** for all parameters and return value
3. **Keep tools focused** - one clear purpose
4. **Return strings** for simple tools (easier for LLM to process)
5. **Handle errors gracefully** - return error messages, don't raise

## Example Additions

### API Tool
```python
@tool
def fetch_weather(city: str) -> str:
    """Get current weather for a city.

    Args:
        city: City name (e.g., "San Francisco")
    """
    # TODO: Call weather API
    return f"Weather in {city}: Sunny, 72°F"
```

### Database Tool
```python
@tool
def query_database(sql: str) -> str:
    """Execute a read-only SQL query.

    Args:
        sql: SQL SELECT query to execute
    """
    # TODO: Implement with proper connection handling
    return "Query results..."
```

### File Tool
```python
@tool
def read_file(path: str) -> str:
    """Read contents of a file.

    Args:
        path: Path to the file to read
    """
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"
```

## After Adding

Remind user to:
1. Implement the TODO placeholder
2. Test the tool in isolation before using with agent
3. Consider error handling for edge cases
