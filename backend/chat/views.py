
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from agent.ollama_client import generate_response

from .models import Conversation, Message
from permission.models import PendingAction


def chat_home(request):

    # Load existing conversations for the sidebar.
    conversations = Conversation.objects.all().order_by("-updated_at")

    # Check whether an existing conversation was selected.
    conversation_id = request.GET.get("conversation_id")

    conversation = None

    if conversation_id:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id
        )

    # Handle new messages.
    if request.method == "POST":

        user_text = request.POST.get("message", "").strip()

        # Do not create or save an empty conversation.
        if not user_text:

            if conversation:
                return redirect(
                    f"/?conversation_id={conversation.id}"
                )

            return redirect("/")

        # Create a conversation only when the first
        # actual message is submitted.
        if conversation is None:

            conversation = Conversation.objects.create(
                title="New Conversation"
            )

        # Save the user's message.
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_text
        )

        # Prepare conversation history.
        history = conversation.messages.all().order_by(
            "created_at"
        )

        ollama_messages = [
            {
                "role": message.role,
                "content": message.content
            }
            for message in history
            if message.role in ["user", "assistant"]
        ]

        try:

            # Send conversation to Ollama.
            assistant_text = generate_response(
                ollama_messages
            )

            # Save only non-empty assistant responses.
            if assistant_text:

                Message.objects.create(
                    conversation=conversation,
                    role="assistant",
                    content=assistant_text
                )

        except Exception as error:

            Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=f"Error communicating with Ollama: {error}"
            )

        # Update conversation timestamp.
        conversation.updated_at = timezone.now()

        conversation.save(
            update_fields=["updated_at"]
        )

        # Return to the conversation.
        return redirect(
            f"/?conversation_id={conversation.id}"
        )

    # Load messages if an existing conversation is selected.
    if conversation:

        chat_messages = conversation.messages.all().order_by(
            "created_at"
        )

        pending_actions = PendingAction.objects.filter(
            approved=False,
            rejected=False
        ).order_by("-created_at")

    else:

        # New unsaved conversation.
        chat_messages = []
        pending_actions = []

    # Prepare template context.
    context = {
        "conversations": conversations,
        "conversation": conversation,
        "chat_messages": chat_messages,
        "pending_actions": pending_actions,
    }

    return render(
        request,
        "chat/index.html",
        context
    )


def create_conversation(request):

    # Do not create a database record yet.
    # Simply open a new blank conversation.
    return redirect("/")
