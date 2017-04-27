import logging
import json
from telegram.ext import Updater, CommandHandler, InlineQueryHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup

#logging.basicConfig(level=logging.DEBUG,
#                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

names = {}
with open('data/names.json') as file:
    names = json.load(file)
namesToSearch = names.keys()
oracleData = {}
with open('data/oracle.json') as file:
    oracleData = json.load(file)
print('Registered {} card names and {} oracle entries'.format(len(namesToSearch), len(oracleData)))

crData = {}
with open('data/cr.json') as file:
    crData = json.load(file)
crDataNames = crData['glossary'].keys()
crDataNumbers = crData['sections'].keys()

print('Registered {} CR glossary terms and {} CR sections'.format(len(crDataNames), len(crDataNumbers)))

def format_card(card):
    mana = ''
    if 'manaCost' in card:
        mana = '\t' + card['manaCost']
    text = ''
    if 'text' in card:
        text = '\n' + card['text']
    footer = ''
    if "Creature" in card['type']:
        footer = '\n{}/{}'.format(card['power'], card['toughness'])
    if "Planeswalker" in card['type'] and 'loyalty' in card:
        footer = '\n{}'.format(card['loyalty'])
    return '<b>{}</b>{}\n<i>{}</i>{}{}'.format(
        card['name'],
        mana,
        card['type'],
        text,
        footer)

def preview_card(card):
    mana = ''
    if 'manaCost' in card:
        mana = '\t' + card['manaCost']
    return '{}{}\n{}'.format(
        card['name'],
        mana,
        card['type'])

def start(bot, update):
    commands = [
        '/o <card name or search strings> - oracle text for a card',
        '/q <question> - oracle text for cards mentioned in the question',
        '/cr <section> (coming soon)',
        '/ipg <section> (coming soon)',
        '/mtr <section> (coming soon)',
    ]
    update.message.reply_text('How can I help?\n{}'.format('\n'.join(commands)), quote = False)

def search_names(words):
    nameCandidates = [name for name in namesToSearch if all(word in name.casefold() for word in words)]

    term = ' '.join(words)

    if len(words) > 1:
        goodCandidates = [name for name in nameCandidates if term in name.casefold()]
        if goodCandidates:
            nameCandidates = goodCandidates

    bestCandidates = [name for name in nameCandidates if term == name.casefold()]
    if bestCandidates:
        return bestCandidates

    return nameCandidates


def oracle(bot, update, args):
    if not args:
        update.message.reply_text('I need some clues to search for, my master!', quote=False)
        return
    words = [word.casefold() for word in args]

    nameCandidates = search_names(words)

    if not nameCandidates:
        update.message.reply_text('I searched very thoroughly, but returned empty-handed, my master!', quote=False)
        return

    if len(nameCandidates) > 20:
        update.message.reply_text('I need more specific clues, my master! This would return {} names'.format(len(nameCandidates)), quote=False)
        return

    if len(nameCandidates) > 1:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(name, callback_data=name)] for name in nameCandidates])
        update.message.reply_text('Which one?', reply_markup=reply_markup, quote=False)
        return

    reply = []
    for name in nameCandidates:
        for uniqueName in names[name]:
            reply.append(format_card(oracleData[uniqueName]))
    update.message.reply_text('\n'.join(reply), parse_mode='HTML', quote = False)

def question(bot, update, args):
    text = ' '.join(args).casefold()
    reply = []
    for name in namesToSearch:
        if name.casefold() in text:
            reply.append('"' + name + '":\n' + '\n'.join([format_card(oracleData[uniqueName]) for uniqueName in names[name]]))
    if reply:
        update.message.reply_text('\n\n'.join(reply), parse_mode='HTML', quote = False)

def inline_oracle(bot, update):
    query = update.inline_query.query.casefold()
    if not query:
        return

    if len(query) < 3:
        return

    words = query.split()
    nameCandidates = search_names(words)
    if not nameCandidates:
        return

    results = list()
    for word in nameCandidates[:3]:
        for uniqueName in names[word]:
            results.append(
                InlineQueryResultArticle(
                    id=oracleData[uniqueName]['name'],
                    title=word,
                    description=preview_card(oracleData[uniqueName]),
                    input_message_content=InputTextMessageContent(format_card(oracleData[uniqueName]), parse_mode='HTML')
                )
            )
    bot.answerInlineQuery(update.inline_query.id, results)

