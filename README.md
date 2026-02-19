# Code Your Own Code Assistant Part 1

Building a Claude Code-style coding assistant is more approachable than most developers expect. In this series, we'll build one from scratch — starting with a simple interactive loop and adding tools in later parts until we have something genuinely useful.

This first part covers the skeleton: getting a conversation loop running against the Anthropic API with streaming output.

## Preliminaries

**Choosing an LLM**

Not every LLM is a good fit for a coding assistant. The two things that matter most here are code quality and tool use support. Tool use (also called function calling) is what lets the model take actions — reading files, running commands, writing code — rather than just generating text. Without it, you have a chatbot, not an assistant.

I'm using Anthropic's Claude for this project, specifically `claude-sonnet-4-6`. Claude's tool use API is clean and well-documented, and in practice it produces reliable results when deciding whether and how to call tools. Other strong options include OpenAI's GPT-4o and Google's Gemini, which both support tool calling — the patterns in this series translate easily to either.

Anthropic models also have the benefit of having tool/function calling enabled in the 3+ versions. You would need to check that if you are using other models.

**Python for the glue**

We're using Python. It has first-party SDKs from every major LLM provider, subprocess and file I/O are easy, and there's no ceremony around getting something running quickly. In principle you could follow along in TypeScript or Go — the Anthropic SDK exists for both — but the examples here will be Python.

Install the SDK:

```bash
uv add anthropic
```

## Coding the Main Loop

The core of any coding assistant is a read-evaluate-respond loop: read user input, send it to the model, print the response, repeat. Here's the minimal version:

**Loading the API key**

The Anthropic SDK picks up `ANTHROPIC_API_KEY` from your environment automatically, so there's no explicit loading needed in code. Set it once in your shell config or `.env` file:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

If you want to load from a `.env` file instead, `python-dotenv` handles that:

```python
from dotenv import load_dotenv
load_dotenv()
```

You can confirm the key is working and see what models are available:

```python
import anthropic

client = anthropic.Anthropic()

def list_models():
    models = client.models.list()
    for model in models.data:
        print(model.id)

list_models()
```

If the key is missing or invalid you'll get an auth error here rather than buried inside your assistant logic later.

Note well: all 3+ version of the Anthropic models support tool/function calling. If you customize with your own models then you would need to check that. 

**The conversation loop**

A multi-turn conversation means we need to maintain message history. The Anthropic API is stateless — every request includes the full conversation so far.

```python
import anthropic

client = anthropic.Anthropic()

conversation_history = []

def chat(user_message: str) -> str:
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        system="You are a coding assistant. Help the user write, understand, and debug code.",
        messages=conversation_history
    )

    assistant_message = response.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })

    return assistant_message

def main():
    print("Coding assistant ready. Type 'exit' to quit.\n")
    while True:
        user_input = input("🧑‍💻 ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue
        response = chat(user_input)
        print(f"\n🦀 {response}\n")

if __name__ == "__main__":
    main()
```

This works, but there's one problem: for longer responses you're staring at a blank terminal waiting for the full reply to arrive. Streaming fixes that.

**Turning on streaming**

With streaming, tokens print as they're generated — the same experience you get in Claude.ai. The SDK makes this straightforward:

```python
def chat_streaming(user_message: str) -> str:
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    full_response = ""
    print("\nAssistant: ", end="", flush=True)

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        system="You are a coding assistant. Help the user write, understand, and debug code.",
        messages=conversation_history
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text

    print("\n")

    conversation_history.append({
        "role": "assistant",
        "content": full_response
    })

    return full_response
```

The `flush=True` on every print call is important — without it Python buffers the output and you lose the streaming effect entirely.

Swap `chat` for `chat_streaming` in the main loop and you have a responsive, multi-turn coding assistant backed by Claude.

**Adding slash commands**

Slash commands give the user a way to control the assistant without sending messages to the model. They're intercepted in the main loop before anything hits the API:

```python
def handle_slash_command(command: str) -> bool:
    """Returns True if the input was a slash command."""
    if command == "/clear":
        conversation_history.clear()
        print("Conversation cleared.\n")
    elif command == "/models":
        list_models()
    elif command == "/help":
        print("/clear   - clear conversation history")
        print("/models  - list available models")
        print("/help    - show this message")
        print("/exit    - quit\n")
    elif command in ("/exit", "/quit"):
        raise SystemExit
    else:
        print(f"Unknown command: {command}\n")
    return True

def main():
    print("Coding assistant ready. Type /help for commands.\n")
    while True:
        user_input = input("🧑‍💻 ").strip()
        if not user_input:
            continue
        if user_input.startswith("/"):
            handle_slash_command(user_input)
            continue
        chat_streaming(user_input)
```

Any input starting with `/` gets routed to `handle_slash_command` and never reaches the model. Adding a new command is just a new `elif` branch.

## What We Have

At this point the assistant can hold a conversation, maintains context across turns, and streams its output. What it can't do yet is act — it can only talk about files and code, not read or write them. That's the limitation we fix in Part 2.

## Up Next

Part 2 adds three tools: read a file, write a file, and run a shell command. With those three primitives the assistant can actually inspect your codebase and make changes — at which point it starts to feel like a real coding tool. The full source for Part 1 is on [GitHub](https://github.com/ethanallen).
