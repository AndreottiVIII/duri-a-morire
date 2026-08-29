# -*- coding: utf-8 -*-
"""Genera il sito Televideo a partire da data/elenco.json.

Produce un unico file HTML autoportante: si apre con doppio clic dal disco,
senza server e senza installare niente. Le foto arrivano da Wikimedia Commons.
"""
import sys, os, json, datetime, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cursus

QUI = os.path.dirname(os.path.abspath(__file__))
INGRESSO = os.path.join(QUI, '..', 'data', 'elenco.json')
USCITA_DIR = os.path.join(QUI, '..', 'sito')
USCITA = os.path.join(USCITA_DIR, 'index.html')

# Lo stesso sito esce due volte, identico salvo il nome: uno per chi capisce
# la battuta e uno da mandare in giro senza spiegazioni. Il lavoro notturno li
# ricostruisce entrambi, quindi non divergono mai.
EDIZIONI = [
    ('index.html', 'Duri a morire — Prima Repubblica edition', 'DURI A MORIRE'),
    ('tracker.html', 'Prima Repubblica Tracker', 'PRIMA REPUBBLICA'),
]
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
    ('Radicali Italiani', 'PR'),
    # 'indipendente' va dopo 'sinistra indipendente', che e' un'altra cosa
    ('indipendente', 'IND.'),
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

# I gruppi parlamentari come li scrivono i registri. Vanno prima delle SIGLE
# generiche perche' certi nomi ingannano: il gruppo "PARTITO SOCIALISTA
# ITALIANO - PARTITO SOCIALISTA DEMOCRATICO ITALIANO UNIFICATI" contiene per
# intero il nome del PSDI, ma era il PSU.
GRUPPI = [
    ('PARTITO SOCIALISTA ITALIANO - PARTITO SOCIALISTA DEMOCRATICO', 'PSU'),
    ('PSI-PSDI', 'PSU'),
    ('PARTITO SOCIALISTA UNITARIO', 'PSU'),
    ("PARTITO SOCIALISTA ITALIANO DI UNITA' PROLETARIA", 'PSIUP'),
    ('PARTITO SOCIALISTA DEI LAVORATORI', 'PSLI'),
    ('PARTITO SOCIALISTA LAVORATORI', 'PSLI'),
    ("UNITA' SOCIALISTA", 'US'),
    ('PARTITO SOCIALISTA DEMOCRATICO', 'PSDI'),
    ('PARTITO SOCIALISTA ITALIANO', 'PSI'),
    ('PARTITO SOCIALISTA', 'PSI'),
    ('DEMOCRATICO CRISTIANO', 'DC'),
    ('DEMOCRAZIA CRISTIANA', 'DC'),
    ('CENTRO CRISTIANO DEMOCRATICO', 'CCD'),
    ('COMUNISTA - PDS', 'PDS'),
    ('RIFONDAZIONE COMUNISTA', 'PRC'),
    ('DP-COMUNISTI', 'DP'),
    ('DEMOCRAZIA PROLETARIA', 'DP'),
    ('PARTITO COMUNISTA ITALIANO', 'PCI'),
    ('COMUNISTA', 'PCI'),
    ('SINISTRA INDIPENDENTE', 'SI'),
    ('SIN. IND.', 'SI'),
    ('MSI-DESTRA NAZIONALE', 'MSI'),
    ('MOVIMENTO SOCIALE ITALIANO', 'MSI'),
    ('MSI - DN', 'MSI'),
    ('MSI', 'MSI'),
    ('COSTITUENTE DI DESTRA', 'DN'),
    ('DEMOCRAZIA NAZIONALE', 'DN'),
    ("FRONTE LIBERALE DEMOCRATICO DELL'UOMO QUALUNQUE", 'FUQ'),
    ('UOMO QUALUNQUE', 'FUQ'),
    ('PARTITO LIBERALE ITALIANO', 'PLI'),
    ('LIBERALE', 'PLI'),
    ('PARTITO REPUBBLICANO', 'PRI'),
    ('REPUBBLICANO', 'PRI'),
    ("PARTITO DEMOCRATICO ITALIANO DI UNITA'", 'PDIUM'),
    ('PARTITO DEMOCRATICO ITALIANO', 'PDI'),
    ('PARTITO NAZIONALE MONARCHICO', 'PNM'),
    ('PARTITO MONARCHICO POPOLARE', 'PMP'),
    ('UNIONE DEMOCRATICA NAZIONALE', 'UDN'),
    ("BLOCCO NAZIONALE DELLA LIBERTA'", 'BNL'),
    ('DEMOCRAZIA DEL LAVORO', 'DL'),
    ('MOVIMENTO PER LA DEMOCRAZIA', 'RETE'),
    ('PARTITO RADICALE', 'PR'),
    ('RADICALE', 'PR'),
    ('LEGA NORD', 'LN'),
    ('FEDERALISTA EUROPEO', 'FE'),
    ('UNIONE NAZIONALE', 'UN'),
    ('AUTONOMISTA', 'AUT'),
    ('VERDE', 'VERDI'),
    ('VERDI', 'VERDI'),
    ('SUDTIROLER', 'SVP'),
    ('MISTO', 'MISTO'),
    # forme abbreviate e puntate con cui il Senato scrive certi gruppi
    ('RIF.COM', 'PRC'),
    ('DEM. SIN', 'DS'),
    ('LIB. SOC. REP', 'LSR'),
    ('FED. EUR', 'FE'),
    ('PSDI - LIB', 'PSDI'),
]