def callback_name(bot, update):
    message_id = update.callback_query.message.message_id
    chat_id = update.callback_query.message.chat.id
    name = update.callback_query.data
    if not name in oracleData:
        return

    bot.editMessageText(
        chat_id = chat_id,
        message_id = message_id,
        parse_mode = 'HTML',
        text = '\n'.join([format_card(oracleData[uniqueName]) for uniqueName in names[name]])
    )
    bot.answerCallbackQuery(update.callback_query.id)

def text(bot, update):
    if update.message.chat.type != 'private':
        return
    text = update.message.text
    if len(text) < 30:
        oracle(bot, update, text.split())
    else:
        question(bot, update, text)

def comp_rules(bot, update, args):
    if not args:
        update.message.reply_text('I need some clues to search for, my master!', quote=False)
        return

    words = [word.casefold() for word in args]

    if words[0][0].isdigit():
        lang = 'en'
        if len(words) > 1 and words[1] == 'ru':
            lang = 'ru'

        results = []
        other = []
        section = words[0].casefold()
        pos = len(section)
        for name in sorted([name for name in crDataNumbers if name.startswith(section)]):
            diff = name[pos:].strip('.')
            if len(diff) < 2 and (len(diff) == 0 or diff.isalpha()):
                results.append(name)
            elif not diff[-1:].isalpha():
                other.append(name)

        if not results:
            update.message.reply_text('This section doesn\'t exist, my master!', quote=False)
            return

        text = '\n'.join(['<b>{}</b> {}'.format(name, crData['sections'][name][lang]) for name in results])
        if other:
            text += '\n<i>(Subsections: {}-{})</i>'.format(other[0], other[-1])
        if len(text) > 4000:
            text = '<b>{}</b> {}\n<i>(See also: {}-{})</i>'.format(results[0], crData['sections'][results[0]][lang], results[1], results[-1])
        update.message.reply_text(text, parse_mode='HTML', quote = False)
        return

    nameCandidates = [name for name in crDataNames if all(word in name.casefold() for word in words)]

    term = ' '.join(words)
    if len(words) > 1:
        goodCandidates = [name for name in nameCandidates if term in name.casefold()]
        if goodCandidates:
            nameCandidates = goodCandidates

    bestCandidates = [name for name in nameCandidates if name.casefold().startswith(term)]
    if bestCandidates:
        nameCandidates = bestCandidates
        excellentCandidate = [name for name in nameCandidates if name.casefold() == term]
        if excellentCandidate:
            nameCandidates = excellentCandidate

    if not nameCandidates:
        update.message.reply_text('I searched very thoroughly, but returned empty-handed, my master!', quote=False)
        return

    if len(nameCandidates) > 20:
        update.message.reply_text('I need more specific clues, my master! This would return {} names'.format(len(nameCandidates)), quote=False)
        return

    text = '\n'.join(['<b>{}</b> {}'.format(name, crData['glossary'][name]) for name in sorted(nameCandidates)])
    update.message.reply_text(text, parse_mode='HTML', quote = False)

def dispatcher_setup(dispatcher):
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', start))
    dispatcher.add_handler(CommandHandler('o', oracle, pass_args=True))
    dispatcher.add_handler(CommandHandler('q', question, pass_args=True))
    dispatcher.add_handler(CommandHandler('cr', comp_rules, pass_args=True))
    dispatcher.add_handler(InlineQueryHandler(inline_oracle))
    dispatcher.add_handler(CallbackQueryHandler(callback_name))
    dispatcher.add_handler(MessageHandler(Filters.text, text))

with open('token') as file:
    token = file.read().strip()
updater = Updater(token)
dispatcher_setup(updater.dispatcher)
updater.start_polling()
updater.idle()
