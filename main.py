import anthropic

client = anthropic.Anthropic()

conversation_history = []


def list_models():
    models = client.models.list()
    for model in models.data:
        print(model.id)


def chat_streaming(user_message: str) -> str:
    conversation_history.append({"role": "user", "content": user_message})

    full_response = ""
    print("\nAssistant: ", end="", flush=True)

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


def chat(user_message: str) -> str:
    conversation_history.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        system="You are a coding assistant. Help the user write, understand, and debug code.",
        messages=conversation_history,
    )

    assistant_message = response.content[0].text
    conversation_history.append({"role": "assistant", "content": assistant_message})

    return assistant_message


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


if __name__ == "__main__":
    main()
