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
    # L'icona come file vero, per Google: quella incorporata (data:) nei
    # risultati di ricerca la ignora e mette il mappamondo grigio. I file
    # stanno nello specchio, prima-repubblica-tracker/sito/.
    '<link rel="icon" href="https://primarepubblica.net/favicon.ico" sizes="48x48">',
    '<link rel="icon" type="image/png" sizes="96x96" href="https://primarepubblica.net/favicon-96.png">',
    '<link rel="icon" type="image/png" sizes="192x192" href="https://primarepubblica.net/favicon-192.png">',
    '<link rel="apple-touch-icon" href="https://primarepubblica.net/apple-touch-icon.png">',
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


# Gli incarichi di governo arrivano dalla Camera uno per governo: Formica alle
# Finanze sono quattro righe, Spadolini I e II, Andreotti VI e VII. Si
# uniscono quelli attaccati, a meno di tre mesi uno dall'altro, e si tiene
# l'elenco dei governi. Un incarico ripreso anni dopo resta una riga a se'.
STACCO_GOVERNI = 92

# Le cariche di Wikidata che sono incarichi di governo: dove c'e' l'elenco
# della Camera, che ha il nome del ministero com'era allora, comanda quello.
PREFISSI_GOVERNO = ('ministro', 'ministri ', 'presidente del consiglio',
                    'vicepresidente del consiglio', 'sottosegretario',
                    'viceministro', 'vice ministro', 'alto commissario')


def _giorni(a, b):
    g = lambda s: datetime.date(int(s[:4]), int(s[5:7]), int(s[8:10]))
    return (g(b) - g(a)).days


def _carica_pulita(c):
    """La Camera mette a volte lo spazio dopo l'apostrofo ('dell' Industria')
    e ha qualche maiuscola di troppo battuta a mano ('MInistro del BIlancio').
    In alcuni governi l'accento e' un apostrofo: "Sanita'" accanto a "Sanità"."""
    c = re.sub(r"(?<=\w)([aeiou])'(?!\w)", lambda m: 'àèìòù'['aeiou'.index(m.group(1))], c)
    c = re.sub(r"(\w)' (?=\w)", r"\1'", c)
    c = re.sub(r'\b([A-Z])([A-Z])(?=[a-z])', lambda m: m.group(1) + m.group(2).lower(), c)
    return c.strip()


def _stessa_carica(c):
    """Lo stesso ministero la Camera lo scrive in piu' modi da un governo
    all'altro: 'Previdenza Sociale' e 'Previdenza sociale', 'culturali ed
    ambientali' e 'culturali e ambientali'. Per unirli conta la sostanza."""
    k = _carica_pulita(c).lower().replace(' ed ', ' e ')
    return re.sub(r'\s+', ' ', k)


def incarichi_governo(lista):
    righe, ultima = [], {}
    for i in sorted(lista, key=lambda i: i['da'] or ''):
        i = dict(i, carica=_carica_pulita(i['carica']))
        r = ultima.get(_stessa_carica(i['carica']))
        if r and r['a'] and i['da'] and _giorni(r['a'], i['da']) <= STACCO_GOVERNI:
            r['a'] = i['a'] if not i['a'] or i['a'] > r['a'] else r['a']
            if i.get('governo') and i['governo'] not in r['governi']:
                r['governi'].append(i['governo'])
            continue
        r = {'carica': i['carica'], 'da': i['da'], 'a': i['a'],
             'governi': [i['governo']] if i.get('governo') else []}
        righe.append(r)
        ultima[_stessa_carica(i['carica'])] = r
    return [[r['carica'], (r['da'] or '')[:4], (r['a'] or '')[:4], ', '.join(r['governi'])]
            for r in righe]


