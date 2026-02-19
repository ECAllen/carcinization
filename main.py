import anthropic

client = anthropic.Anthropic()

conversation_history = []


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
        response = chat(user_input)
        print(f"\n🦀 {response}\n")


if __name__ == "__main__":
    main()
