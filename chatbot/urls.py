from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatView, ConversationViewSet, chatbot_ui,chat_ui

router = DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("chat/", chatbot_ui, name="chatbot-ui"),
    path("studio/", chat_ui, name="chat-ui"),
    path("api/chat/", ChatView.as_view(), name="chat-api"),
    path("api/", include(router.urls)),
]
