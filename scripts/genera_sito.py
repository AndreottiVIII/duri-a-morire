# -*- coding: utf-8 -*-
"""Genera il sito Televideo a partire da data/elenco.json.

Produce un unico file HTML autoportante: si apre con doppio clic dal disco,
senza server e senza installare niente. Le foto arrivano da Wikimedia Commons.
"""
import sys, os, json, datetime, re

QUI = os.path.dirname(os.path.abspath(__file__))
INGRESSO = os.path.join(QUI, '..', 'data', 'elenco.json')
USCITA_DIR = os.path.join(QUI, '..', 'sito')
USCITA = os.path.join(USCITA_DIR, 'index.html')
MODELLO = os.path.join(QUI, 'modello.html')

# Sigle di partito: quarant'anni di prima Repubblica in sei caratteri.
SIGLE = [
    ('Democrazia Cristiana', 'DC'),
    ('Partito Comunista Italiano', 'PCI'),
    ('Partito Socialista Italiano di Unit', 'PSIUP'),
    ('Partito Socialista Democratico Italiano', 'PSDI'),
    ('Partito Socialista Italiano', 'PSI'),
    ('Partito Repubblicano Italiano', 'PRI'),
    ('Partito Liberale Italiano', 'PLI'),
    ('Movimento Sociale Italiano', 'MSI'),
    ('Partito Democratico della Sinistra', 'PDS'),
    ('Rifondazione Comunista', 'PRC'),
    ('Partito Radicale', 'PR'),
    ('Democrazia Proletaria', 'DP'),
    ('Lega Nord', 'LN'),
    ('Lega Lombarda', 'LL'),
    ('Federazione dei Verdi', 'VERDI'),
    ('Verdi', 'VERDI'),
    ('Sudtiroler Volkspartei', 'SVP'),
    ('Volkspartei', 'SVP'),
    ('Rete', 'RETE'),
    ('Partito Nazionale Monarchico', 'PNM'),
    ('Partito Monarchico Popolare', 'PMP'),
    ('Partito Monarchico', 'PNM'),
    ('sinistra indipendente', 'SI'),
    ('PSI-PSDI', 'PSU'),
    ('Partito Popolare Italiano', 'PPI'),
    ('Partito Nazionale Fascista', 'PNF'),
    # I minori della Costituente e della prima Repubblica: pochi seggi, ma
    # hanno fatto la storia di quegli anni e meritano la loro sigla.
    ('Fronte dell’Uomo Qualunque', 'FUQ'),
    ("Fronte dell'Uomo Qualunque", 'FUQ'),
    ('Unione Democratica Nazionale', 'UDN'),
    ('Blocco Nazionale della Libert', 'BNL'),
    ('Partito Sardo d', 'PSdAz'),
    ('Partito d’Azione', 'PdA'),
    ("Partito d'Azione", 'PdA'),
    ('Partito Democratico del Lavoro', 'PDLav'),
    ('Partito Democratico Italiano di Unit', 'PDIUM'),
    ('Union Vald', 'UV'),
    ('Unione Siciliana Cristiano Sociale', 'USCS'),
    ('Movimento Indipendentista Siciliano', 'MIS'),
    ('Partito Socialista Unitario', 'PSU'),
    ('Partito Comunista d', 'PCdI'),
    ('Partito Fascista Repubblicano', 'PFR'),
    ('Democrazia Nazionale', 'DN'),
    ('Movimento per la Democrazia', 'RETE'),
]

ORDINE_MANDATI = ['Costituente', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII',
                  'VIII', 'IX', 'X', 'XI', 'Governo Ciampi', 'Governo Dini']


# Le sigle gia' scritte a mano nel file: vanno solo messe in maiuscolo, tranne
# quelle che accorciate male diventerebbero illeggibili.
CURATE = {'La Rete': 'RETE'}


def sigla_curata(partito):
    return CURATE.get(partito.strip(), partito.strip().upper())[:6]


def sigla(partiti, ripiego=None):
    # L'ordine delle SIGLE decide la precedenza: chi ha militato prima nella DC
    # e poi nel PPI va mostrato come DC, non come il partito che venne dopo.
    for lungo, corto in SIGLE:
        for p in partiti:
            if lungo.lower() in p.lower():
                return corto
    if ripiego:
        return sigla_curata(ripiego)
    if partiti:
        return acronimo(partiti[0])
    return ''


