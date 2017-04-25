import logging
import json
from telegram.ext import Updater, CommandHandler, InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent

#logging.basicConfig(level=logging.DEBUG,
#                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

names = {}
with open('data/names.json') as file:
    names = json.load(file)
namesToSearch = names.keys()
oracleData = {}
with open('data/oracle.json') as file:
    oracleData = json.load(file)
print('Registered {} card names and {} oracle entries'.format(len(names), len(oracleData)))

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
    return '{}{}\n{}{}{}'.format(
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

def format_names(names):
    return '\n'.join(sorted(names))

def start(bot, update):
    commands = [
        '/o <card name or search strings> - oracle text for a card',
        '/q <question> - oracle text for cards mentioned in the question',
        '/cr <section> (coming soon)',
        '/ipg <section> (coming soon)',
        '/mtr <section> (coming soon)',
    ]
    update.message.reply_text('How can I help?\n{}'.format('\n'.join(commands)))

def search_names(words):
    nameCandidates = [name for name in namesToSearch if all(word in name.casefold() for word in words)]

    if len(words) > 1:
        term = ' '.join(words)
        goodCandidates = [name for name in nameCandidates if term in name]
        if goodCandidates:
            return goodCandidates
    return nameCandidates


def oracle(bot, update, args):
    if not args:
        update.message.reply_text('I need some clues to search for, my master!')
        return
    words = [word.casefold() for word in args]

    nameCandidates = search_names(words)

    if not nameCandidates:
        update.message.reply_text('I searched very thoroughly, but returned empty-handed, my master!')
        return

    if len(nameCandidates) > 20:
        update.message.reply_text('I need more specific clues, my master! This would return {} names'.format(len(nameCandidates)))
        return

    if len(nameCandidates) > 1:
        update.message.reply_text(format_names(nameCandidates))
        return

    reply = []
    for name in nameCandidates:
        for uniqueName in names[name]:
            reply.append(format_card(oracleData[uniqueName]))
    update.message.reply_text('\n'.join(reply))

def question(bot, update, args):
    words = args
    text = ' '.join(words).casefold()
    reply = []
    for name in namesToSearch:
        if name.casefold() in text:
            reply.append('"' + name + '":')
            for uniqueName in names[name]:
                reply.append(format_card(oracleData[uniqueName]))
    if reply:
        update.message.reply_text('\n'.join(reply))

def inline_oracle(bot, update):
    print("Inline oracle")
    query = update.inline_query.query.casefold()
    if not query:
        return

    print(query)

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
                    input_message_content=InputTextMessageContent(format_card(oracleData[uniqueName]))
                )
            )
    print(results)
    bot.answerInlineQuery(update.inline_query.id, results)

def dispatcher_setup(dispatcher):
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', start))
    dispatcher.add_handler(CommandHandler('o', oracle, pass_args=True))
    dispatcher.add_handler(CommandHandler('q', question, pass_args=True))
    dispatcher.add_handler(InlineQueryHandler(inline_oracle))

with open('token') as file:
    token = file.read().strip()
updater = Updater(token)
dispatcher_setup(updater.dispatcher)
updater.start_polling()
updater.idle()
