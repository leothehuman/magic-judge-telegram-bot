import logging
import json
import oracle
from telegram.ext import Updater, CommandHandler, InlineQueryHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup

#logging.basicConfig(level=logging.DEBUG,
#                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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

def start_command(bot, update):
    commands = [
        '/o <card name or search strings> - oracle text for a card',
        '/q <question> - oracle text for cards mentioned in the question',
        '/cr <section> (coming soon)',
        '/ipg <section> (coming soon)',
        '/mtr <section> (coming soon)',
    ]
    update.message.reply_text('How can I help?\n{}'.format('\n'.join(commands)), quote = False)

def oracle_command(bot, update, args):
    if not args:
        update.message.reply_text('I need some clues to search for, my master!', quote=False)
        return
    words = [word.casefold() for word in args]

    nameCandidates = oracle.get_matching_names(words)

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
        for oracleName in oracle.get_oracle_names(name):
            reply.append(format_card(oracle.get_card(oracleName)))
    update.message.reply_text('\n'.join(reply), parse_mode='HTML', quote = False)

def question_command(bot, update, args):
    text = ' '.join(args).casefold()

    names = oracle.get_names_in_text(text)

    reply = []
    for name in names:
        reply.append('"' + name + '":\n' + '\n'.join([format_card(oracle.get_card(oracleName)) for oracleName in oracle.get_oracle_names(name)]))
    if reply:
        update.message.reply_text('\n\n'.join(reply), parse_mode='HTML', quote = False)

def inline_oracle(bot, update):
    query = update.inline_query.query.casefold()
    if not query:
        return

    if len(query) < 3:
        return

    words = query.split()
    nameCandidates = oracle.get_matching_names(words)
    if not nameCandidates:
        return

    results = list()
    for word in nameCandidates[:3]:
        for oracleName in oracle.get_oracle_names(word):
            card = oracle.get_card(oracleName)
            results.append(
                InlineQueryResultArticle(
                    id=card['name'],
                    title=word,
                    description=preview_card(card),
                    input_message_content=InputTextMessageContent(format_card(card), parse_mode='HTML')
                )
            )
    bot.answerInlineQuery(update.inline_query.id, results)

def callback_name(bot, update):
    message_id = update.callback_query.message.message_id
    chat_id = update.callback_query.message.chat.id
    name = update.callback_query.data

    names = oracle.get_oracle_names(name)
    if not names:
        bot.answerCallbackQuery(update.callback_query.id)
        return

    bot.editMessageText(
        chat_id = chat_id,
        message_id = message_id,
        parse_mode = 'HTML',
        text = '\n'.join([format_card(oracle.get_card(oracleName)) for oracleName in names])
    )
    bot.answerCallbackQuery(update.callback_query.id)

def text(bot, update):
    if update.message.chat.type != 'private':
        return
    text = update.message.text
    if len(text) < 30:
        oracle_command(bot, update, text.split())
    else:
        question(bot, update, text)

def comp_rules_command(bot, update, args):
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

def ask_command(bot, update, args):
    pass

def dispatcher_setup(dispatcher):
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('help', start_command))
    dispatcher.add_handler(CommandHandler('o', oracle_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('q', question_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('cr', comp_rules_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('ask', ask_command, pass_args=True))
    dispatcher.add_handler(InlineQueryHandler(inline_oracle))
    dispatcher.add_handler(CallbackQueryHandler(callback_name))
    dispatcher.add_handler(MessageHandler(Filters.text, text))

with open('config.json') as file:
    config = json.load(file)

updater = Updater(config['token'])
dispatcher_setup(updater.dispatcher)
updater.start_polling()
updater.idle()
