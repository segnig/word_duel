from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ChosenInlineResultHandler,
    CommandHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

from word_duel.handlers.callbacks import button_handler
from word_duel.handlers.chat import handle_group_text
from word_duel.handlers.commands import cancel, guess, newduel, start, word
from word_duel.handlers.dm import handle_private_message
from word_duel.handlers.inline import chosen_inline_result, inline_query


def register_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newduel", newduel))
    app.add_handler(CommandHandler("word", word))
    app.add_handler(CommandHandler("guess", guess))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(ChosenInlineResultHandler(chosen_inline_result))
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
            handle_private_message,
        )
    )
    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
            handle_group_text,
        )
    )
