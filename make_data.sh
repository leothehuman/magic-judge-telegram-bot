#!/bin/sh
curl http://media.wizards.com/2018/downloads/MagicCompRules%2020181005.txt | iconv -f cp1251 -t utf8 > cr.txt
mkdir -p data
python3 scripts/update_cards.py
python3 scripts/update_cr.py
