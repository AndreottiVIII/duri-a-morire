# -*- coding: utf-8 -*-
"""Genera il sito Televideo a partire da data/elenco.json.

Produce un unico file HTML autoportante: si apre con doppio clic dal disco,
senza server e senza installare niente. Le foto arrivano da Wikimedia Commons.
"""
import sys, os, json, datetime, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cursus
import pagine_statiche

QUI = os.path.dirname(os.path.abspath(__file__))
INGRESSO = os.path.join(QUI, '..', 'data', 'elenco.json')
USCITA_DIR = os.path.join(QUI, '..', 'sito')
USCITA = os.path.join(USCITA_DIR, 'index.html')
# L'edizione che gira fuori, una pagina per schermata, impacchettata per il
# sito specchio (vedi pagine_statiche.py). Non entra nel repository: la
# pubblica solo il lavoro notturno.
ARCHIVIO = os.path.join(USCITA_DIR, 'primarepubblica.tar.gz')

# Lo stesso sito esce due volte, identico salvo il nome: uno per chi capisce
# la battuta e uno da mandare in giro senza spiegazioni. Il lavoro notturno li
# ricostruisce entrambi, quindi non divergono mai.
# Il colofone: chi fa il sito, da dove nasce, e cosa si puo' farne. Una riga
# che comincia con # e' un'intestazione, una vuota e' uno stacco. Sta solo
# nell'edizione che gira fuori, dove chi arriva non sa niente di noi.
COLOFONE = [
    'Questo sito tiene il conto di chi è ancora vivo fra i parlamentari e '
    'i ministri della Prima Repubblica: dalla Costituente del 1946 all’XI '
    'legislatura, più i ministri dei governi Ciampi e Dini.',
    '',
    'Si aggiorna ogni notte da solo, incrociando quattro fonti pubbliche: '
    'Wikidata, gli open data della Camera dei deputati e quelli del Senato, e '
    'le voci di Wikipedia.',
    '',
    '#CHI LO FA',
    'Davide Caniatti',
    'davide.caniatti@gmail.com',
    '',
    'Scrivetemi per segnalazioni, correzioni o domande.',
    '',
    '#DA DOVE NASCE',
    'Tutto parte dalla hall of fame. È la lista che Fabio, un amico, tiene '
    'a mano da anni per seguire gli ultimi dinosauri della Prima Repubblica: '
    'sessantasei nomi scelti da lui, fra ministri, segretari di partito, '
    'sindacalisti e banchieri.',
    '',
    'Il sito è nato per tenere aggiornata quella lista, e poi si è '
    'allargato a tutti i parlamentari.',
    '',
    '#DATI E PRIVACY',
    'I dati vengono da archivi pubblici e riguardano persone pubbliche per il '
    'ruolo che hanno ricoperto: date di nascita e di morte, legislature, gruppo '
    'parlamentare. Le stesse cose che stanno negli archivi del Parlamento e su '
    'Wikipedia.',
    '',
    'Quando le fonti sono in disaccordo, il sito lo scrive. Quando nessuna sa '
    'rispondere lo scrive lo stesso: né vivo né morto, non risulta.',
    '',
    '#RIPRODUZIONE',
    'I dati sono pubblici e liberi alla fonte: Wikidata e gli open data di '
    'Camera e Senato. Le fotografie vengono da Wikimedia Commons e restano dei '
    'loro autori.',
    '',
    'Il resto è mio: la raccolta, la verifica, il codice e queste pagine. '
    'La lista da cui tutto parte è di Fabio.',
    '',
    'Per copiare questo sito, ripubblicarlo altrove, riusarne delle parti o '
    'adattarlo serve la mia autorizzazione scritta, e va citata la fonte: '
    'Prima Repubblica Tracker, Davide Caniatti.',
    '',
    'Vale anche per gli estratti, per le tabelle e per i dati così come li '
    'trovate qui, già incrociati e verificati.',
    '',
    'Per chiedere l’autorizzazione: davide.caniatti@gmail.com',
]

# L'anteprima per WhatsApp, Telegram, Facebook, X. Solo per l'edizione che gira
# fuori: punta a primarepubblica.net, e l'immagine sta nel repository che la
# pubblica (prima-repubblica-tracker, sito/preview.jpg).
# La descrizione che Google mostra sotto il titolo. Sta sotto i 160 caratteri,
# oltre i quali viene tagliata, e porta il numero delle schede.
DESCRIZIONE_TRACKER = ('Chi è ancora vivo dei %s parlamentari e ministri della '
                       'Prima Repubblica, dalla Costituente al 1994. Aggiornato ogni '
                       'giorno con i dati di Camera e Senato.')
