from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import Conversation, Message
from .services import ChatbotService
import uuid


# ============================================
# MODEL TESTS
# ============================================

class ConversationModelTest(TestCase):
    """Test cases for Conversation model"""

    def setUp(self):
        """Set up test data before each test"""
        self.session_id = str(uuid.uuid4())

    def test_create_conversation(self):
        """Test creating a conversation"""
        conversation = Conversation.objects.create(session_id=self.session_id)
        self.assertEqual(conversation.session_id, self.session_id)
        self.assertIsNotNone(conversation.created_at)
        self.assertIsNotNone(conversation.updated_at)
        print("✓ Conversation created successfully")

    def test_conversation_string_representation(self):
        """Test conversation __str__ method"""
        conversation = Conversation.objects.create(session_id=self.session_id)
        expected = f"Conversation {self.session_id}"
        self.assertEqual(str(conversation), expected)
        print(f"✓ Conversation string representation correct: {str(conversation)}")

    def test_conversation_unique_session_id(self):
        """Test that session_id must be unique"""
        Conversation.objects.create(session_id=self.session_id)
        with self.assertRaises(Exception):
            Conversation.objects.create(session_id=self.session_id)
        print("✓ Session ID uniqueness enforced")


class MessageModelTest(TestCase):
    """Test cases for Message model"""

    def setUp(self):
        """Set up test data before each test"""
        self.conversation = Conversation.objects.create(
            session_id=str(uuid.uuid4())
        )

    def test_create_user_message(self):
        """Test creating a user message"""
        message = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Hello, chatbot!'
        )
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.content, 'Hello, chatbot!')
        self.assertEqual(message.conversation, self.conversation)
        print("✓ User message created successfully")

    def test_create_assistant_message(self):
        """Test creating an assistant message"""
        message = Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Hello! How can I help you?'
        )
        self.assertEqual(message.role, 'assistant')
        print("✓ Assistant message created successfully")

    def test_message_ordering(self):
        """Test that messages are ordered by timestamp"""
        msg1 = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='First message'
        )
        msg2 = Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Second message'
        )
        messages = Message.objects.all()
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)
        print("✓ Messages ordered correctly by timestamp")

    def test_message_string_representation(self):
        """Test message __str__ method"""
        message = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='This is a test message'
        )
        self.assertEqual(str(message), 'user: This is a test message')
        print(f"✓ Message string representation: {str(message)}")

    def test_related_messages(self):
        """Test accessing messages through conversation"""
        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Message 1'
        )
        Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Message 2'
        )
        message_count = self.conversation.messages.count()
        self.assertEqual(message_count, 2)
        print(f"✓ Conversation has {message_count} messages")


# ============================================
# SERVICE TESTS
# ============================================

class ChatbotServiceTest(TestCase):
    """Test cases for ChatbotService"""

    def setUp(self):
        """Set up test data before each test"""
        self.service = ChatbotService()
        self.session_id = str(uuid.uuid4())

    def test_get_or_create_conversation_new(self):
        """Test creating a new conversation"""
        conversation = self.service.get_or_create_conversation()
        self.assertIsNotNone(conversation)
        self.assertIsNotNone(conversation.session_id)
        print(f"✓ New conversation created with session_id: {conversation.session_id}")

    def test_get_or_create_conversation_existing(self):
        """Test getting an existing conversation"""
        conversation1 = self.service.get_or_create_conversation(self.session_id)
        conversation2 = self.service.get_or_create_conversation(self.session_id)
        self.assertEqual(conversation1.id, conversation2.id)
        print("✓ Retrieved existing conversation successfully")

    def test_get_conversation_history_empty(self):
        """Test getting history from empty conversation"""
        conversation = Conversation.objects.create(session_id=self.session_id)
        history = self.service.get_conversation_history(conversation)
        self.assertEqual(len(history), 0)
        print("✓ Empty conversation returns empty history")

    def test_get_conversation_history_with_messages(self):
        """Test getting conversation history with messages"""
        conversation = Conversation.objects.create(session_id=self.session_id)
        Message.objects.create(
            conversation=conversation,
            role='user',
            content='Hello'
        )
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content='Hi there!'
        )
        history = self.service.get_conversation_history(conversation)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['role'], 'user')
        self.assertEqual(history[1]['role'], 'assistant')
        print(f"✓ Retrieved {len(history)} messages from history")

    @patch('chatbot.services.OpenAI')
    def test_chat_success(self, mock_openai):
        """Test successful chat interaction"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! How can I help?"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = ChatbotService()
        result = service.chat("Hello", self.session_id)

        self.assertIn('message', result)
        self.assertIn('session_id', result)
        self.assertEqual(result['message'], "Hello! How can I help?")
        print("✓ Chat interaction successful")

    @patch('chatbot.services.OpenAI')
    def test_chat_error_handling(self, mock_openai):
        """Test chat error handling"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        service = ChatbotService()
        result = service.chat("Hello", self.session_id)

        self.assertIn('error', result)
        self.assertIn('API Error', result['error'])
        print("✓ Error handling works correctly")


# ============================================
# API TESTS
# ============================================