def gia_in_parlamento(c, parlamento):
    """Una carica di Wikidata che le Camere registrano gia': "Presidente della
    Camera dei deputati 1992-1994" e "Presidente della Camera 1992-1994" sono
    la stessa. Stesso inizio di nome e anni che si toccano."""
    mia = c['carica'].lower()
    for nome, da, a in parlamento:
        loro = nome.lower()
        if not (mia.startswith(loro) or loro.startswith(mia)):
            continue
        if not c.get('da') or not da:
            return True
        if int(c['da']) <= int(a or 9999) and int(da) <= int(c.get('a') or 9999):
            return True
    return False


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
    # Dall'anagrafe della Camera: il sesso, per scrivere "deceduta" e non
    # "deceduto"; studi e professione; la foto ufficiale per chi su Wikimedia
    # non ce l'ha; la Consulta Nazionale; gli incarichi di governo.
    if p.get('genere') == 'f':
        d['g'] = 'f'
    if p.get('studi'):
        d['st'] = p['studi']
    if not d.get('f') and p.get('foto_camera'):
        d['f'] = p['foto_camera']
        d['fc'] = 1
    # i collegamenti alle schede autorevoli: portale storico della Camera,
    # scheda del Senato, Treccani
    lk = [p.get('storia_camera') or '', p.get('scheda_senato') or '', p.get('treccani') or '']
    if any(lk):
        d['lk'] = lk
    if p.get('consulta'):
        d['cn'] = 1
    # dove e come e' stato eletto in ogni legislatura: ['IX', 'C', 'Bari'],
    # ['VIII', 'S', 'a vita']
    elezioni = p.get('elezioni') or {}
    if elezioni:
        d['el'] = [[m] + elezioni[m] for m in d['m'] if m in elezioni]
    if p.get('proposte'):
        d['pl'] = [p['proposte']['primo'], p['proposte']['cofirmate']]
    # i voti di preferenza, legislatura per legislatura: ['X', 75251]
    if p.get('preferenze'):
        d['pf'] = [[x[0], x[4]] for x in sorted(p['preferenze'],
                                                key=lambda x: ORDINE_MANDATI.index(x[0]))]
    # I gruppi parlamentari, legislatura per legislatura, coi passaggi:
    # {'IV': [['PSI', '1963'], ['PSI-PSDI', '1966']]}. Due adesioni di fila
    # allo stesso gruppo (una sospensione, un cambio di ramo) sono una sola.
    if p.get('gruppi'):
        gr = {}
        for leg, ramo, sigla, da, a in p['gruppi']:
            righe = gr.setdefault(leg, [])
            if not righe or righe[-1][0] != sigla:
                righe.append([sigla, (da or '')[:4]])
        d['gr'] = gr
    # le domande di autorizzazione a procedere (e all'arresto) contro di lui,
    # 1983-1994: [anno, arresto 0/1, esito 'c' concessa 'n' negata 'r' atti
    # restituiti, '' nessun voto registrato]
    if p.get('autorizzazioni'):
        d['au'] = [['19' + x[1][-2:], 1 if x[2] == 'arresto' else 0, (x[4] or '')[:1]]
                   for x in p['autorizzazioni']]
    # le elezioni alla Camera in cui era candidato e non e' entrato:
    # [legislatura, anno, circoscrizione, preferenze]
    if p.get('sconfitte'):
        d['sc'] = [[x[0], x[1], x[2].split('-')[0].title(), x[4]] for x in p['sconfitte']]
    governo = incarichi_governo(p.get('incarichi_governo') or [])
    if governo:
        d['gv'] = governo
    # le cariche in Parlamento si uniscono con la stessa regola: tre mandati
    # di fila da Presidente della Camera sono una riga sola
    parlamento = [r[:3] for r in incarichi_governo(p.get('incarichi_parlamento') or [])]
    if parlamento:
        d['ip'] = parlamento

    cariche = cursus.completa_date(p.get('cursus'), p.get('cariche_datate'))
    if governo:
        cariche = [c for c in cariche if not c['carica'].lower().startswith(PREFISSI_GOVERNO)]
    if parlamento:
        cariche = [c for c in cariche if not gia_in_parlamento(c, parlamento)]
    if p.get('cursus'):
        # il cursus scritto a mano non deve ripetere ne' le cariche, ne' il
        # governo, ne' il Parlamento
        avanzo = cursus.residuo(p['cursus'], cariche + [
            {'carica': r[0], 'da': r[1] or None, 'a': r[2] or None}
            for r in governo + parlamento])
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
    # dove e' nato, morto e sepolto, quando Wikidata lo sa
    lu = p.get('luoghi') or {}
    if lu:
        d['lu'] = [lu.get('nascita', ''), lu.get('morte', ''), lu.get('sepoltura', '')]
    return d


def main():
    grezzo = json.load(open(INGRESSO, encoding='utf-8'))
    persone = [compatta(p) for p in grezzo['persone']]
    # Le parentele, dette dal punto di vista della scheda: di Antonio Gava,
    # Silvio Gava e' il padre. La parola dipende dal sesso dell'altro, quando
    # l'anagrafe della Camera lo sa.
    genere = {p['qid']: p.get('genere') for p in grezzo['persone']}
    parole = {'figlio': ('figlio', 'figlia'), 'fratello': ('fratello', 'sorella')}
    per_qid = {d['q']: d for d in persone}
    for p in grezzo['persone']:
        if p.get('parenti') and p['qid'] in per_qid:
            fa = []
            for rel, altro in p['parenti']:
                if rel in parole:
                    rel = parole[rel][1] if genere.get(altro) == 'f' else parole[rel][0]
                fa.append([rel, altro])
            per_qid[p['qid']]['fa'] = fa
    # le righe di spiegazione scritte a mano, con la fonte
    note = json.load(open(os.path.join(QUI, '..', 'data', 'note_redazione.json'), encoding='utf-8'))
    for d in persone:
        if d['q'] in note:
            d['nt'] = [note[d['q']]['testo'], note[d['q']]['fonte']]
    # la lista della P2 sequestrata nel 1981, con la nota che vi si legge
    p2 = os.path.join(QUI, '..', 'data', 'registri', 'lista_p2.json')
    if os.path.exists(p2):
        for v in json.load(open(p2, encoding='utf-8')):
            if v['qid'] in per_qid:
                per_qid[v['qid']]['p2'] = ('in sonno' if v['in_sonno'] else
                                           'passato al Grande Oriente' if v['grande_oriente'] else '')
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
    # I titoli delle proposte di legge non stanno nel programma, che pesa gia'
    # abbastanza: ogni scheda ha il suo file, che il Televideo legge quando la
    # si apre.
    titoli_proposte = {}
    copia = os.path.join(QUI, '..', 'data', 'registri', 'camera_proposte.json')
    if os.path.exists(copia):
        proposte = json.load(open(copia, encoding='utf-8'))
        for p in grezzo['persone']:
            v = proposte.get(p.get('anagrafe_camera') or p.get('id_camera') or '')
            if p.get('proposte') and v and v.get('titoli'):
                titoli_proposte[p['qid']] = [[d[:4], t] for d, t in v['titoli']]
    quanti, in_mappa = pagine_statiche.costruisci(
        scheletro, dati_veri, (titolo_home, descrizione, dati_strutturati(dati)), ARCHIVIO,
        titoli_proposte)
    print('Scritto %s (%.0f KB) — %d file, %d indirizzi nella mappa del sito'
          % (os.path.normpath(ARCHIVIO), os.path.getsize(ARCHIVIO) / 1024.0,
             quanti, in_mappa))
    print('%d persone, di cui %d viventi' % (
        len(persone), sum(1 for p in persone if p['s'] == 1)))


if __name__ == '__main__':
    main()
