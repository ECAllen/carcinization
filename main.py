import anthropic
import json
import subprocess

client = anthropic.Anthropic()

conversation_history = []
current_model = "claude-sonnet-4-6"

#######################
## Slash commands
#######################


def list_models():
    models = client.models.list()
    for model in models.data:
        print(model.id)


def select_model(model_name: str):
    """Validate and select a model by name."""
    global current_model
    available = [m.id for m in client.models.list().data]
    if model_name in available:
        current_model = model_name
        print(f"Model set to: {current_model}\n")
    else:
        print(f"Unknown model: '{model_name}'")
        print("Available models:")
        for m in available:
            print(f"  {m}")
        print()


def handle_slash_command(command: str) -> bool:
    """Returns True if the input was a slash command."""
    parts = command.split(maxsplit=1)
    base = parts[0]
    arg = parts[1] if len(parts) > 1 else None

    if base == "/clear":
        conversation_history.clear()
        print("Conversation cleared.\n")
    elif base == "/models":
        list_models()
    elif base == "/model":
        if arg:
            select_model(arg)
        else:
            print(f"Current model: {current_model}")
            print("Available models:")
            list_models()
            print()
    elif base == "/help":
        print("/clear            - clear conversation history")
        print("/models           - list available models")
        print("/model            - show current model and list available models")
        print("/model <name>     - switch to the named model")
        print("/help             - show this message")
        print("/exit             - quit\n")
    elif base in ("/exit", "/quit"):
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


# ── curl tool ──────────────────────────────────────────────────────────────────

curl_http_tool = {
    "name": "curl_http",
    "description": (
        "Make an HTTP request using curl. "
        "Use this tool whenever a web page needs to be retrieved from a URL or "
        "data needs to be fetched from an API. "
        "Supports GET, POST, PUT, PATCH, and DELETE methods, custom headers, "
        "request bodies, bearer-token / basic / API-key authentication, "
        "redirect following, SSL control, and configurable timeouts."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The full URL to send the request to.",
            },
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                "description": "HTTP method to use. Defaults to GET.",
            },
            "headers": {
                "type": "object",
                "description": (
                    "Optional key/value map of HTTP headers to include, "
                    "e.g. {\"Authorization\": \"Bearer token\", "
                    "\"Content-Type\": \"application/json\"}."
                ),
                "additionalProperties": {"type": "string"},
            },
            "body": {
                "type": "string",
                "description": (
                    "Optional request body. For JSON APIs supply a JSON string; "
                    "for form data supply a URL-encoded string."
                ),
            },
            "auth_user": {
                "type": "string",
                "description": (
                    "Optional basic-auth credentials in 'username:password' format."
                ),
            },
            "follow_redirects": {
                "type": "boolean",
                "description": "Follow HTTP redirects (curl -L). Defaults to true.",
            },
            "verify_ssl": {
                "type": "boolean",
                "description": (
                    "Verify SSL certificates. Set to false to ignore certificate "
                    "errors (curl -k). Defaults to true."
                ),
            },
            "timeout": {
                "type": "integer",
                "description": (
                    "Maximum time in seconds allowed for the entire operation "
                    "(curl --max-time). Defaults to 30."
                ),
            },
            "connect_timeout": {
                "type": "integer",
                "description": (
                    "Maximum time in seconds to wait for a connection "
                    "(curl --connect-timeout). Defaults to 10."
                ),
            },
        },
        "required": ["url"],
    },
}


def curl_http(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    body: str | None = None,
    auth_user: str | None = None,
    follow_redirects: bool = True,
    verify_ssl: bool = True,
    timeout: int = 30,
    connect_timeout: int = 10,
) -> str:
    """
    Execute a curl command and return a structured result containing the
    HTTP status code, response headers, and response body.
    """
    cmd: list[str] = ["curl", "-s", "-S"]  # silent but show errors

    # ── HTTP method ────────────────────────────────────────────────────────────
    cmd += ["-X", method.upper()]

    # ── Include response headers in the output so we can parse them ───────────
    cmd.append("-i")

    # ── Follow redirects ───────────────────────────────────────────────────────
    if follow_redirects:
        cmd.append("-L")

    # ── SSL verification ───────────────────────────────────────────────────────
    if not verify_ssl:
        cmd.append("-k")

    # ── Timeouts ───────────────────────────────────────────────────────────────
    cmd += ["--max-time", str(timeout)]
    cmd += ["--connect-timeout", str(connect_timeout)]

    # ── Basic auth ─────────────────────────────────────────────────────────────
    if auth_user:
        cmd += ["-u", auth_user]

    # ── Custom headers ─────────────────────────────────────────────────────────
    if headers:
        for key, value in headers.items():
            cmd += ["-H", f"{key}: {value}"]

    # ── Request body ───────────────────────────────────────────────────────────
    if body:
        cmd += ["-d", body]

    # ── URL (always last) ──────────────────────────────────────────────────────
    cmd.append(url)

    # ── Run ────────────────────────────────────────────────────────────────────
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + connect_timeout + 5,  # generous outer timeout
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "curl process timed out", "command": " ".join(cmd)})
    except FileNotFoundError:
        return json.dumps({"error": "curl executable not found. Please install curl."})

    if result.returncode != 0:
        return json.dumps(
            {
                "error": result.stderr.strip() or "curl returned a non-zero exit code",
                "exit_code": result.returncode,
            }
        )

    raw = result.stdout

    # ── Parse status line + headers from the response ─────────────────────────
    # curl -i outputs: <headers block>\r\n\r\n<body>
    # When redirects are followed there may be multiple header blocks; keep the last.
    response_headers: dict[str, str] = {}
    status_code: int | None = None
    body_text: str = raw

    if "\r\n\r\n" in raw:
        *header_blocks, body_text = raw.split("\r\n\r\n")
        last_header_block = header_blocks[-1]
        lines = last_header_block.splitlines()
        if lines:
            # First line: "HTTP/1.1 200 OK"
            status_line = lines[0]
            parts = status_line.split(None, 2)
            if len(parts) >= 2 and parts[1].isdigit():
                status_code = int(parts[1])
            for line in lines[1:]:
                if ":" in line:
                    hname, _, hvalue = line.partition(":")
                    response_headers[hname.strip()] = hvalue.strip()

    # ── Try to pretty-print JSON bodies ───────────────────────────────────────
    content_type = response_headers.get("Content-Type", "")
    parsed_body = None
    if "application/json" in content_type:
        try:
            parsed_body = json.loads(body_text)
        except json.JSONDecodeError:
            pass

    return json.dumps(
        {
            "status_code": status_code,
            "headers": response_headers,
            "body": parsed_body if parsed_body is not None else body_text,
        },
        indent=2,
    )


#######################
## chat and main
#######################


def chat_streaming(user_message: str) -> str:
    conversation_history.append({"role": "user", "content": user_message})

    full_response = ""
    print("\n🦀: ", end="", flush=True)

    with client.messages.stream(
        model=current_model,
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


TOOLS = [read_file_tool, write_file_tool, curl_http_tool]

SYSTEM = (
    "You are a coding assistant. Help the user write, understand, and debug code. "
    "You have access to a read_file tool. Use it to inspect files the user mentions. "
    "You have access to a curl_http tool. Use it whenever you need to retrieve a web "
    "page from a URL or fetch data from an API."
)


def chat(user_message: str) -> str:
    conversation_history.append({"role": "user", "content": user_message})

    while True:
        response = client.messages.create(
            model=current_model,
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
                    elif block.name == "curl_http":
                        result = curl_http(**block.input)
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
