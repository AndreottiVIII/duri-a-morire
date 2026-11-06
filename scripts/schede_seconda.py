# -*- coding: utf-8 -*-
"""Chi ha una scheda anche su Seconda Repubblica Tracker, e a quale indirizzo.

Legge le pagine gia' costruite del sito gemello (cartella accanto a questa,
seconda-repubblica-tracker/pubblica/onorevole/) e il suo elenco. La stessa
persona nei due siti la lega il codice Wikidata o, dove di la' manca (alcuni
senatori, Andreotti compreso, hanno solo il codice del Senato), la voce di
Wikipedia: il nome da solo no. Scrive data/seconda_repubblica.json,
{codice Wikidata o indirizzo Wikipedia: indirizzo della scheda}.
Le legislature 1994-2013 sono chiuse, quindi basta rifarlo di rado.

    python scripts/schede_seconda.py
"""
import glob
import json
import os
import re
import urllib.parse

QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEMELLO = os.path.join(QUI, '..', 'seconda-repubblica-tracker')
USCITA = os.path.join(QUI, 'data', 'seconda_repubblica.json')
SITO = 'https://secondarepubblica.it'


def main():
    # nome e nascita -> voce di Wikipedia, dall'elenco del sito gemello
    voci = {}
    for p in json.load(open(os.path.join(GEMELLO, 'data', 'elenco.json'), encoding='utf-8'))['persone']:
        if p.get('wikipedia'):
            voci.setdefault((p['nome'], p.get('nascita') or ''), set()).add(
                urllib.parse.unquote(p['wikipedia']))

    schede, pagine = {}, 0
    for f in sorted(glob.glob(os.path.join(GEMELLO, 'pubblica', 'onorevole', '*', 'index.html'))):
        testo = open(f, encoding='utf-8').read()
        c = re.search(r'<link rel="canonical" href="%s(/onorevole/[^"]+/)"' % re.escape(SITO), testo)
        m = re.search(r'"mainEntity":(\{[^}]*\})', testo)
        if not (c and m):
            continue
        pagine += 1
        chi = json.loads(m.group(1))
        chiavi = [x.rsplit('/', 1)[1] for x in chi.get('sameAs', []) if '/wikidata.org/wiki/Q' in x]
        w = voci.get((chi['name'], chi.get('birthDate', '')), set())
        if len(w) == 1:
            chiavi.append(w.pop())
        for k in chiavi:
            if k in schede and schede[k] != c.group(1):
                raise SystemExit('Due schede per %s' % k)
            schede[k] = c.group(1)
    if pagine < 2000:
        raise SystemExit('Solo %d schede: la cartella del sito gemello non sembra completa.' % pagine)
    json.dump(schede, open(USCITA, 'w', encoding='utf-8'), sort_keys=True, indent=0)
    print('Schede lette: %d, persone riconoscibili: %d' % (pagine, len(set(schede.values()))))


if __name__ == '__main__':
    main()
