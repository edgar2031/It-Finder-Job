import asyncio
from telegram.constants import ChatAction
from telegram.ext import CallbackContext


async def send_typing_action(context: CallbackContext, chat_id: int, duration: float = 1.0):
    """
    Send typing action and wait for specified duration.
    
    Args:
        context: The callback context from the handler
        chat_id: The chat ID to send typing action to
        duration: How long to show typing indicator (in seconds)
    """
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    if duration > 0:
        await asyncio.sleep(duration)


async def with_typing_indicator(func, context: CallbackContext, chat_id: int, *args, **kwargs):
    """
    Execute a function while showing typing indicator.
    
    Args:
        func: The function to execute
        context: The callback context
        chat_id: The chat ID to send typing action to
        *args, **kwargs: Arguments to pass to the function
    """
    # Send typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    
    # Execute the function
    if asyncio.iscoroutinefunction(func):
        result = await func(*args, **kwargs)
    else:
        result = func(*args, **kwargs)
    
    return result
