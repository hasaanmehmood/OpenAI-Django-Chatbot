

# Run Server:
# Step 1:
cd OpenAiChatbot

# Step 2:
run migrations

# Step 3:
python manage.py runserver

# Step 4:
Goto: http://127.0.0.1:8000/chat/




# Automated Testing:

# Run all tests
python manage.py test chatbot

# Run with detailed output (recommended first time)
python manage.py test chatbot --verbosity=2

# Run specific test class
python manage.py test chatbot.tests.ConversationModelTest

# Run specific test method
python manage.py test chatbot.tests.ChatAPITest.test_chat_post_new_conversation
```

## What the Tests Cover:

### ✅ **Model Tests** (8 tests)
- Creating conversations and messages
- Model relationships
- Data validation
- String representations

### ✅ **Service Tests** (6 tests)
- Conversation management
- Chat functionality
- Error handling
- Mocked OpenAI API calls

### ✅ **API Tests** (10 tests)
- POST requests to chat endpoint
- GET requests for conversations
- Validation and error responses
- Session management

### ✅ **Integration Tests** (2 tests)
- Complete conversation flows
- Multiple concurrent users

## Expected Output:
```
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.234s

OK
Destroying test database for alias 'default'...