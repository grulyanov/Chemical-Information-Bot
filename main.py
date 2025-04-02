import os
import pandas as pd

import pubchempy as pcp
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from checker import UserChecker
from config import TOKEN, URL

data = 'data'
user_checker = UserChecker()
bot = telebot.TeleBot(TOKEN, parse_mode=None)

#Dataset reading

df = pd.read_csv('iupac_high-confidence_v2_2.csv')


# Telebot creation. Welcome handler
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing? Send me a compound name or CID!\n For example, 2244 or aspirin")


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
        sdf_path = f'{cid}.sdf'
        pcp.download('PNG', image_path, cid, 'cid', overwrite=True)
        pcp.download('SDF', sdf_path, cid, 'cid', overwrite= True)

        caption = (
            f"Molecular formula: {compound.molecular_formula}\n"
            f'Molecular weight: {compound.molecular_weight}\n'
            f'InChI: {compound.inchi}\n'
            f"IUPAC name: {compound.iupac_name}\n"
            f"SMILES: {smiles}\n"
            f"PubChem Link: {URL + str(cid)}\n"
        )

        # Image opening
        with open(image_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=caption)
        os.remove(image_path)
        with open(sdf_path, 'rb') as molfile:
           bot.send_document(message.chat.id, molfile)
        os.remove(sdf_path)  # TODO: замена на временный файл (убрать os)
        if compound.inchi in df['InChI'].values:
            filt_df = df[df['InChI'] == compound.inchi][['pka_type', 'pka_value', 'T', 'remarks']]
            file_path = f'{name}_pKa_values.xlsx'
            filt_df.to_excel(file_path)
            marker = ''
            with open(file_path, 'rb') as file:
                bot.send_document(message.chat.id, file)
            os.remove(file_path)
        else:
            marker = 'There is no dissociation constant data for such substance'



    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}. Please try again.")


if __name__ == '__main__':
    bot.polling()
