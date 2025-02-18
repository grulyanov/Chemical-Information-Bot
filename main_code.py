import os

import telebot
import pubchempy as pcp

from config import TOKEN


URL = 'https://pubchem.ncbi.nlm.nih.gov/compound/'  # Основной URL сайта
WIKI_URL = 'https://en.wikipedia.org/wiki/'  # URL Википедии
DOWNLOAD_FOLDER = 'download'

# murden version
bot = telebot.TeleBot(TOKEN, parse_mode=None)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(func=lambda message: True)
def get_prop(message):
    name = message.text.strip()
    if name.isdigit():
        properties = pcp.get_properties('IsomericSMILES', name, 'cid')  # Получаем свойства по CID
        smiles = properties[0]['IsomericSMILES'] if properties else "Not available"
    else:
        properties = pcp.get_properties('IsomericSMILES', name, 'name')  # Получаем свойства по CID
        smiles = properties[0]['IsomericSMILES'] if properties else "Not available"  # ?

        return properties, smiles


def get_data(name):
    if name.isdigit():
        cid = name  # TODO: убрать зависимость try-except, like name.isdigit()
        compounds = pcp.Compound.from_cid(cid)
        pcp.download('PNG', f'{name}.png', cid, 'cid', overwrite=True)  # Загрузка изображения в png, название файла
        properties, smiles = get_prop(cid)

        with open(f'{cid}.png', 'rb') as photo:
            bot.send_photo(name.chat.id, photo, caption=f'''Here is the: {name},
                                                          Molecular formula: {compounds.molecular_formula},
                                                          IUPAC name: {compounds.iupac_name},
                                                          SMILES: {smiles},
                                                          PubChem Link: {URL + str(cid)}''')

        # print(compounds.molecular_formula, compounds.iupac_name,
        # smiles, URL + str(cid), sep='\n')
    else:
        compounds = pcp.get_compounds(name, 'name')
        properties, smiles = get_prop(name)

        if compounds:
            smile = smiles[0]
            compound = compounds[0]
            # print(compound.molecular_formula, compound.iupac_name,
            # smiles, URL + name, WIKI_URL + name, sep='\n') # Аналогично, что и выше
            pcp.download('PNG', f'{name}.png', name, 'name', overwrite=True)
            with open(f'{cid}.png', 'rb') as photo:
                bot.send_photo(name.chat.id, photo, caption=f'''Here is the: {name},
                                                          Molecular formula: {compounds.molecular_formula},
                                                          IUPAC name: {compounds.iupac_name},
                                                          SMILES: {smiles},
                                                          PubChem Link: {URL + str(cid)}''')

        else:
            print('Substance not found.')
    return compounds, properties, smiles


bot.polling()

bot = telebot.TeleBot(TOKEN, parse_mode=None)


# Telebot creation. Welcome handler
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing? Send me a compound name or CID!")


# Chem.Inf Handler
@bot.message_handler(func=lambda message: True)
def handle_input(message):
    name = message.text.strip()
    get_data(name, message)


def get_data(name, message):
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


bot.polling()
