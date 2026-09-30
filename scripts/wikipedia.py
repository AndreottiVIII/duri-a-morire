# -*- coding: utf-8 -*-
"""Quarta fonte: le voci di Wikipedia in italiano.

Wikidata e i registri di Camera e Senato arrivano tardi, a volte di settimane:
Pietro Soddu e' morto il 16 settembre 2026 e la sua voce lo diceva il giorno
stesso, mentre Wikidata e la Camera due settimane dopo lo davano ancora vivo.
Lo stesso per Imma Barbarossa, morta il 26. Chi aggiorna Wikipedia legge il
giornale del mattino; chi aggiorna Wikidata, quando capita.

La data sta nel template Bio in testa alla voce (AnnoMorte, GiornoMeseMorte):
e' lo stesso che genera la categoria "Morti nel 2026".
"""
import json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wd import UA

API = 'https://it.wikipedia.org/w/api.php'

MESI = {m: i + 1 for i, m in enumerate((
    'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio',
    'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'))}


def titolo(url):
    """https://it.wikipedia.org/wiki/Pietro_Soddu -> 'Pietro Soddu'."""
    return urllib.parse.unquote(url.rsplit('/wiki/', 1)[-1]).replace('_', ' ')


# Wikimedia risponde 429 a raffica a chi non si presenta con un contatto:
# lo User-Agent e' quello di Wikidata, e i tentativi sono generosi.
def _chiedi(parametri, tentativi=6):
    ultimo = None
    for i in range(tentativi):
        try:
            u = API + '?' + urllib.parse.urlencode(parametri)
            r = urllib.request.Request(u, headers={'User-Agent': UA})
            return json.load(urllib.request.urlopen(r, timeout=120))
        except Exception as e:
            ultimo = e
            sys.stderr.write('  ritento (%d): %s\n' % (i + 1, e))
            time.sleep(5 * (i + 1))
    raise ultimo


def _campo(bio, nome):
    m = re.search(r'\|\s*%s\s*=\s*([^|\n}]*)' % nome, bio)
    return m.group(1).strip() if m else ''


def data_morte(testo):
    """(data, precisione) dal template Bio, oppure None se la voce non ne ha."""
    m = re.search(r'\{\{\s*Bio\s*\|', testo or '', re.I)
    if not m:
        return None
    bio = testo[m.start():]
    anno = re.match(r'(\d{4})\b', _campo(bio, 'AnnoMorte'))
    if not anno:
        return None
    # '16 settembre', ma anche '1º settembre' o '1° settembre'
    gm = re.match(r'(\d{1,2})\D*?\s+([a-z]+)', _campo(bio, 'GiornoMeseMorte').lower())
    if gm and gm.group(2) in MESI:
        return '%s-%02d-%02d' % (anno.group(1), MESI[gm.group(2)], int(gm.group(1))), 'giorno'
    return anno.group(1), 'anno'


def morti(titoli):
    """{titolo richiesto: (data, precisione)} per le voci che riportano una morte.

    Se l'API non risponde l'eccezione sale: chi chiama decide se fermarsi.
    """
    titoli = list(dict.fromkeys(titoli))
    fuori = {}
    for i in range(0, len(titoli), 50):
        blocco = titoli[i:i + 50]
        r = _chiedi({'action': 'query', 'prop': 'revisions', 'rvprop': 'content',
                     'rvslots': 'main', 'redirects': 1, 'titles': '|'.join(blocco),
                     'format': 'json', 'formatversion': 2})['query']
        # La voce puo' essere stata spostata: si risale dal titolo finale a
        # quello che avevamo chiesto.
        verso = {t: t for t in blocco}
        for passo in r.get('normalized', []) + r.get('redirects', []):
            for orig, dest in list(verso.items()):
                if dest == passo['from']:
                    verso[orig] = passo['to']
        testi = {p['title']: p['revisions'][0]['slots']['main']['content']
                 for p in r.get('pages', []) if p.get('revisions')}
        for orig, finale in verso.items():
            d = data_morte(testi.get(finale))
            if d:
                fuori[orig] = d
        time.sleep(0.5)
    return fuori