class ChatAPITest(APITestCase):
    """Test cases for Chat API endpoints"""

    def setUp(self):
        """Set up test client and URLs"""
        self.client = APIClient()
        self.chat_url = '/api/chat/'
        self.session_id = str(uuid.uuid4())

    @patch('chatbot.services.ChatbotService.chat')
    def test_chat_post_new_conversation(self, mock_chat):
        """Test POST to chat endpoint with new conversation"""
        mock_chat.return_value = {
            'message': 'Hello! How can I help?',
            'session_id': self.session_id,
            'conversation_id': 1
        }

        data = {'message': 'Hello'}
        response = self.client.post(self.chat_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('session_id', response.data)
        print(f"✓ New chat conversation: {response.data['session_id']}")

    @patch('chatbot.services.ChatbotService.chat')
    def test_chat_post_existing_conversation(self, mock_chat):
        """Test POST to chat endpoint with existing conversation"""
        mock_chat.return_value = {
            'message': 'Sure, I can help with that!',
            'session_id': self.session_id,
            'conversation_id': 1
        }

        data = {
            'message': 'Can you help me?',
            'session_id': self.session_id
        }
        response = self.client.post(self.chat_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['session_id'], self.session_id)
        print("✓ Continued existing conversation")

    def test_chat_post_missing_message(self):
        """Test POST without message field"""
        data = {}
        response = self.client.post(self.chat_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
        print("✓ Missing message validation works")

    def test_chat_post_empty_message(self):
        """Test POST with empty message"""
        data = {'message': ''}
        response = self.client.post(self.chat_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print("✓ Empty message validation works")

    @patch('chatbot.services.ChatbotService.chat')
    def test_chat_post_api_error(self, mock_chat):
        """Test POST when API returns error"""
        mock_chat.return_value = {
            'error': 'API connection failed',
            'session_id': self.session_id
        }

        data = {'message': 'Hello'}
        response = self.client.post(self.chat_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        print("✓ API error handled correctly")


class ConversationAPITest(APITestCase):
    """Test cases for Conversation API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.session_id = str(uuid.uuid4())

        # Create test conversation with messages
        self.conversation = Conversation.objects.create(
            session_id=self.session_id
        )
        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Hello'
        )
        Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Hi there!'
        )

    def test_get_conversation_by_session_id(self):
        """Test retrieving conversation by session_id"""
        url = f'/api/conversations/{self.session_id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['session_id'], self.session_id)
        self.assertEqual(len(response.data['messages']), 2)
        print(f"✓ Retrieved conversation with {len(response.data['messages'])} messages")

    def test_get_nonexistent_conversation(self):
        """Test retrieving non-existent conversation"""
        fake_session_id = str(uuid.uuid4())
        url = f'/api/conversations/{fake_session_id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("✓ Non-existent conversation returns 404")

    def test_list_conversations(self):
        """Test listing all conversations"""
        url = '/api/conversations/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        print(f"✓ Listed {len(response.data)} conversations")

    def test_conversation_messages_order(self):
        """Test that messages are returned in correct order"""
        url = f'/api/conversations/{self.session_id}/'
        response = self.client.get(url)

        messages = response.data['messages']
        self.assertEqual(messages[0]['role'], 'user')
        self.assertEqual(messages[1]['role'], 'assistant')
        print("✓ Messages returned in correct order")


# ============================================
# INTEGRATION TESTS
# ============================================

class IntegrationTest(APITestCase):
    """Integration tests for complete conversation flow"""

    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
        self.chat_url = '/api/chat/'

    @patch('chatbot.services.OpenAI')
    def test_full_conversation_flow(self, mock_openai):
        """Test a complete conversation flow"""
        # Mock OpenAI responses
        mock_responses = [
            "Hello! How can I help you today?",
            "Sure! Python is a high-level programming language.",
            "You're welcome! Feel free to ask more questions."
        ]

        mock_client = MagicMock()

        def mock_create(*args, **kwargs):
            response = MagicMock()
            response.choices = [MagicMock()]
            response.choices[0].message.content = mock_responses.pop(0)
            return response

        mock_client.chat.completions.create.side_effect = mock_create
        mock_openai.return_value = mock_client

        # First message
        response1 = self.client.post(
            self.chat_url,
            {'message': 'Hello'},
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        session_id = response1.data['session_id']
        print(f"✓ Message 1: Started conversation {session_id}")

        # Second message
        response2 = self.client.post(
            self.chat_url,
            {'message': 'What is Python?', 'session_id': session_id},
            format='json'
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['session_id'], session_id)
        print("✓ Message 2: Continued conversation")

        # Third message
        response3 = self.client.post(
            self.chat_url,
            {'message': 'Thank you!', 'session_id': session_id},
            format='json'
        )
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        print("✓ Message 3: Completed conversation")

        # Verify conversation history
        conversation = Conversation.objects.get(session_id=session_id)
        message_count = conversation.messages.count()
        self.assertEqual(message_count, 6)  # 3 user + 3 assistant
        print(f"✓ Total messages in conversation: {message_count}")

    @patch('chatbot.services.OpenAI')
    def test_multiple_concurrent_conversations(self, mock_openai):
        """Test handling multiple conversations simultaneously"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Create two separate conversations
        response1 = self.client.post(
            self.chat_url,
            {'message': 'Hello from user 1'},
            format='json'
        )
        session_id_1 = response1.data['session_id']

        response2 = self.client.post(
            self.chat_url,
            {'message': 'Hello from user 2'},
            format='json'
        )
        session_id_2 = response2.data['session_id']

        # Verify they're different conversations
        self.assertNotEqual(session_id_1, session_id_2)
        print(f"✓ Created 2 concurrent conversations")

        # Verify both conversations exist
        self.assertTrue(Conversation.objects.filter(session_id=session_id_1).exists())
        self.assertTrue(Conversation.objects.filter(session_id=session_id_2).exists())
        print("✓ Both conversations saved independently")