PAROLINE = {'di', 'del', 'della', 'dei', 'degli', 'delle', 'e', 'per', 'con',
            'il', 'la', 'lo', 'i', 'gli', 'le', 'dell', 'è', 'a', 'da'}


def acronimo(nome):
    """Da 'Alleanza Nazionale' ad 'AN': meglio le iniziali che un troncone.
    Via le precisazioni fra parentesi e i trattini, che producevano sigle
    come 'UC(' o 'DÈL–M'."""
    nome = re.sub(r'\([^)]*\)', ' ', nome)
    parole = [w for w in re.split(r'[^0-9A-Za-zÀ-ɏ]+', nome)
              if w and w.lower() not in PAROLINE]
    return ''.join(w[0] for w in parole).upper()[:6]


def foto_url(u):
    if not u:
        return None
    return u.replace('http://', 'https://') + '?width=260'


def compatta(p):
    """Una persona ridotta all'osso: il file finito deve restare leggero."""
    d = {
        'q': p['qid'],
        'n': p['nome'] or '?',
        'b': p['nascita'],
        'bp': p['prec_nascita'],
        'd': p['morte'],
        'dp': p['prec_morte'],
        's': {'vivente': 1, 'deceduto': 2, 'ignoto': 3}[p['stato']],
        'm': [x for x in ORDINE_MANDATI if x in p['mandati']],
        # Per i 66 curati comanda la colonna scritta a mano: e' una scelta
        # editoriale su quale partito li definisca in quegli anni, e Wikidata
        # (che elenca anche le militanze successive) non la puo' rimpiazzare.
        'p': sigla_curata(p['partito_hof']) if p.get('partito_hof')
             else sigla(p['partiti']),
    }
    if p.get('foto'):
        d['f'] = foto_url(p['foto'])
    if p.get('wikipedia'):
        d['w'] = p['wikipedia']
    if p.get('hall_of_fame'):
        d['h'] = 1
    if p.get('non_eletto'):
        d['x'] = 1
    if p.get('cursus'):
        d['c'] = p['cursus']
    if p.get('fonte_morte'):
        d['fd'] = p['fonte_morte']
    # L'identificativo della Camera permette al tasto AGGIORNA di ricontrollare
    # il registro ufficiale senza dover riaccoppiare i nomi nel browser.
    if p.get('id_camera'):
        d['ci'] = p['id_camera']
    if p.get('morte_ignota'):
        d['di'] = 1
    if p.get('cariche_datate'):
        d['cd'] = [[c['carica'], c['da'] or '', c['a'] or ''] for c in p['cariche_datate']]
    return d


def main():
    grezzo = json.load(open(INGRESSO, encoding='utf-8'))
    persone = [compatta(p) for p in grezzo['persone']]
    persone.sort(key=lambda d: d['n'].lower())

    dati = {
        'generato': grezzo['generato'],
        'soglia': grezzo['eta_massima_credibile'],
        'legislature': [
            ['Costituente', '1946-48'], ['I', '1948-53'], ['II', '1953-58'],
            ['III', '1958-63'], ['IV', '1963-68'], ['V', '1968-72'],
            ['VI', '1972-76'], ['VII', '1976-79'], ['VIII', '1979-83'],
            ['IX', '1983-87'], ['X', '1987-92'], ['XI', '1992-94'],
            ['Governo Ciampi', '1993-94'], ['Governo Dini', '1995-96'],
        ],
        'persone': persone,
    }

    modello = open(MODELLO, encoding='utf-8').read()
    html = modello.replace('/*__DATI__*/',
                           json.dumps(dati, ensure_ascii=False, separators=(',', ':')))

    os.makedirs(USCITA_DIR, exist_ok=True)
    open(USCITA, 'w', encoding='utf-8').write(html)
    kb = os.path.getsize(USCITA) / 1024.0
    print('Scritto %s (%.0f KB)' % (os.path.normpath(USCITA), kb))
    print('%d persone, di cui %d viventi' % (
        len(persone), sum(1 for p in persone if p['s'] == 1)))


if __name__ == '__main__':
    main()
