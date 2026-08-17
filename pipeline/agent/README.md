# pipeline/agent/

Agent loop and tool definitions. The agent uses OpenAI-compatible function calling to solve bounded tasks (repair a Dockerfile, write tests, author a verifier). The loop ends when the model replies with no tool calls or hits the turn cap.

## Files

| File | What it does |
|---|---|
| `loop.py` | `Agent` (behind `AgentRunner`): manages the message list, dispatches tool calls, truncates long results, writes a trajectory file to `transcripts/agent/` |
| `tools.py` | Two tool sets. `concrete_tools`: `read_file`, `grep`, `write_file`, `run` (executes only inside the Docker container). `graph_tools`: `show_symbol`, `callers`, `callees`, `tests_for`, `show_commit` (backed by repo graph / history index / git) and `okf` (reads from the `.okf` knowledge bundle). All paths are sandboxed to the workdir or bundle |

## How it's used

Instantiated by the hygiene build-repair step, baseline fix agent, test-gen agent, and task-builder verifier agent. Each caller sets its own system prompt, tool set, and step name (which selects the LLM tier and reasoning level via `config.STEP_MODEL`).

## Not here

- LLM client itself: `pipeline/llm/`
- Container runner behind the `run` tool: `pipeline/docker/`
