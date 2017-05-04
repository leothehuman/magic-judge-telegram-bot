import json

crData = {}
with open('data/cr.json') as file:
    crData = json.load(file)
crDataNames = crData['glossary'].keys()
crDataNumbers = crData['sections'].keys()

print('Registered {} CR glossary terms and {} CR sections'.format(len(crDataNames), len(crDataNumbers)))

def cr_search(words):

    if not words:
        return 'I need some clues to search for, my master!'
    
    words = [word.casefold() for word in words]
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
            return 'This section doesn\'t exist, my master!'

        text = '\n'.join(['<b>{}</b> {}'.format(name, crData['sections'][name][lang]) for name in results])
        if other:
            text += '\n<i>(Subsections: {}-{})</i>'.format(other[0], other[-1])
        if len(text) > 4000:
            text = '<b>{}</b> {}\n<i>(See also: {}-{})</i>'.format(results[0], crData['sections'][results[0]][lang], results[1], results[-1])

    else:
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
            return 'I searched very thoroughly, but returned empty-handed, my master!'
            

        if len(nameCandidates) > 20:
            return 'I need more specific clues, my master! This would return {} names'.format(len(nameCandidates))

        text = '\n'.join(['<b>{}</b> {}'.format(name, crData['glossary'][name]) for name in sorted(nameCandidates)])

    return text