ANTEPRIMA_TRACKER = '\n'.join([
    '<meta name="description" content="%%DESCRIZIONE%%">',
    '<meta property="og:type" content="website">',
    '<meta property="og:locale" content="it_IT">',
    '<meta property="og:site_name" content="Prima Repubblica Tracker">',
    '<meta property="og:title" content="Prima Repubblica Tracker">',
    '<meta property="og:description" content="%%DESCRIZIONE%%">',
    '<meta property="og:url" content="https://primarepubblica.net/">',
    # Come voynichizer.com, dove WhatsApp l'anteprima la mostra: JPEG e non PNG,
    # tipo e indirizzo sicuro dichiarati, e un nome di file nuovo, perche'
    # WhatsApp si ricorda a lungo di un'immagine che non e' riuscito a leggere.
    '<meta property="og:image" content="https://primarepubblica.net/preview.jpg">',
    '<meta property="og:image:secure_url" content="https://primarepubblica.net/preview.jpg">',
    '<meta property="og:image:type" content="image/jpeg">',
    '<meta property="og:image:width" content="1200">',
    '<meta property="og:image:height" content="630">',
    '<meta property="og:image:alt" content="Una pagina del Televideo: Prima Repubblica, '
    'chi è ancora vivo e chi no">',
    '<meta name="twitter:card" content="summary_large_image">',
    '<meta name="twitter:image" content="https://primarepubblica.net/preview.jpg">',
])

EDIZIONI = [
    # nome file, titolo, testata, colofone, anteprima per le condivisioni
    ('index.html', 'Duri a morire — Prima Repubblica edition',
     'DURI A MORIRE', None, ''),
    ('tracker.html', 'Prima Repubblica Tracker: chi è ancora vivo fra i parlamentari',
     'PRIMA REPUBBLICA', COLOFONE, ANTEPRIMA_TRACKER),
]
MODELLO = os.path.join(QUI, 'modello.html')

# Tutte e due le edizioni, e la copia che sta su github.io, sono la stessa
# pagina. Google deve sapere qual e' quella da mostrare, o sceglie da solo e
# puo' scegliere quella sbagliata.
INDIRIZZO_UFFICIALE = 'https://primarepubblica.net/'


def migliaia(n):
    return format(n, ',').replace(',', '.')


def testa_per_motori(nome_file, dati):
    """L'indirizzo ufficiale e, per l'edizione che gira fuori, i dati
    strutturati: dicono a Google che questo e' un archivio, chi lo cura e da
    quali fonti viene, e lo rendono trovabile nella ricerca di dataset."""
    righe = ['<link rel="canonical" href="%s">' % INDIRIZZO_UFFICIALE]
    if nome_file == 'tracker.html':
        righe.append(dati_strutturati(dati))
    return '\n'.join(righe)


def dati_strutturati(dati):
    autore = {'@type': 'Person', '@id': INDIRIZZO_UFFICIALE + '#autore',
              'name': 'Davide Caniatti'}
    grafo = {
        '@context': 'https://schema.org',
        '@graph': [
            {'@type': 'WebSite', '@id': INDIRIZZO_UFFICIALE + '#sito',
             'url': INDIRIZZO_UFFICIALE, 'name': 'Prima Repubblica Tracker',
             'inLanguage': 'it-IT', 'author': {'@id': autore['@id']}},
            autore,
            {'@type': 'Dataset',
             'name': 'Parlamentari e ministri della Prima Repubblica: chi è ancora vivo',
             'description': ('Elenco dei %s parlamentari e ministri della Prima '
                             'Repubblica italiana, dalla Costituente del 1946 all’XI '
                             'legislatura, con data di nascita, data di morte, '
                             'legislature e gruppo parlamentare. Si aggiorna ogni '
                             'giorno incrociando Wikidata, gli open data della '
                             'Camera dei deputati e del Senato, e Wikipedia.'
                             % migliaia(len(dati['persone']))),
             'url': INDIRIZZO_UFFICIALE,
             'creator': {'@id': autore['@id']},
             'inLanguage': 'it-IT',
             'temporalCoverage': '1946/1996',
             'spatialCoverage': {'@type': 'Place', 'name': 'Italia'},
             'dateModified': dati['generato'],
             'isBasedOn': ['https://www.wikidata.org/',
                           'https://dati.camera.it/',
                           'https://dati.senato.it/',
                           'https://it.wikipedia.org/'],
             'keywords': ['Prima Repubblica', 'parlamentari', 'Assemblea Costituente',
                          'Camera dei deputati', 'Senato della Repubblica',
                          'storia politica italiana']},
        ],
    }
    return ('<script type="application/ld+json">%s</script>'
            % json.dumps(grafo, ensure_ascii=False, separators=(',', ':')))


def intestazione(nome_file):
    """Il titolo della pagina per chi legge con lo schermo e per i motori.
    Graficamente c'e' gia', nella testata del Televideo."""
    nome = ('Prima Repubblica Tracker' if nome_file == 'tracker.html'
            else 'Duri a morire')
    return ('<h1 class="solo-lettori">%s: chi è ancora vivo fra i parlamentari '
            'della Prima Repubblica</h1>' % nome)