# Gruppi che non sono partiti: il misto raccoglie chi un gruppo non ce l'ha,
# l'autonomista metteva insieme sardisti, azionisti e socialisti, e i gruppi
# congiunti sono due partiti sotto un tetto. Per chi sedeva li' il gruppo non
# dice niente, e comanda il partito di Wikidata.
CONTENITORI = {
    'MISTO', 'AUTONOMISTA', 'DEM. SIN.', 'DEM. IND. SIN.',
    'LIB. SOC. REP.', 'PSDI - LIB.', 'MSI - PNM',
    'FEDERALISTA EUROPEO', 'FED. EUR. EC.',
}


def e_contenitore(gruppo):
    return (gruppo or '').strip().upper().rstrip('.') in {
        c.rstrip('.') for c in CONTENITORI}


# Partiti che nessuno ha mai preso come seconda casacca: quando compaiono sono
# quella che definisce la persona, e vanno riconosciuti prima dei grandi.
# Il terzo campo, quando c'e', dice in quali legislature quel partito poteva
# esistere: il Partito d'Azione si sciolse nel 1947, e attribuirlo a un
# deputato eletto nel 1987 sarebbe lo stesso errore di Sgarbi al contrario.
DISTINTIVI = [
    ("Partito Sardo d'Azione", 'PSdAz', None),
    ('Partito Sardo d', 'PSdAz', None),
    ("Partito d'Azione", 'PdA', {'Costituente', 'I', 'II'}),
    ('Partito d’Azione', 'PdA', {'Costituente', 'I', 'II'}),
    ('Sudtiroler Volkspartei', 'SVP', None),
    ('Volkspartei', 'SVP', None),
    ('Union Vald', 'UV', None),
    ('Movimento Indipendentista Siciliano', 'MIS', None),
    ('Unione Siciliana Cristiano Sociale', 'USCS', None),
    ('Partito Nazionale Fascista', 'PNF', {'Costituente', 'I'}),
]


def sigla_gruppo(gruppo):
    """Dal nome del gruppo parlamentare alla sigla.

    Il Senato certi gruppi li scrive gia' abbreviati ('PLI', 'PSIUP'): quelle
    vanno lasciate stare, non ridotte alla loro iniziale come farebbe
    l'acronimo automatico.
    """
    g = (gruppo or '').upper().replace('’', "'")
    if not g:
        return ''
    for lungo, corto in GRUPPI:
        if lungo in g:
            return corto
    compatto = re.sub(r'[^A-Z]', '', g)
    if len(compatto) <= 6 and len(g) <= 8:
        return compatto
    return acronimo(gruppo)


# Le sigle per esteso. Una sigla sola dice poco a chi non ha vissuto quegli
# anni, e "FUQ" o "PDIUM" non le indovina nessuno.
NOMI_PARTITI = {
    'DC': 'Democrazia Cristiana',
    'PCI': 'Partito Comunista Italiano',
    'PSI': 'Partito Socialista Italiano',
    'MSI': 'Movimento Sociale Italiano',
    'MISTO': 'Gruppo misto',
    'PRI': 'Partito Repubblicano Italiano',
    'PSDI': 'Partito Socialista Democratico Italiano',
    'PLI': 'Partito Liberale Italiano',
    'PDS': 'Partito Democratico della Sinistra',
    'LN': 'Lega Nord',
    'PSU': 'PSI-PSDI Unificati',
    'SI': 'Sinistra Indipendente',
    'PNM': 'Partito Nazionale Monarchico',
    'PRC': 'Partito della Rifondazione Comunista',
    'FUQ': "Fronte dell'Uomo Qualunque",
    'UDN': 'Unione Democratica Nazionale',
    'VERDI': 'Federazione dei Verdi',
    'PR': 'Partito Radicale',
    'PSIUP': "Partito Socialista Italiano di Unita' Proletaria",
    'PSLI': 'Partito Socialista dei Lavoratori Italiani',
    'US': "Unita' Socialista",
    'DP': 'Democrazia Proletaria',
    'DN': 'Democrazia Nazionale',
    'PDIUM': "Partito Democratico Italiano di Unita' Monarchica",
    'PMP': 'Partito Monarchico Popolare',
    'PDI': 'Partito Democratico Italiano',
    'BNL': "Blocco Nazionale della Liberta'",
    'DL': 'Democrazia del Lavoro',
    'RETE': 'Movimento per la Democrazia: La Rete',
    'CCD': 'Centro Cristiano Democratico',
    'FE': 'Federalista Europeo',
    'UN': 'Unione Nazionale',
    'AUT': 'Autonomista',
    'SVP': 'Sudtiroler Volkspartei',
    'IND.': 'Indipendente',
    'RAD.': 'Radicali',
    'LSR': 'Liberale Socialista Repubblicano',
    'PUPC': "Partito di Unita' Proletaria per il Comunismo",
    'DS': 'Democratici di Sinistra',
    'PSDAZ': "Partito Sardo d'Azione",
    'PSdAz': "Partito Sardo d'Azione",
    'PdA': "Partito d'Azione",
    'PDA': "Partito d'Azione",
    'UV': 'Union Valdotaine',
    'USCS': 'Unione Siciliana Cristiano Sociale',
    'PPI': 'Partito Popolare Italiano',
    'PD': 'Partito Democratico',
    'FI': 'Forza Italia',
    'AN': 'Alleanza Nazionale',
    'PNF': 'Partito Nazionale Fascista',
    'MIS': 'Movimento Indipendentista Siciliano',
    'PDLav': 'Partito Democratico del Lavoro',
    'PCdI': "Partito Comunista d'Italia",
    'PFR': 'Partito Fascista Repubblicano',
    'PDL': "Il Popolo della Liberta'",
    'AP': 'Alleanza dei Progressisti',
    'DIS': 'Democratici Indipendenti di Sinistra',
    'ESS': 'Estrema sinistra storica',
    'FDP': 'Fronte Democratico Popolare',
    'LAL': 'Lega Alpina Lumbarda',
    'LAV': 'Lega Autonomia Veneta',
    'LV': 'Liga Veneta',
    'MC': "Movimento Comunita'",
    'PLD': 'Partito Liberale Democratico',
    'PSU': 'PSI-PSDI Unificati',
    'LSR': 'Liberale Socialista Repubblicano',
}

