from openai import OpenAI
from django.conf import settings
from .models import Conversation, Message
import uuid


class ChatbotService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo"

    def get_or_create_conversation(self, session_id=None):
        if session_id:
            conversation, created = Conversation.objects.get_or_create(
                session_id=session_id
            )
        else:
            session_id = str(uuid.uuid4())
            conversation = Conversation.objects.create(session_id=session_id)

        return conversation

    def get_conversation_history(self, conversation):
        messages = conversation.messages.all()
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    def chat(self, user_message, session_id=None):
        # Get or create conversation
        conversation = self.get_or_create_conversation(session_id)

        # Save user message
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message
        )

        # Get conversation history
        messages = self.get_conversation_history(conversation)

        # Add system message if it's a new conversation
        if len(messages) == 1:
            messages.insert(0, {
                "role": "system",
                "content": "You are a helpful assistant."
            })

        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            assistant_message = response.choices[0].message.content

            # Save assistant message
            Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=assistant_message
            )

            return {
                'message': assistant_message,
                'session_id': conversation.session_id,
                'conversation_id': conversation.id
            }

        except Exception as e:
            return {
                'error': str(e),
                'session_id': conversation.session_id
            }
