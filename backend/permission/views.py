
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone

from permission.models import PendingAction
from permission.manager import requires_approval

from agent.tools.registry import TOOLS

from chat.models import Conversation, Message


# =====================================================
# SAVE RESULT AND RETURN TO ORIGINAL CONVERSATION
# =====================================================

def save_action_result(request, content):
    conversation_id = request.POST.get("conversation_id")

    if not conversation_id or not conversation_id.isdigit():
        return redirect("/")

    conversation = get_object_or_404(
        Conversation,
        pk=int(conversation_id)
    )

    # Save the actual result as an assistant message.
    Message.objects.create(
        conversation=conversation,
        role="assistant",
        content=content
    )

    conversation.updated_at = timezone.now()
    conversation.save(update_fields=["updated_at"])

    return redirect(f"/?conversation_id={conversation.id}")


# =====================================================
# FORMAT TOOL RESULT
# =====================================================

def format_action_result(tool_name, result):

    if result.get("success"):

        response = [
            f"Successfully completed: {tool_name}",
            "",
            result.get(
                "message",
                "Operation completed successfully."
            )
        ]

        if result.get("path"):
            response.append(f"Path: {result['path']}")

        if result.get("source"):
            response.append(f"Source: {result['source']}")

        if result.get("destination"):
            response.append(
                f"Destination: {result['destination']}"
            )

        return "\n".join(response)

    return (
        f"The operation {tool_name} failed.\n\n"
        f"Reason: {result.get('error', 'Unknown error')}"
    )


# =====================================================
# APPROVE ACTION
# =====================================================

@require_POST
def approve_action(request, action_id):

    with transaction.atomic():

        action = get_object_or_404(
            PendingAction.objects.select_for_update(),
            pk=action_id
        )

        # Prevent duplicate execution.
        if action.approved or action.rejected:

            response_text = (
                f"Action {action.tool_name} "
                "has already been resolved. "
                "It was not executed again."
            )

        else:

            # Find the requested tool.
            tool = TOOLS.get(action.tool_name)

            # Only allow tools configured to require approval.
            if not requires_approval(action.tool_name):

                result = {
                    "success": False,
                    "error": "This tool is not configured for approval."
                }

            elif tool is None:

                result = {
                    "success": False,
                    "error": "Requested tool was not found."
                }

            else:

                try:
                    # Execute the tool after approval.
                    result = tool(**action.arguments)

                except Exception as error:

                    result = {
                        "success": False,
                        "error": str(error)
                    }

            # Ensure the result is a dictionary.
            if not isinstance(result, dict):

                result = {
                    "success": False,
                    "error": str(result)
                }

            # Update approval record.
            action.approved = True
            action.executed = bool(result.get("success"))
            action.result = result
            action.resolved_at = timezone.now()

            action.save(update_fields=[
                "approved",
                "executed",
                "result",
                "resolved_at",
            ])

            # Generate the actual operation result.
            response_text = format_action_result(
                action.tool_name,
                result
            )

    # Return to the original conversation with the result.
    return save_action_result(
        request,
        response_text
    )


# =====================================================
# REJECT ACTION
# =====================================================

@require_POST
def reject_action(request, action_id):

    with transaction.atomic():

        action = get_object_or_404(
            PendingAction.objects.select_for_update(),
            pk=action_id
        )

        # Prevent resolving the same request twice.
        if action.approved or action.rejected:

            response_text = (
                f"Action {action.tool_name} "
                "has already been resolved."
            )

        else:

            # Mark action as rejected.
            action.rejected = True
            action.resolved_at = timezone.now()

            action.save(update_fields=[
                "rejected",
                "resolved_at",
            ])

            response_text = (
                f"Action rejected: {action.tool_name}.\n\n"
                "No changes were made."
            )

    # Return to the original conversation with the result.
    return save_action_result(
        request,
        response_text
    )
