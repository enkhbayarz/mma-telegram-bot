from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, \
    CallbackContext, CallbackQueryHandler, \
    InlineQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import requests
import json
import re

print('Starting up bot...')

TOKEN: Final = '6463008563:AAG5XPOwVdQv1BAWfY0aG96iEd7bZ6kG54Y'
BOT_USERNAME: Final = '@mindset_mastery_bot'

product_data = {}


# Lets us use the /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    print(chat_id)

    username = update.message.chat.username
    print(username)

    if username is None:
        return await update.message.reply_text('Таны telegram username байхгүй байна. Та өөрийн telegram username-г '
                                               'тохируулаад ашиглана уу. /start')

    response = requests.get(f'http://54.199.215.22:3000/user/username/{username}')
    print(response.text)

    if response.status_code == 200:
        data = response.text

        if 'telegramName' not in data:
            await update.message.reply_text('Та бүртгэлгүй байна.')

        if 'chatId' not in data:
            json_data = {
                "telegramName": username,
                "chatId": chat_id
            }
            response_user_add = requests.post('http://54.199.215.22:3000/user', json=json_data)
            if response.status_code == 200:
                print("POST request successful!")
                print(response_user_add.json)

        if data != 'null' and 'amount' in data:
            button_extension = InlineKeyboardButton("Сунгалт хийх", callback_data="button_extension_data")
            keyboard_extension = [[button_extension]]
            reply_markup_extension = InlineKeyboardMarkup(keyboard_extension)
            await update.message.reply_text('Энэ товчин дээр дарж сунгалтаа хийнэ үү',
                                            reply_markup=reply_markup_extension)
        else:
            await update.message.reply_text('Та бүртгэлгүй байна.')
    else:
        await update.message.reply_text("Failed to fetch data from the webhook.")


# Lets us use the /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('/start\n\n/payment\n\n/expire\n\n/help\n\n')


async def expire_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    print(chat_id)
    response = requests.get(f'http://54.199.215.22:3000/user/chatId/{chat_id}')
    print(response.text)
    if response.status_code == 200:
        if 'endDate' in response.text:
            response_data = json.loads(response.text)
            endDate = response_data["endDate"]
            await update.message.reply_text(f'Таны хугацаа дуусах өдөр: {endDate}')
        else:
            await update.message.reply_text(f'Та бүртгэлгүй байна.')
    else:
        await update.message.reply_text('Failed to fetch data from the webhook.')


# Payment
async def payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    username = update.message.chat.username
    print(username)

    if username is None:
        return await update.message.reply_text('Таны telegram username байхгүй байна. Та өөрийн telegram username-г '
                                               'тохируулаад ашиглана уу. /start')

    response = requests.get(f'http://54.199.215.22:3000/user/username/{username}')
    print(response.text)

    if response.status_code == 200:
        data = response.text
        if data != 'null' and 'amount' in data:
            button_extension = InlineKeyboardButton("Сунгалт хийх", callback_data="button_extension_data")
            keyboard_extension = [[button_extension]]
            reply_markup_extension = InlineKeyboardMarkup(keyboard_extension)
            await update.message.reply_text('Энэ товчин дээр дарж сунгалтаа хийнэ үү',
                                            reply_markup=reply_markup_extension)
        else:
            await update.message.reply_text('Та бүртгэлгүй байна.')
    else:
        await update.message.reply_text("Failed to fetch data from the webhook.")


# Handle Button Press Action
async def handle_button_press(update: Update, context):
    query = update.callback_query
    print(query)
    chat_id = query.from_user.id

    if query.data == 'button_extension_data':
        print('button_extension_data')
        response = requests.get(f'http://54.199.215.22:3000/product/chatid/{chat_id}')
        if response.status_code == 200:
            data = response.text
            product_data['product'] = response.text
            print(data)
            response_data = json.loads(data)
            inline_keyboard = []
            for index, product in enumerate(response_data):
                amount = product["amount"]
                date_type = product["dateType"]
                duration = product["duration"]
                button_text = f'{duration} {date_type}: {amount * duration}'
                print(button_text)
                button = InlineKeyboardButton(text=button_text, callback_data=f'product{index}')
                inline_keyboard.append([button])
            reply_markup_product = InlineKeyboardMarkup(inline_keyboard)
            await query.message.reply_text('Та дараах сонголтоос аль нэгийг нь сонгоно уу',
                                           reply_markup=reply_markup_product)
    elif 'product' in query.data:
        number = int(re.sub(r'\D', '', query.data))
        product = ''
        if 'product' in product_data:
            product = product_data['product']
        else:
            response = requests.get(f'http://54.199.215.22:3000/product/chatid/{chat_id}')
            if response.status_code == 200:
                product = response.text

        response_data = json.loads(product)
        print(response_data)
        product_id = response_data[number]['_id']

        print(product_id)
        print(chat_id)

        response = requests.post(
            f'http://54.199.215.22:3000/create-invoice/{chat_id}/{product_id}')

        response_data_invoice = json.loads(response.text)
        print(response_data_invoice['data']['qrLink'])
        button_qr_link = InlineKeyboardButton("QPay Link", url=response_data_invoice['data']['qrLink'])
        keyboard_qr_link = [[button_qr_link]]
        reply_markup_qr_link = InlineKeyboardMarkup(keyboard_qr_link)

        await query.message.reply_text('Энэ товчин дээр дарж төлбөрөө төлнө үү',
                                       reply_markup=reply_markup_qr_link)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get basic info of the incoming message
    message_type: str = update.message.chat.type
    text: str = update.message.text
    print(update)

    # Print a log for debugging
    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    # React to group messages only if users mention the bot directly
    if message_type == 'group':
        # Replace with your bot username
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return  # We don't want the bot respond if it's not mentioned in the group
    else:
        response: str = handle_response(text)

    # Reply normal if the message is in private
    print('Bot:', response)
    await update.message.reply_text(response)


# Log errors
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


def handle_response(text: str) -> str:
    # Create your own response logic
    processed: str = text.lower()

    if 'hello' in processed:
        return 'Hey there!'

    if 'how are you' in processed:
        return 'I\'m good!'

    if 'i love python' in processed:
        return 'Remember to subscribe!'

    return 'I don\'t understand'


# Run the program
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('payment', payment_command))
    app.add_handler(CommandHandler('expire', expire_command))
    app.add_handler(CommandHandler('help', help_command))
    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Buttons
    app.add_handler(CallbackQueryHandler(handle_button_press))

    # Log all errors
    app.add_error_handler(error)

    print('Polling...')
    # Run the bot
    app.run_polling(poll_interval=5)
