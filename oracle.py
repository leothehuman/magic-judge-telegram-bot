import json

with open('data/names.json') as file:
    names = json.load(file)
namesToSearch = names.keys()
with open('data/oracle.json') as file:
    oracleData = json.load(file)
print('Registered {} card names and {} oracle entries'.format(len(namesToSearch), len(oracleData)))

def get_matching_names(words):
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

def get_card(name):
    if name in oracleData:
        return oracleData[name]
    else:
        return None

def get_oracle_names(name):
    if name in names:
        return names[name]
    else:
        return None

def get_names_in_text(text):
    result = []
    for name in namesToSearch:
        if name.casefold() in text:
            result.append(name)
    return result
