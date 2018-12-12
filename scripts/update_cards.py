from urllib.request import Request, urlopen
import json

def save(name, data):
    with open(name, 'w', encoding = 'utf8') as file:
        json.dump(data, file, ensure_ascii = False, indent = 4, sort_keys = True)

def download():
    cards = list()
    page = 1
    nonEmpty = True
    while nonEmpty:
        request_url = 'https://api.magicthegathering.io/v1/cards?page={}'.format(page)
        print('Loading page {}...'.format(page))
        try:
            req = Request(request_url, headers={'User-Agent': 'Mozilla/5.0'})
            response = json.loads(urlopen(req).read().decode("utf-8"))
            cardsPage = response['cards']
            nonEmpty = bool(cardsPage)
            if nonEmpty:
                cards.extend(cardsPage)
                page += 1
        except HTTPError:
            print ('Failed at page {}'.format(page))
    return cards

# Can load or download and save card info

# Load
#with open('data/cards.json') as file:
#    cards = json.load(file)

# Download and save for the future
cards = download()
#save('data/cards.json', cards)

languages = ['Russian']
ignore = [
    {'language': 'Russian', 'name': 'Plunder'},
    {'language': 'Russian', 'name': 'Goblin Spelunkers'},
    {'language': 'Russian', 'name': 'Raise Dead'},
]
copy = ['name', 'flavor', 'power', 'toughness', 'colors', 'printings', 'legality', 'manaCost', 'subtypes', 'text', 'layout', 'colorIdentity', 'type', 'types', 'cmc', 'loyalty', 'rulings']

names = {}
oracle = {}

for card in cards:
    if card['name'] in names:
        if not card['name'] in names[card['name']]:
            names[card['name']].append(card['name'])
    else:
        names[card['name']] = [card['name']]

    if 'foreignNames' in card:
        for translation in card['foreignNames']:
            if translation['name'] and translation['language'] in languages and not {'language': translation['language'], 'name': card['name']} in ignore:
                if translation['name'] in names:
                    if not card['name'] in names[translation['name']]:
                        print('{} version of "{}": "{}" is named as another card "{}"'.format(translation['language'], card['name'], translation['name'], names[translation['name']]))
                        names[translation['name']].append(card['name'])

                else:
                  names[translation['name']] = [card['name']]

    if not card['name'] in oracle:
        oracle[card['name']] = {k: card[k] for k in card if k in copy}

save('data/names.json', names)
save('data/oracle.json', oracle)

