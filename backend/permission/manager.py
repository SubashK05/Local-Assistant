from permission.models import PendingAction


SENSITIVE_TOOLS = {
    "edit_file",
    "delete_item",
    "move_item",
    "copy_item",
}


def requires_approval(tool_name):
    return tool_name in SENSITIVE_TOOLS


def request_approval(tool_name, arguments):
    action = PendingAction.objects.create(
        tool_name=tool_name,
        arguments=arguments,
    )

    return {
        "success": False,
        "requires_approval": True,
        "action_id": action.id,
        "message": (
            f"Approval required before executing {tool_name}."
        ),
    }
