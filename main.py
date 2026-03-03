import anthropic

client = anthropic.Anthropic()

conversation_history = []

#######################
## Slash commands
#######################


def list_models():
    models = client.models.list()
    for model in models.data:
        print(model.id)


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


#######################
## Tools
#######################

read_file_tool = {
    "name": "read_file",
    "description": "Read the contents of a file at the given path and return them as a string.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the file to read.",
            }
        },
        "required": ["path"],
    },
}


def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


write_file_tool = {
    "name": "write_file",
    "description": "Write content to a file at the given path, creating it if it does not exist.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the file to write.",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file.",
            },
        },
        "required": ["path", "content"],
    },
}


def write_file(path: str, content: str) -> str:
    with open(path, "w") as f:
        f.write(content)
    return f"Wrote {len(content)} characters to {path}."


#######################
## chat and main
#######################


def chat_streaming(user_message: str) -> str:
    conversation_history.append({"role": "user", "content": user_message})

    full_response = ""
    print("\n🦀: ", end="", flush=True)

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        system="You are a coding assistant. Help the user write, understand, and debug code.",
        messages=conversation_history,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text

    print("\n")

    conversation_history.append({"role": "assistant", "content": full_response})

    return full_response


TOOLS = [read_file_tool, write_file_tool]

SYSTEM = (
    "You are a coding assistant. Help the user write, understand, and debug code. "
    "You have access to a read_file tool. Use it to inspect files the user mentions."
)


def chat(user_message: str) -> str:
    conversation_history.append({"role": "user", "content": user_message})

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=SYSTEM,
            tools=TOOLS,
            messages=conversation_history,
        )

        if response.stop_reason == "tool_use":
            conversation_history.append(
                {"role": "assistant", "content": response.content}
            )

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if block.name == "read_file":
                        result = read_file(**block.input)
                    elif block.name == "write_file":
                        result = write_file(**block.input)
                    else:
                        result = f"Unknown tool: {block.name}"
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )

            conversation_history.append({"role": "user", "content": tool_results})

        else:
            assistant_message = next(
                block.text for block in response.content if hasattr(block, "text")
            )
            conversation_history.append(
                {"role": "assistant", "content": assistant_message}
            )
            return assistant_message


def main():
    print("Coding assistant ready. Type /help for commands.\n")
    while True:
        user_input = input("🧑‍💻 ").strip()
        if not user_input:
            continue
        if user_input.startswith("/"):
            handle_slash_command(user_input)
            continue
        response = chat(user_input)
        print(f"\n🦀: {response}\n")


if __name__ == "__main__":
    main()
