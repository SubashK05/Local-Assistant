from permission.manager import (
    requires_approval,
    request_approval,
)

from agent.tools.filesystem import (
    list_files,
    read_file,
    create_file,
    create_folder,
    edit_file,
    move_item,
    copy_item,
    delete_item,
)

TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "create_file": create_file,
    "create_folder": create_folder,
    "edit_file": edit_file,
    "move_item": move_item,
    "copy_item": copy_item,
    "delete_item": delete_item,
}


def execute_tool(tool_name, arguments):
    tool = TOOLS.get(tool_name)

    if tool is None:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
        }

    if requires_approval(tool_name):
        return request_approval(tool_name, arguments)

    try:
        return tool(**arguments)

    except Exception as error:
        return {
            "success": False,
            "error": str(error),
        }
