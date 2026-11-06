
import json
import ollama

from agent.tools.registry import execute_tool


MODEL_NAME = "qwen3.5:4b"

def generate_conversation_title(user_message):
    """
    Generate a short, meaningful conversation title using Ollama.
    """

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": """
                            You generate concise titles for chat conversations.

                            Rules:
                            - Understand the user's main intention.
                            - Generate a title of 3 to 6 words.
                            - Use clear, meaningful language.
                            - Do not include quotation marks.
                            - Do not include explanations.
                            - Return only the title.
                            """
                },
                {
                    "role": "user",
                    "content": (
                        "Generate a title for this conversation "
                        "based on the user's first message:\n\n"
                        f"{user_message}"
                    )
                }
            ],
            options={
                "temperature": 0.2
            }
        )

        title = (response.message.content or "").strip()

        # Clean up the generated title.
        title = title.splitlines()[0].strip()
        title = title.strip("\"'`*# ")

        if title.lower().startswith("title:"):
            title = title[6:].strip()

        # Use a fallback if Ollama returns an empty title.
        if not title:
            title = user_message[:60].strip()

        return title[:60]

    except Exception as error:
        print("[JARVIS] Title generation failed:", error)

        # Do not interrupt chat creation if title generation fails.
        return user_message[:60].strip() or "New Conversation"



# Maximum tool-call rounds for one user request.
# This is not a conversation-wide or session-wide limit.
MAX_TOOL_ROUNDS = 10


# ==========================================================
# TOOL DEFINITIONS
# ==========================================================

TOOLS = [

    # 1. List files and folders
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List files and directories inside the workspace. "
                "Use this whenever the user asks to see workspace contents."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Relative workspace directory. "
                            "Use '.' for the workspace root."
                        )
                    }
                },
                "required": ["path"]
            }
        }
    },

    # 2. Read a file
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the contents of a UTF-8 text file inside the workspace. "
                "Use this whenever the user asks to read or inspect a file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative workspace file path."
                    }
                },
                "required": ["path"]
            }
        }
    },

    # 3. Create a file
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": (
                "Create a new file inside the workspace. "
                "Do not overwrite existing files. "
                "Use this whenever the user requests file creation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative file path inside the workspace."
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write into the new file."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },

    # 4. Create a folder
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": (
                "Create a new folder inside the workspace. "
                "Use this whenever the user requests folder creation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative folder path inside the workspace."
                    }
                },
                "required": ["path"]
            }
        }
    },

    # 5. Edit a file
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Replace the complete contents of an existing text file. "
                "Call this whenever the user explicitly requests a file edit. "
                "The application will handle approval. "
                "Do not ask for approval in ordinary chat text."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative file path inside the workspace."
                    },
                    "content": {
                        "type": "string",
                        "description": "The new complete file contents."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },

    # 6. Move or rename an item
    {
        "type": "function",
        "function": {
            "name": "move_item",
            "description": (
                "Move or rename a file or folder inside the workspace. "
                "Call this whenever the user explicitly requests moving "
                "or renaming. The application will handle approval."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Current relative path of the item."
                    },
                    "destination": {
                        "type": "string",
                        "description": "New relative destination path."
                    }
                },
                "required": ["source", "destination"]
            }
        }
    },

    # 7. Copy an item
    {
        "type": "function",
        "function": {
            "name": "copy_item",
            "description": (
                "Copy a file or folder inside the workspace. "
                "Call this whenever the user explicitly requests copying. "
                "The application will handle approval."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Relative path of the original item."
                    },
                    "destination": {
                        "type": "string",
                        "description": "Relative path for the new copy."
                    }
                },
                "required": ["source", "destination"]
            }
        }
    },

    # 8. Delete an item
    {
        "type": "function",
        "function": {
            "name": "delete_item",
            "description": (
                "Delete a file or folder by moving it into workspace trash. "
                "Call this whenever the user explicitly requests deletion. "
                "The application will handle approval. "
                "Do not ask for approval in ordinary chat text."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Relative path of the file or folder to delete."
                        )
                    }
                },
                "required": ["path"]
            }
        }
    },
]


# ==========================================================
# SYSTEM INSTRUCTIONS
# ==========================================================

SYSTEM_PROMPT = """
You are Jarvis, a personal local AI assistant.

You have access to filesystem tools provided by the application.