def presentazione(nome_file, dati):
    """Una riga in chiaro in fondo alla pagina, per l'edizione che gira
    fuori. Senza, l'unico testo che Google trova e' la griglia dello schermo."""
    if nome_file != 'tracker.html':
        return ''
    vivi = sum(1 for p in dati['persone'] if p['s'] == 1)
    return ('<p class="presentazione">Prima Repubblica Tracker tiene il conto di chi '
            'è ancora vivo fra i %s parlamentari e ministri della Prima '
            'Repubblica, dalla Costituente del 1946 all’XI legislatura: '
            'oggi sono %s.</p>' % (migliaia(len(dati['persone'])), migliaia(vivi)))

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
]


# Partiti che nel Parlamento repubblicano non sono mai esistiti: sciolti prima
# del 1946, non possono essere il partito d'elezione di nessuno qui. Su
# Wikidata compaiono fra le militanze di chi c'era stato da giovane, e senza
# questo filtro Giorgio Almirante risultava eletto per il Partito Nazionale
# Fascista invece che per il MSI.
FUORI_EPOCA = (
    'partito nazionale fascista',
    'partito fascista repubblicano',
    'associazione nazionalista italiana',
)


def nel_perimetro(partito):
    basso = (partito or '').lower()
    return not any(x in basso for x in FUORI_EPOCA)


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


def partito_di(p):
    """La sigla del partito d'elezione.

    In ordine: la scelta editoriale sui 66 curati, poi il gruppo parlamentare
    di allora, e solo per i gruppi che partiti non sono il partito di Wikidata,
    ripulito da quelli che in Parlamento non ci sono mai stati.
    """
    if p.get('partito_hof'):
        return sigla_curata(p['partito_hof'])
    ammessi = [x for x in p['partiti'] if nel_perimetro(x)]
    if e_contenitore(p.get('gruppo_eletto')) and ammessi:
        return sigla(ammessi, mandati=p['mandati'])
    if p.get('gruppo_eletto'):
        return sigla_gruppo(p['gruppo_eletto'])
    return sigla(ammessi, mandati=p['mandati'])


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
        'p': partito_di(p),
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
    cariche = cursus.completa_date(p.get('cursus'), p.get('cariche_datate'))
    if p.get('cursus'):
        avanzo = cursus.residuo(p['cursus'], cariche)
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
    if cariche:
        d['cd'] = [[c['carica'], c['da'] or '', c['a'] or ''] for c in cariche]
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
    descrizione = DESCRIZIONE_TRACKER % migliaia(len(dati['persone']))
    for nome_file, titolo, testata, colofone, anteprima in EDIZIONI:
        percorso = os.path.join(USCITA_DIR, nome_file)
        html = (base.replace('<!--%%ANTEPRIMA%%-->', anteprima)
                    .replace('%%DESCRIZIONE%%', descrizione)
                    .replace('<!--%%CANONICO%%-->', testa_per_motori(nome_file, dati))
                    .replace('<!--%%INTESTAZIONE%%-->', intestazione(nome_file))
                    .replace('<!--%%PRESENTAZIONE%%-->', presentazione(nome_file, dati))
                    .replace('%%TITOLO%%', titolo)
                    .replace('%%TESTATA%%', testata)
                    .replace('/*__COLOFONE__*/',
                             json.dumps(colofone, ensure_ascii=False)))
        open(percorso, 'w', encoding='utf-8').write(html)
        print('Scritto %s (%.0f KB) — %s'
              % (os.path.normpath(percorso), os.path.getsize(percorso) / 1024.0, titolo))
    # L'edizione a pagine: stessi dati, piu' l'indirizzo di ogni scheda e il
    # posto dove andra' la tabella degli indirizzi.
    persone_veri = [dict(p) for p in persone]
    pagine_statiche.assegna_schegge(persone_veri)
    dati_veri = dict(dati, persone=persone_veri, __INDIRIZZI__=None)
    _, titolo_home, testata_home, _, _ = EDIZIONI[1]
    scheletro = (modello
                 .replace('/*__DATI__*/',
                          json.dumps(dati_veri, ensure_ascii=False, separators=(',', ':')))
                 .replace('<!--%%PRESENTAZIONE%%-->', presentazione('tracker.html', dati))
                 .replace('%%TESTATA%%', testata_home)
                 .replace('/*__COLOFONE__*/', json.dumps(COLOFONE, ensure_ascii=False)))
    quanti, in_mappa = pagine_statiche.costruisci(
        scheletro, dati_veri, (titolo_home, descrizione, dati_strutturati(dati)), ARCHIVIO)
    print('Scritto %s (%.0f KB) — %d file, %d indirizzi nella mappa del sito'
          % (os.path.normpath(ARCHIVIO), os.path.getsize(ARCHIVIO) / 1024.0,
             quanti, in_mappa))
    print('%d persone, di cui %d viventi' % (
        len(persone), sum(1 for p in persone if p['s'] == 1)))


if __name__ == '__main__':
    main()
