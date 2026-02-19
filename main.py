import anthropic

client = anthropic.Anthropic()

conversation_history = []


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


def main():
    print("Coding assistant ready. Type 'exit' to quit.\n")
    while True:
        user_input = input("🧑‍💻 ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue
        response = chat_streaming(user_input)
        print(f"\n🦀 {response}\n")


if __name__ == "__main__":
    main()