ORDINE_MANDATI = ['Costituente', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII',
                  'VIII', 'IX', 'X', 'XI', 'Governo Ciampi', 'Governo Dini']


# Le sigle gia' scritte a mano nel file: vanno solo messe in maiuscolo, tranne
# quelle che accorciate male diventerebbero illeggibili.
# Le sigle del foglio curato vanno ricondotte a quelle che usa tutto il resto
# del sito, o lo stesso partito finisce contato due volte: Emma Bonino era
# l'unica "Rad." e restava fuori dai radicali.
CURATE = {'La Rete': 'RETE', 'Rad.': 'PR', 'Radicali': 'PR'}


def sigla_curata(partito):
    return CURATE.get(partito.strip(), partito.strip().upper())[:6]


def sigla(partiti, ripiego=None, mandati=None):
    for lungo, corto, ammessi in DISTINTIVI:
        if ammessi and not (ammessi & set(mandati or [])):
            continue
        for x in partiti:
            if lungo.lower() in x.lower():
                return corto
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
        # Ordine di precedenza: la scelta editoriale sui 66, poi il gruppo
        # parlamentare di allora, e solo in mancanza di entrambi Wikidata.
        'p': (sigla_curata(p['partito_hof']) if p.get('partito_hof')
              else sigla(p['partiti'], mandati=p['mandati'])
                   if e_contenitore(p.get('gruppo_eletto')) and p['partiti']
              else sigla_gruppo(p['gruppo_eletto']) if p.get('gruppo_eletto')
              else sigla(p['partiti'], mandati=p['mandati'])),
    }
    if p.get('foto'):
        d['f'] = foto_url(p['foto'])
    if p.get('wikipedia'):
        d['w'] = p['wikipedia']
    if p.get('hall_of_fame'):
        d['h'] = 1
    if p.get('non_eletto'):
        d['x'] = 1
    # Del cursus scritto a mano resta solo quello che le cariche non dicono
    # gia': altrimenti la scheda ripete due volte le stesse poltrone.
    if p.get('cursus'):
        avanzo = cursus.residuo(p['cursus'], p.get('cariche_datate'))
        if avanzo:
            d['cr'] = avanzo
    if p.get('fonte_morte'):
        d['fd'] = p['fonte_morte']
    if p.get('morte_dubbia'):
        d['md'] = p['morte_dubbia']
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
        'nomi_partiti': NOMI_PARTITI,
        'persone': persone,
    }

    modello = open(MODELLO, encoding='utf-8').read()
    base = modello.replace('/*__DATI__*/',
                           json.dumps(dati, ensure_ascii=False, separators=(',', ':')))

    os.makedirs(USCITA_DIR, exist_ok=True)
    for nome_file, titolo, testata in EDIZIONI:
        percorso = os.path.join(USCITA_DIR, nome_file)
        html = base.replace('%%TITOLO%%', titolo).replace('%%TESTATA%%', testata)
        open(percorso, 'w', encoding='utf-8').write(html)
        print('Scritto %s (%.0f KB) — %s'
              % (os.path.normpath(percorso), os.path.getsize(percorso) / 1024.0, titolo))
    print('%d persone, di cui %d viventi' % (
        len(persone), sum(1 for p in persone if p['s'] == 1)))


if __name__ == '__main__':
    main()
