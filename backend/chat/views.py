
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from agent.ollama_client import (
    generate_response,
    generate_conversation_title,
)

from .models import Conversation, Message
from permission.models import PendingAction


def chat_home(request):

    conversations = Conversation.objects.all().order_by(
        "-updated_at"
    )

    conversation_id = request.GET.get("conversation_id")
    conversation = None

    # Load an existing conversation if selected.
    if conversation_id:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id
        )

    if request.method == "POST":

        user_text = request.POST.get("message", "").strip()

        # Ignore empty submissions.
        if not user_text:

            if conversation:
                return redirect(
                    f"/?conversation_id={conversation.id}"
                )

            return redirect("/")

        # Create a database record only after receiving
        # the first non-empty message.
        if conversation is None:
            conversation = Conversation.objects.create(
                title="New Conversation"
            )

        # Check whether this is the first message.
        is_first_message = not conversation.messages.exists()

        # Save the user's message.
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_text
        )

        # Generate a meaningful title only once.
        if is_first_message:

            conversation.title = generate_conversation_title(
                user_text
            )

            conversation.save(update_fields=["title"])

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

            # Generate Jarvis's response.
            assistant_text = generate_response(
                ollama_messages
            )

            # Do not save empty approval responses.
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

        return redirect(
            f"/?conversation_id={conversation.id}"
        )

    # Load chat history.
    if conversation:

        chat_messages = conversation.messages.all().order_by(
            "created_at"
        )

        pending_actions = PendingAction.objects.filter(
            approved=False,
            rejected=False
        ).order_by("-created_at")

    else:

        # Display a blank unsaved conversation.
        chat_messages = []
        pending_actions = []

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

    # Display a blank conversation.
    # Do not create a database record yet.
    return redirect("/")
