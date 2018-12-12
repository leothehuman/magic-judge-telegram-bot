import json
import io

data = {'glossary': {}, 'sections': {}}

part = None
parts = {'Glossary': 'glossary', 'Credits': 'sections', 'X-Z        300': 'sections', '1. Словарь терминов': 'glossary'}

key = None
value = None

with open('cr.txt') as file:
    for line in file:
        content = line.strip()
        if content in parts:
            part = parts[content]
            continue

        if part == 'glossary':
            if line == '\n':
                if key and value:
                    data[part][key] = value.strip()
                key, value = None, None

            elif key:
                if value:
                    value += '\n' + content
                else:
                    value = content
            else:
                key = content

        if part == 'sections':
            if line == '\n':
                if key and value:
                    data[part][key] = {'en': value.strip()}
                key, value = None, None

            elif key:
                value += '\n' + content

            else:
                if content.startswith(tuple('0123456789')):
                    key, value = content.split(' ', 1)


part = None
eng_key = None
try:
    with open('cr_ru.txt') as file:
        for line in file:
            content = line.strip()
            if content in parts:
                part = parts[content]
                continue

            if content.startswith('1. ') and 'ru' in data['sections']['1.']:
                content = content.split('1. ', 1)[1]

            if part == 'glossary':
                if line == '\n':
                    if key and eng_key and value:
                        data[part][key] = eng_key +'\n' + value
                    key, eng_key, value = None, None, None

                elif key:
                    if value:
                        value += '\n' + content
                    else:
                        value = content

                elif eng_key:
                    key = content

                else:
                    eng_key = content

            if part == 'sections':
                if line == '\n':
                    if key and value:
                        if key in data[part]:
                            if 'ru' in data[part][key]:
                                print('{:8} ! duplicate'.format(key))
                            else:
                                data[part][key]['ru'] = value
                        else:
                            print('{:8} ! unknown'.format(key))
                    key, value = None, None

                elif key:
                    value += '\n' + content

                else:
                    if content.startswith(tuple('0123456789')) and content.count(' ') > 0:
                        key, value = content.split(' ', 1)
                        if key.endswith('.') and not key[:-1].endswith(tuple('0123456789')):
                            print('{:8} extra dot'.format(key))
                            key = key[:-1]
                        if key.endswith(tuple('0123456789')):
                            print('{:8} no dot'.format(key))
                            key += '.'
                        if key.endswith(tuple('ас')):
                            print('{:8} russian letter'.format(key))
                            key = key.replace('а', 'a').replace('с', 'c')
except:
    pass

for section in data['sections']:
    if 'ru' not in data['sections'][section]:
        print('{:8} ! no ru translation'.format(section))

with io.open('data/cr.json', 'w', encoding = 'utf8') as file:
    json.dump(data, file, ensure_ascii = False, indent = 4, sort_keys = True)
