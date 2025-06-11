"""Microsoft Teams Bot Framework integration."""
import logging
from typing import List
from botbuilder.core import (
    ActivityHandler, 
    TurnContext, 
    MessageFactory,
    CardFactory
)
from botbuilder.schema import (
    Activity, 
    ActivityTypes, 
    ChannelAccount,
    CardAction,
    ActionTypes,
    SuggestedActions
)
from src.services.openai_service import openai_service
from src.config import config

logger = logging.getLogger(__name__)


class TeamsBot(ActivityHandler):
    """
    Teams bot that handles conversations using Azure OpenAI.
    """
    
    def __init__(self):
        """Initialize the Teams bot."""
        super().__init__()
        
    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handle message activities from users.
        
        Args:
            turn_context: The turn context for the current conversation turn
        """
        try:
            # Get user information
            user = turn_context.activity.from_property
            user_name = user.name if user else "Unknown User"
            user_id = user.id if user else "unknown"
            
            # Get conversation ID
            conversation_id = turn_context.activity.conversation.id
            
            # Get the user's message
            user_message = turn_context.activity.text.strip()
            
            logger.info(f"Received message from {user_name} ({user_id}): {user_message}")
            
            # Handle special commands
            if user_message.lower() in ['/help', 'help']:
                await self._send_help_message(turn_context)
                return
            
            if user_message.lower() in ['/clear', 'clear']:
                openai_service.clear_conversation(conversation_id)
                await turn_context.send_activity(
                    MessageFactory.text("✅ Conversation history cleared!")
                )
                return
            
            if user_message.lower() in ['/summary', 'summary']:
                await self._send_conversation_summary(turn_context, conversation_id)
                return
            
            # Show typing indicator
            await self._send_typing_activity(turn_context)
            
            # Get response from Azure OpenAI
            ai_response = await openai_service.get_chat_response(
                message=user_message,
                conversation_id=conversation_id,
                user_name=user_name
            )
            
            # Send the response
            await turn_context.send_activity(MessageFactory.text(ai_response))
            
            logger.info(f"Sent AI response to {user_name}")
            
        except Exception as e:
            logger.error(f"Error handling message activity: {e}")
            await turn_context.send_activity(
                MessageFactory.text(
                    "I'm sorry, I encountered an error while processing your message. "
                    "Please try again or contact support if the issue persists."
                )
            )
    
    async def on_teams_members_added_activity(
        self, 
        members_added: List[ChannelAccount], 
        turn_context: TurnContext
    ):
        """
        Handle when members are added to the Teams conversation.
        
        Args:
            members_added: List of members that were added
            turn_context: The turn context for the current conversation turn
        """
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                # Send welcome message to new members
                await self._send_welcome_message(turn_context, member.name)
    
    async def on_members_added_activity(
        self, 
        members_added: List[ChannelAccount], 
        turn_context: TurnContext
    ):
        """
        Handle when members are added to the conversation.
        
        Args:
            members_added: List of members that were added
            turn_context: The turn context for the current conversation turn
        """
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                # Send welcome message to new members
                await self._send_welcome_message(turn_context, member.name)
    
    async def _send_welcome_message(self, turn_context: TurnContext, user_name: str = None):
        """
        Send a welcome message to new users.
        
        Args:
            turn_context: The turn context for the current conversation turn
            user_name: Name of the user to welcome
        """
        welcome_text = f"👋 Hello{' ' + user_name if user_name else ''}! I'm your AI assistant."
        
        welcome_card = {
            "type": "AdaptiveCard",
            "version": "1.0",
            "body": [
                {
                    "type": "TextBlock",
                    "text": welcome_text,
                    "size": "Medium",
                    "weight": "Bolder"
                },
                {
                    "type": "TextBlock",
                    "text": (
                        "I can help you with various tasks, answer questions, and have conversations. "
                        "Just type your message and I'll respond!"
                    ),
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": "**Available Commands:**",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": "• `/help` - Show this help message\n• `/clear` - Clear conversation history\n• `/summary` - Show conversation summary",
                    "wrap": True
                }
            ]
        }
        
        # Create adaptive card attachment
        card_attachment = CardFactory.adaptive_card(welcome_card)
        
        # Send the welcome message with card
        await turn_context.send_activity(
            MessageFactory.attachment(card_attachment)
        )
        
        # Also send quick action buttons
        suggested_actions = SuggestedActions(
            actions=[
                CardAction(
                    title="Get Help",
                    type=ActionTypes.im_back,
                    value="/help"
                ),
                CardAction(
                    title="Start Conversation",
                    type=ActionTypes.im_back,
                    value="Hello! How can you help me today?"
                )
            ]
        )
        
        message = MessageFactory.text("What would you like to do?")
        message.suggested_actions = suggested_actions
        
        await turn_context.send_activity(message)
    
    async def _send_help_message(self, turn_context: TurnContext):
        """
        Send help information to the user.
        
        Args:
            turn_context: The turn context for the current conversation turn
        """
        help_card = {
            "type": "AdaptiveCard",
            "version": "1.0",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "🤖 AI Assistant Help",
                    "size": "Large",
                    "weight": "Bolder"
                },
                {
                    "type": "TextBlock",
                    "text": "I'm an AI-powered chatbot that can help you with various tasks:",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": "**What I can do:**",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": (
                        "• Answer questions on a wide range of topics\n"
                        "• Help with writing and editing\n"
                        "• Provide explanations and tutorials\n"
                        "• Assist with problem-solving\n"
                        "• Have natural conversations"
                    ),
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": "**Available Commands:**",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": (
                        "• `/help` - Show this help message\n"
                        "• `/clear` - Clear conversation history\n"
                        "• `/summary` - Show conversation summary"
                    ),
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": "**Tips:**",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": (
                        "• Be specific with your questions for better responses\n"
                        "• I remember our conversation context\n"
                        "• Feel free to ask follow-up questions"
                    ),
                    "wrap": True
                }
            ]
        }
        
        card_attachment = CardFactory.adaptive_card(help_card)
        await turn_context.send_activity(MessageFactory.attachment(card_attachment))
    
    async def _send_conversation_summary(self, turn_context: TurnContext, conversation_id: str):
        """
        Send conversation summary to the user.
        
        Args:
            turn_context: The turn context for the current conversation turn
            conversation_id: The conversation ID to summarize
        """
        summary = openai_service.get_conversation_summary(conversation_id)
        
        if summary["message_count"] == 0:
            await turn_context.send_activity(
                MessageFactory.text("📊 No conversation history found.")
            )
            return
        
        summary_card = {
            "type": "AdaptiveCard",
            "version": "1.0",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "📊 Conversation Summary",
                    "size": "Large",
                    "weight": "Bolder"
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {
                            "title": "Total Messages:",
                            "value": str(summary["message_count"])
                        },
                        {
                            "title": "Your Messages:",
                            "value": str(summary["user_messages"])
                        },
                        {
                            "title": "AI Responses:",
                            "value": str(summary["assistant_messages"])
                        },
                        {
                            "title": "Participants:",
                            "value": ", ".join(summary["participants"]) if summary["participants"] else "Unknown"
                        }
                    ]
                }
            ]
        }
        
        card_attachment = CardFactory.adaptive_card(summary_card)
        await turn_context.send_activity(MessageFactory.attachment(card_attachment))
    
    async def _send_typing_activity(self, turn_context: TurnContext):
        """
        Send a typing indicator to show the bot is processing.
        
        Args:
            turn_context: The turn context for the current conversation turn
        """
        typing_activity = Activity(
            type=ActivityTypes.typing,
            from_property=turn_context.activity.recipient,
            recipient=turn_context.activity.from_property,
            conversation=turn_context.activity.conversation
        )
        
        await turn_context.send_activity(typing_activity)