FILESYSTEM TOOL RULES:

1. When the user asks to list files or folders, call list_files.
2. When the user asks to read a file, call read_file.
3. When the user asks to create a file, call create_file.
4. When the user asks to create a folder, call create_folder.
5. When the user asks to edit a file, call edit_file.
6. When the user asks to move or rename an item, call move_item.
7. When the user asks to copy an item, call copy_item.
8. When the user asks to delete an item, call delete_item.

APPROVAL RULES:

1. Do not ask for approval through ordinary chat text.
2. Do not ask the user to type Yes or No for a sensitive operation.
3. Call the appropriate tool when the user explicitly requests
   the operation.
4. The application handles approval for sensitive operations.
5. If a tool returns requires_approval=true, tell the user
   that an approval request has been created.
6. Never claim that an operation succeeded unless the tool
   returns a successful result.

ACCURACY RULES:

1. Never invent files, folders, paths or file contents.
2. Never claim that you read a file unless read_file returned
   its contents successfully.
3. Never claim that you created, copied, moved, edited or deleted
   something without a successful tool result.
4. When a tool returns an error, explain the actual error.
5. Use relative paths inside the workspace.
"""


# ==========================================================
# HELPER: NORMALIZE TOOL ARGUMENTS
# ==========================================================

def normalize_arguments(arguments):
    """
    Convert Ollama tool arguments into a Python dictionary.
    """

    if isinstance(arguments, str):
        arguments = json.loads(arguments)

    elif hasattr(arguments, "model_dump"):
        arguments = arguments.model_dump()

    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a dictionary.")

    return arguments


# ==========================================================
# MAIN FUNCTION
# ==========================================================

def generate_response(messages):
    """
    Send conversation messages to Ollama.

    Execute requested filesystem tools through the registry.
    Sensitive operations are intercepted by the permission manager.
    """

    # Always use the latest system instructions.
    conversation = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Preserve conversation history without old system prompts.
    for message in messages:

        if isinstance(message, dict):

            if message.get("role") == "system":
                continue

        conversation.append(message)

    # Process tool calls.
    for round_number in range(1, MAX_TOOL_ROUNDS + 1):

        print(f"\n[JARVIS] Tool round: {round_number}")

        response = ollama.chat(
            model=MODEL_NAME,
            messages=conversation,
            tools=TOOLS,
        )

        assistant_message = response.message

        tool_calls = assistant_message.tool_calls or []

        print("\n========== JARVIS RESPONSE ==========")
        print("Assistant content:", repr(assistant_message.content))
        print("Number of tool calls:", len(tool_calls))
        print("=====================================\n")

        # No tool call: return the normal assistant response.
        if not tool_calls:

            content = assistant_message.content

            if content:
                return content

            return "I couldn't generate a response. Please try again."

        # Preserve the assistant tool-call message.
        conversation.append(assistant_message)

        # Execute requested tools.
        for tool_call in tool_calls:

            tool_name = tool_call.function.name

            try:
                arguments = normalize_arguments(
                    tool_call.function.arguments
                )

            except (ValueError, TypeError, json.JSONDecodeError) as error:

                print("[JARVIS] Invalid tool arguments:", error)

                return (
                    "I couldn't process the requested operation "
                    "because the tool arguments were invalid."
                )

            print("\n========== JARVIS TOOL DEBUG ==========")
            print("Tool:", tool_name)
            print("Arguments:", arguments)

            # All tool execution goes through the registry.
            result = execute_tool(
                tool_name,
                arguments
            )

            print("Result:", result)
            print("=======================================\n")

            # Check whether user approval is required.
            if (
                isinstance(result, dict)
                and result.get("requires_approval")
            ):
                print(
                    f"[JARVIS] Approval requested for "
                    f"{tool_name}, action ID: {result.get('action_id')}"
                )

                # The approval card will communicate this to the user.
                # Do not save an extra assistant message in the conversation.
                return ""

            # Send the tool result back to Ollama.
            conversation.append({
                "role": "tool",
                "tool_name": tool_name,
                "content": json.dumps(
                    result,
                    ensure_ascii=False,
                    default=str
                )
            })

    # Safety guard for repeated tool-call rounds in one request.
    return (
        "I couldn't complete this request because too many "
        "consecutive tool-call rounds were attempted. "
        "Please split the task into smaller requests."
    )
