import os

import pubchempy as pcp
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from checker import UserChecker
from config import TOKEN, URL

user_checker = UserChecker()
bot = telebot.TeleBot(TOKEN, parse_mode=None)


# Telebot creation. Welcome handler
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing? Send me a compound name or CID!\n For example, H2O or aspirin")


@bot.message_handler(commands=['settings'])
def settings(message):
    markup = InlineKeyboardMarkup()
    btn_pubchem = InlineKeyboardButton("PubChem", callback_data="toggle_pubchem")
    btn_other = InlineKeyboardButton("Other", callback_data="toggle_other")
    markup.add(btn_pubchem, btn_other)

    settings_current = user_checker.get_settings(message.chat.id)
    text = (f"Текущие настройки:\n"
            f"PubChem: {'+' if settings_current['pubchem'] else '-'}\n"
            f"Other: {'+' if settings_current['other'] else '-'}\n")
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle"))
def toggle_site(call):
    chat_id = call.message.chat.id
    settings_current = user_checker.get_settings(call.message.chat.id)
    if call.data == "toggle_pubchem":
        settings_current['pubchem'] = not settings_current['pubchem']
        bot.answer_callback_query(call.id, "PubChem изменен")
    elif call.data == "toggle_other":
        settings_current['other'] = not settings_current['other']
        bot.answer_callback_query(call.id, "Other изменен")

    settings_current = user_checker.get_settings(call.message.chat.id)
    text = (f"Текущие настройки:\n"
            f"PubChem: {'+' if settings_current['pubchem'] else '-'}\n"
            f"Other: {'+' if settings_current['other'] else '-'}\n")
    bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                          reply_markup=call.message.reply_markup)


# Chem.Inf Handler
@bot.message_handler(func=lambda message: True)
def handle_input(message):
    name = message.text.strip()

    # TODO: Добавить проверку статуса парсинга сайтов
    user_checker.get_settings(message.chat.id)

    # TODO: Парсить в зависимости от сайта
    get_data_pubchem(name, message)


def get_data_pubchem(name, message):
    try:  # checkout for CID
        if name.isdigit():
            cid = name
            compound = pcp.Compound.from_cid(cid)
        else:
            # checkout for name
            compounds = pcp.get_compounds(name, 'name')
            if compounds:
                compound = compounds[0]
                cid = compound.cid
            else:
                # if substance not found...
                bot.reply_to(message, "Substance not found. 😢")
                return
            # getting properties: smiles, photo, name, molucalar formula and etc.
        properties = pcp.get_properties('IsomericSMILES', cid, 'cid')
        smiles = properties[0]['IsomericSMILES'] if properties else "Not available"
        image_path = f'{cid}.png'
        pcp.download('PNG', image_path, cid, 'cid', overwrite=True)

        caption = (
            f"Here is the: {name}\n"
            f"Molecular formula: {compound.molecular_formula}\n"
            f"IUPAC name: {compound.iupac_name}\n"
            f"SMILES: {smiles}\n"
            f"PubChem Link: {URL + str(cid)}"
        )

        # Image opening
        with open(image_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=caption)
        os.remove(image_path)

    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}. Please try again.")


if __name__ == '__main__':
    bot.polling()
