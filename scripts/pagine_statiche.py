# -*- coding: utf-8 -*-
"""L'edizione che gira fuori, scomposta in una pagina per schermata.

Il Televideo e' una pagina sola che cambia contenuto, e per Google era
proprio questo: una pagina. Le schede delle persone stavano dopo un
cancelletto (primarepubblica.net/#Q50005), e quella parte dell'indirizzo lui
la ignora. Chi cercava "Rino Formica" non arrivava qui.

Qui ogni schermata diventa un file vero, con il suo indirizzo, il suo titolo
e la sua descrizione:

    /onorevole/rino-formica/index.html
    /viventi/index.html
    /legislature/costituente/index.html

A vista non cambia niente. Ogni file contiene lo stesso Televideo e chiama lo
stesso programma, che sta in un file a parte (televideo.js) e il browser
scarica una volta sola: e' lui a leggere l'indirizzo e ad aprire la
schermata giusta. Il file e la mappa del sito finiscono in un archivio,
primarepubblica.tar.gz, che il sito specchio scarica e pubblica cosi' com'e'.
"""
import hashlib
import html
import io
import json
import os
import re
import tarfile
import unicodedata

INDIRIZZO = 'https://primarepubblica.net'
SITO = 'Prima Repubblica Tracker'

# Le schermate del Televideo e il loro indirizzo. Le legislature si
# aggiungono da sole, una per riga di DATI['legislature'].
PAGINE = {
    100: '/',
    101: '/viventi/',
    110: '/legislature/',
    130: '/hall-of-fame/',
    131: '/hall-of-fame/ancora-in-piedi/',
    132: '/hall-of-fame/in-memoriam/',
    133: '/hall-of-fame/per-partito/',
    134: '/hall-of-fame/compleanni/',
    135: '/hall-of-fame/piu-incarichi/',
    150: '/ricerca/',
    200: '/statistiche/',
    210: '/statistiche/sopravvissuti-per-partito/',
    220: '/statistiche/curva-di-estinzione/',
    230: '/statistiche/ultimi-per-legislatura/',
    240: '/statistiche/ultimi-per-partito/',
    250: '/statistiche/piu-legislature/',
    260: '/statistiche/defunti/',
    261: '/statistiche/defunti-per-partito/',
    270: '/statistiche/piu-incarichi/',
    280: '/statistiche/piu-votati/',
    285: '/statistiche/lista-p2/',
    290: '/camera/circoscrizioni/',
    295: '/senato/regioni/',
    300: '/in-memoriam/',
    400: '/sorte-ignota/',
    500: '/compleanni/',
    600: '/ricontrolla/',
    700: '/info/',
}

# Gli elenchi che si aprono toccando un numero: tipo -> inizio dell'indirizzo.
ELENCHI = {
    'partito': '/viventi/partito/',
    'mandato': '/viventi/legislatura/',
    'mortipartito': '/in-memoriam/partito/',
    'morti': '/in-memoriam/',
    'hof': '/hall-of-fame/partito/',
    # due dimensioni separate: la Camera votava per circoscrizioni, il Senato
    # per regioni
    'circ': '/camera/circoscrizione/',
    'reg': '/senato/regione/',
}

NON_ELETTIVI = ('a vita', 'di diritto')

# l'anno dell'elezione che apri' ogni legislatura
ANNI_ELEZIONE = {'I': '1948', 'II': '1953', 'III': '1958', 'IV': '1963', 'V': '1968',
                 'VI': '1972', 'VII': '1976', 'VIII': '1979', 'IX': '1983', 'X': '1987',
                 'XI': '1992'}


def eletti_per_luogo(persone, ramo):
    """{luogo: [persone]} per la Camera ('C') o il Senato ('S')."""
    fuori = {}
    for p in persone:
        for leg, r, luogo in p.get('el', []):
            if r == ramo and luogo and luogo not in NON_ELETTIVI:
                gente = fuori.setdefault(luogo, [])
                if p not in gente:
                    gente.append(p)
    return fuori

# Schermate che non servono a chi cerca: esistono, ma Google non le mostri.
FUORI_DAI_MOTORI = {150, 600}

MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio',
        'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']


def scheggia(testo):
    """'Ciriaco De Mita' -> 'ciriaco-de-mita'. La stessa riduzione la fa il
    Televideo (scheggia, in modello.html) per gli elenchi: devono coincidere."""
    t = unicodedata.normalize('NFD', str(testo).lower())
    t = ''.join(c for c in t if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')


def assegna_schegge(persone):
    """Il pezzo d'indirizzo di ogni scheda: il nome, e l'anno di nascita solo
    per gli omonimi. Se anche l'anno coincide, il codice Wikidata."""
    gruppi = {}
    for p in persone:
        # le precisazioni fra parentesi che Wikipedia aggiunge agli omonimi,
        # 'Giovanni Di Benedetto (politico 1923)', nell'indirizzo non servono:
        # agli omonimi ci pensa l'anno
        nome = re.sub(r'\s*\([^)]*\)', '', p['n'])
        gruppi.setdefault(scheggia(nome) or p['q'].lower(), []).append(p)
    for base, gente in gruppi.items():
        if len(gente) == 1:
            gente[0]['u'] = base
            continue
        anni = {}
        for p in gente:
            anni.setdefault((p['b'] or '')[:4], []).append(p)
        for a, stessi in anni.items():
            for p in stessi:
                if a and len(stessi) == 1:
                    p['u'] = '%s-%s' % (base, a)
                else:
                    p['u'] = '%s-%s' % (base, p['q'].lower())


# ------------------------------------------------------------ parole in chiaro

def accenta(testo):
    """I nomi dei partiti stanno scritti come sul Televideo, con l'apostrofo al
    posto dell'accento ("Unita'"). In una frase vera l'accento ci vuole."""
    return re.sub(r"([aeiou])'(?=\s|$|,)",
                  lambda m: {'a': 'à', 'e': 'è', 'i': 'ì', 'o': 'ò', 'u': 'ù'}[m.group(1)],
                  testo)


def data_estesa(s, prec):
    if not s:
        return None
    if prec == 'anno' or len(s) == 4:
        return s[:4]
    mese = MESI[int(s[5:7]) - 1]
    if prec == 'mese' or len(s) == 7:
        return '%s %s' % (mese, s[:4])
    g = int(s[8:10])
    return '%s %s %s' % ('1º' if g == 1 else g, mese, s[:4])


def eta(p, oggi):
    """Come eta() nel Televideo: con il solo anno si fa conto sul primo luglio."""
    if not p['b']:
        return None
    norm = lambda s: s if len(s) >= 10 else s[:4] + '-07-01'
    fine = norm(p['d']) if p['d'] else oggi
    nas = norm(p['b'])
    a = int(fine[:4]) - int(nas[:4])
    if fine[5:10] < nas[5:10]:
        a -= 1
    return a


def titolo_scheda(p):
    """Neutro, e uguale a titoloScheda() nel Televideo."""
    a = (p['b'] or '')[:4]
    if p['s'] == 2:
        return '%s (%s–%s)' % (p['n'], a or '?', (p['d'] or '')[:4] or '?')
    return '%s%s, %s' % (p['n'], ' (%s)' % a if a else '',
                         'vivente' if p['s'] == 1 else 'sorte ignota')


def legislature_in_chiaro(p):
    leg = [m for m in p['m'] if not m.startswith('Governo')]
    gov = [m[len('Governo '):] for m in p['m'] if m.startswith('Governo')]
    frasi = []
    if len(leg) == 1:
        frasi.append("Nell'Assemblea Costituente." if leg[0] == 'Costituente'
                     else 'In Parlamento nella %s legislatura.' % leg[0])
    elif leg:
        frasi.append('In Parlamento per %d legislature, dalla %s alla %s.'
                     % (len(leg), leg[0], leg[-1]))
    if len(gov) == 1:
        frasi.append('Nel governo %s.' % gov[0])
    elif gov:
        frasi.append('Nei governi %s.' % ' e '.join(gov))
    return ' '.join(frasi)


def partito_in_chiaro(p, nomi):
    if not p['p']:
        return ''
    return accenta(nomi.get(p['p'], p['p'])) + '.'


def descrizione_scheda(p, nomi, oggi):
    """Una riga che dica subito quello che si cerca. Senza aggettivi al
    maschile o al femminile: il sesso nei dati non c'e', e 'deceduto' detto
    di Nilde Iotti sarebbe sbagliato."""
    nascita = data_estesa(p['b'], p['bp'])
    anni = eta(p, oggi)
    if p['s'] == 1:
        apertura = '%s%s è in vita%s.' % (
            p['n'], ' (%s)' % nascita if nascita else '',
            ' e ha %d anni' % anni if anni is not None else '')
    elif p['s'] == 2:
        morte = data_estesa(p['d'], p['dp'])
        apertura = '%s (%s – %s)%s.' % (
            p['n'], nascita or '?', morte or '?',
            ' ha vissuto %d anni' % anni if anni is not None and morte else '')
    else:
        apertura = ('%s%s: le fonti non ne registrano la morte, ma non sanno '
                    'dire se sia ancora in vita.'
                    % (p['n'], ' (%s)' % nascita if nascita else ''))
    governo = ''
    anni_gov = sorted(a for c in p.get('gv', []) for a in (c[1], c[2]) if a)
    if anni_gov:
        governo = ('Incarichi di governo nel %s.' % anni_gov[0] if anni_gov[0] == anni_gov[-1]
                   else 'Incarichi di governo dal %s al %s.' % (anni_gov[0], anni_gov[-1]))
    studi = (p['st'].rstrip('.') + '.') if p.get('st') else ''
    if p.get('pf'):
        # il risultato migliore: e' il numero che chi cerca vuole sapere
        leg, voti = max(p['pf'], key=lambda x: x[1])
        anno = ANNI_ELEZIONE.get(leg, '')
        governo = (governo + ' ' if governo else '') + \
            'Record personale: %s preferenze nel %s.' % (format(voti, ',').replace(',', '.'), anno)
    return ' '.join(x for x in (apertura, partito_in_chiaro(p, nomi),
                                legislature_in_chiaro(p), governo, studi) if x)


# ------------------------------------------------------------ le schermate

def schermate(dati):
    """Tutte le pagine da scrivere: (indirizzo, numero o None, titolo,
    descrizione, persona o None). Il titolo e' senza il nome del sito."""
    P = dati['persone']
    nomi = dati['nomi_partiti']
    oggi = dati['generato']
    viventi = [p for p in P if p['s'] == 1]
    defunti = [p for p in P if p['s'] == 2]
    hof = [p for p in P if p.get('h')]
    n_tot = format(len(P), ',').replace(',', '.')
    esteso = lambda s: accenta(nomi.get(s, s))
    fuori = []

    def pagina(num, titolo, descrizione):
        fuori.append((PAGINE[num], num, titolo, descrizione, None))

    pagina(101, 'I parlamentari della Prima Repubblica ancora vivi',
           'I %d parlamentari e ministri della Prima Repubblica ancora in vita, dal più '
           'anziano. Si aggiorna ogni giorno con i dati di Camera e Senato.' % len(viventi))
    pagina(110, 'Le legislature della Prima Repubblica: quanti sono ancora vivi',
           'Dalla Costituente all’XI legislatura: per ognuna, quanti dei suoi '
           'parlamentari sono ancora in vita.')
    for i, (L, anni) in enumerate(dati['legislature']):
        gente = [p for p in P if L in p['m']]
        vivi = sum(1 for p in gente if p['s'] == 1)
        if L == 'Costituente':
            nome, chi = 'Assemblea Costituente (%s)' % anni, 'membri dell’Assemblea Costituente'
        elif L.startswith('Governo'):
            nome = '%s (%s)' % (L, anni)
            chi = 'membri del governo %s' % L[len('Governo '):]
        else:
            nome = '%s legislatura (%s)' % (L, anni)
            chi = 'parlamentari della %s legislatura' % L
        num = 111 + i
        PAGINE[num] = '/legislature/%s/' % scheggia(L)
        resto = ('non ne resta in vita nessuno' if not vivi
                 else 'ne resta in vita uno solo' if vivi == 1
                 else 'ne sono ancora in vita %d' % vivi)
        pagina(num, '%s: chi è ancora vivo' % nome,
               'Dei %d %s %s. L’elenco completo, dal più anziano.'
               % (len(gente), chi, resto))
    hof_vivi = sum(1 for p in hof if p['s'] == 1)
    pagina(130, 'Hall of fame: i %d protagonisti della Prima Repubblica' % len(hof),
           'La lista curata a mano da cui è nato il sito: %d nomi fra ministri, '
           'segretari di partito, sindacalisti e banchieri. Ancora in vita: %d.'
           % (len(hof), hof_vivi))
    pagina(131, 'Hall of fame: ancora in piedi',
           'I %d della hall of fame ancora in vita, dal più anziano.' % hof_vivi)
    pagina(132, 'Hall of fame: in memoriam',
           'I %d della hall of fame che non ci sono più, dal più recente.'
           % sum(1 for p in hof if p['s'] == 2))
    pagina(133, 'Hall of fame per partito',
           'I %d della hall of fame divisi per partito, e quanti ne restano.' % len(hof))
    pagina(134, 'Hall of fame: compleanni',
           'I prossimi compleanni fra i protagonisti della hall of fame ancora in vita.')
    pagina(135, 'Hall of fame: chi ha avuto più incarichi',
           'I protagonisti della Prima Repubblica che hanno occupato più poltrone.')
    camera_luoghi = eletti_per_luogo(P, 'C')
    senato_luoghi = eletti_per_luogo(P, 'S')
    pagina(290, 'Le circoscrizioni della Camera: chi è ancora vivo fra gli eletti',
           'Per ognuna delle %d circoscrizioni della Camera, dalla Costituente al 1994, '
           'quanti deputati vi furono eletti e quanti sono ancora in vita.'
           % len(camera_luoghi))
    pagina(295, 'Le regioni del Senato: chi è ancora vivo fra gli eletti',
           'Per ognuna delle %d regioni del Senato, dal 1948 al 1994, quanti senatori '
           'vi furono eletti e quanti sono ancora in vita.' % len(senato_luoghi))
    pagina(150, 'Cerca un parlamentare della Prima Repubblica',
           'Cerca per nome fra i %s parlamentari e ministri della Prima Repubblica.' % n_tot)
    pagina(200, 'Statistiche: età, decano e sopravvissuti della Prima Repubblica',
           'Quanti sono ancora vivi, l’età media, il decano, i morti degli ultimi '
           'dodici mesi, fra i %s parlamentari della Prima Repubblica.' % n_tot)
    pagina(210, 'Parlamentari della Prima Repubblica ancora vivi, per partito',
           'Quanti parlamentari e ministri della Prima Repubblica restano, partito per partito.')
    pagina(220, 'Curva di estinzione: i morti di ogni anno',
           'Quanti parlamentari della Prima Repubblica sono morti, anno per anno, '
           'negli ultimi sedici anni.')
    pagina(230, 'L’ultimo di ogni legislatura della Prima Repubblica',
           'Per ogni legislatura, quanti sono ancora vivi o, se non ne resta nessuno, '
           'chi è stato l’ultimo.')
    pagina(240, 'L’ultimo di ogni partito della Prima Repubblica',
           'Per ogni partito della Prima Repubblica, quanti eletti sono ancora vivi o, '
           'se non ne resta nessuno, chi è stato l’ultimo.')
    pagina(250, 'I parlamentari della Prima Repubblica con più legislature',
           'La classifica di chi è stato eletto più volte, dalla Costituente all’XI '
           'legislatura.')
    pagina(260, 'I parlamentari della Prima Repubblica che non ci sono più',
           'Età media alla morte, il più longevo e il più giovane fra i %d '
           'parlamentari della Prima Repubblica scomparsi.' % len(defunti))
    pagina(261, 'Parlamentari della Prima Repubblica scomparsi, per partito',
           'Quanti parlamentari e ministri della Prima Repubblica non ci sono più, '
           'partito per partito.')
    pagina(270, 'I parlamentari della Prima Repubblica con più incarichi',
           'La classifica di chi ha occupato più poltrone: ministeri, sottosegretariati, '
           'presidenze delle Camere, delle commissioni e dei gruppi parlamentari.')
    pagina(280, 'I parlamentari più votati della Prima Repubblica',
           'La classifica dei voti di preferenza alla Camera dal 1948 al 1992, elezione '
           'per elezione: da Andreotti a Moro, da Berlinguer a Rumor.')
    pagina(285, 'I parlamentari nella lista P2: chi è ancora vivo',
           'I parlamentari della Prima Repubblica il cui nome compare nella lista della '
           'loggia P2 sequestrata a Castiglion Fibocchi nel 1981: chi c’è ancora e chi no.')
    pagina(300, 'In memoriam: i parlamentari della Prima Repubblica scomparsi',
           'I %d parlamentari e ministri della Prima Repubblica che non ci sono più, '
           'dal più recente.' % len(defunti))
    pagina(400, 'Sorte ignota: parlamentari di cui non si sa se siano vivi',
           'Parlamentari della Prima Repubblica di cui nessuna fonte registra la morte, '
           'ma che avrebbero un’età difficile da credere.')
    pagina(500, 'Compleanni dei parlamentari della Prima Repubblica',
           'Chi compie gli anni oggi e nei prossimi giorni, fra i parlamentari e i '
           'ministri della Prima Repubblica ancora in vita.')
    pagina(600, 'Ricontrolla ora chi è ancora vivo',
           'Rilegge lo stato dei viventi su Wikidata e sul registro della Camera.')
    pagina(700, 'Info su Prima Repubblica Tracker',
           'Chi fa il sito, da dove nasce, da quali fonti vengono i dati e come si '
           'possono riusare.')

    # gli elenchi per partito, legislatura, anno: quelli che esistono davvero
    def elenco(tipo, valore, titolo, descrizione):
        fuori.append((ELENCHI[tipo] + scheggia(valore) + '/', None, titolo, descrizione, None))

    def per_sigla(gente):
        conta = {}
        for p in gente:
            if p['p']:
                conta.setdefault(p['p'], []).append(p)
        return conta

    for s, gente in sorted(per_sigla(viventi).items()):
        elenco('partito', s, '%s (%s): chi è ancora vivo' % (esteso(s), s),
               'Partito: %s. I %d parlamentari e ministri della Prima Repubblica '
               'ancora in vita, dal più anziano.' % (esteso(s), len(gente)))
    for s, gente in sorted(per_sigla(defunti).items()):
        elenco('mortipartito', s, '%s (%s): i parlamentari scomparsi' % (esteso(s), s),
               'Partito: %s. I %d parlamentari e ministri della Prima Repubblica che '
               'non ci sono più, dal più recente.' % (esteso(s), len(gente)))
    for s, gente in sorted(per_sigla([p for p in hof if p['s'] == 1]).items()):
        elenco('hof', s, 'Hall of fame, %s: chi è ancora vivo' % esteso(s),
               'I protagonisti della hall of fame eletti con %s ancora in vita.' % esteso(s))
    for L, anni in dati['legislature']:
        vivi = [p for p in viventi if L in p['m']]
        if vivi:
            nome = ('Assemblea Costituente' if L == 'Costituente'
                    else L if L.startswith('Governo') else '%s legislatura' % L)
            elenco('mandato', L, '%s (%s): i sopravvissuti' % (nome, anni),
                   '%s (%s): i %d ancora in vita, dal più anziano.' % (nome, anni, len(vivi)))
    def resto(vivi):
        return ('non ne resta in vita nessuno' if not vivi
                else 'ne resta in vita uno solo' if vivi == 1
                else 'ne sono ancora in vita %d' % vivi)

    for luogo, gente in sorted(camera_luoghi.items()):
        vivi = sum(1 for p in gente if p['s'] == 1)
        # il collegio dei resti nazionali non e' un territorio
        nome = luogo if luogo.startswith('Collegio') else 'Circoscrizione di ' + luogo
        dove = 'nel collegio unico nazionale' if luogo.startswith('Collegio') \
            else 'nella circoscrizione di ' + luogo
        elenco('circ', luogo, '%s: deputati della Prima Repubblica ancora vivi' % nome,
               'Dei %d deputati eletti %s dalla Costituente al 1994 %s. L’elenco completo, '
               'dal più anziano.' % (len(gente), dove, resto(vivi)))
    for luogo, gente in sorted(senato_luoghi.items()):
        vivi = sum(1 for p in gente if p['s'] == 1)
        elenco('reg', luogo, 'Senatori eletti in %s nella Prima Repubblica: chi è ancora vivo'
               % luogo,
               'Dei %d senatori eletti in %s dal 1948 al 1994 %s. L’elenco completo, '
               'dal più anziano.' % (len(gente), luogo, resto(vivi)))

    per_anno = {}
    for p in defunti:
        if p['d']:
            per_anno.setdefault(p['d'][:4], []).append(p)
    for a, gente in sorted(per_anno.items()):
        elenco('morti', a, 'Parlamentari della Prima Repubblica morti nel %s' % a,
               'I %d parlamentari e ministri della Prima Repubblica morti nel %s.'
               % (len(gente), a))

    for p in P:
        fuori.append(('/onorevole/%s/' % p['u'], None, titolo_scheda(p),
                      descrizione_scheda(p, nomi, oggi), p))
    return fuori


# ------------------------------------------------------------ la testa

def testa(indirizzo, titolo, descrizione, persona, dati, extra_home):
    url = INDIRIZZO + indirizzo
    e = lambda s: html.escape(s, quote=True)
    righe = ['<link rel="canonical" href="%s">' % e(url)]
    if persona:
        p = persona
        individuo = {'@type': 'Person', 'name': p['n'],
                     'sameAs': ['https://www.wikidata.org/wiki/' + p['q']]}
        if p.get('w'):
            individuo['sameAs'].append(p['w'])
        if p['b']:
            individuo['birthDate'] = p['b']
        if p['d']:
            individuo['deathDate'] = p['d']
        if p.get('f'):
            individuo['image'] = p['f']
        if p.get('g') == 'f':
            individuo['gender'] = 'Female'
        grafo = {'@context': 'https://schema.org', '@type': 'ProfilePage',
                 'url': url, 'name': titolo, 'inLanguage': 'it-IT',
                 'dateModified': dati['generato'],
                 'isPartOf': {'@id': INDIRIZZO + '/#sito'},
                 'mainEntity': individuo}
        righe.append('<script type="application/ld+json">%s</script>'
                     % json.dumps(grafo, ensure_ascii=False, separators=(',', ':'))
                     .replace('</', '<\\/'))
    if extra_home:
        righe.append(extra_home)
    return '\n'.join(righe)


def anteprima(indirizzo, titolo, descrizione, num):
    e = lambda s: html.escape(s, quote=True)
    righe = ['<meta name="description" content="%s">' % e(descrizione)]
    if num in FUORI_DAI_MOTORI:
        righe.append('<meta name="robots" content="noindex">')
    righe += [
        '<meta property="og:type" content="website">',
        '<meta property="og:locale" content="it_IT">',
        '<meta property="og:site_name" content="%s">' % SITO,
        '<meta property="og:title" content="%s">' % e(titolo),
        '<meta property="og:description" content="%s">' % e(descrizione),
        '<meta property="og:url" content="%s">' % e(INDIRIZZO + indirizzo),
        # JPEG con nome nuovo e tipo dichiarato: vedi ANTEPRIMA_TRACKER in
        # genera_sito.py, e' quello che fa funzionare WhatsApp.
        '<meta property="og:image" content="%s/preview.jpg">' % INDIRIZZO,
        '<meta property="og:image:secure_url" content="%s/preview.jpg">' % INDIRIZZO,
        '<meta property="og:image:type" content="image/jpeg">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="Una pagina del Televideo: Prima '
        'Repubblica, chi è ancora vivo e chi no">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:image" content="%s/preview.jpg">' % INDIRIZZO,
        # L'icona come file vero, per Google: quella incorporata (data:) nei
        # risultati di ricerca la ignora e mette il mappamondo grigio. I file
        # stanno nello specchio, prima-repubblica-tracker/sito/.
        '<link rel="icon" href="https://primarepubblica.net/favicon.ico" sizes="48x48">',
        '<link rel="icon" type="image/png" sizes="96x96" href="https://primarepubblica.net/favicon-96.png">',
        '<link rel="icon" type="image/png" sizes="192x192" href="https://primarepubblica.net/favicon-192.png">',
        '<link rel="apple-touch-icon" href="https://primarepubblica.net/apple-touch-icon.png">',
    ]
    return '\n'.join(righe)


# ------------------------------------------------------------ il montaggio

def scomponi(scheletro):
    """Separa dal modello gia' riempito il foglio di stile e il programma, che
    diventano due file comuni a tutte le pagine."""
    i = scheletro.index('<style>')
    j = scheletro.index('</style>', i) + len('</style>')
    stile = scheletro[i + len('<style>'):j - len('</style>')]
    a = scheletro.index('<script>\nconst DATI')
    b = scheletro.rindex('</script>')
    programma = scheletro[a + len('<script>'):b]
    involucro = (scheletro[:i] + '<!--%%STILE%%-->' + scheletro[j:a]
                 + '<!--%%PROGRAMMA%%-->' + scheletro[b + len('</script>'):])
    return involucro, stile.strip('\n') + '\n', programma.strip('\n') + '\n'


def costruisci(scheletro, dati, home, uscita_archivio, titoli_proposte=None):
    """scheletro: il modello con dati, testata, colofone e presentazione gia'
    al loro posto, e ancora da riempire titolo, testa, anteprima, intestazione.
    home: (titolo, descrizione, dati strutturati) della pagina principale.
    Scrive l'archivio e restituisce il numero di pagine."""
    involucro, stile, programma = scomponi(scheletro)
    v = dati['generato']
    titolo_home, descr_home, strutturati_home = home

    # Al programma la tabella degli indirizzi e i titoli arrivano con i dati.
    # I titoli delle schede il Televideo li compone da solo (titoloScheda):
    # portarseli dietro tutti peserebbe quanto mezzo elenco.
    elenco_schermate = schermate(dati)
    titoli = {'/': titolo_home}
    for indirizzo, num, titolo, descrizione, persona in elenco_schermate:
        if not persona:
            titoli[indirizzo] = '%s | %s' % (titolo, SITO)
    programma = programma.replace(
        '"__INDIRIZZI__":null',
        '"indirizzi":' + json.dumps({'pagine': {str(k): x for k, x in PAGINE.items()},
                                     'elenchi': ELENCHI, 'titoli': titoli},
                                    ensure_ascii=False, separators=(',', ':')), 1)
    if '"indirizzi":' not in programma:
        raise SystemExit('Nel programma manca il posto per la tabella degli indirizzi.')

    # Il richiamo ai due file comuni cambia quando cambia il loro contenuto,
    # non la data: anche una correzione fatta in giornata arriva subito a chi
    # ha gia' in memoria la copia vecchia.
    impronta = lambda s: hashlib.sha1(s.encode('utf-8')).hexdigest()[:10]
    involucro = (involucro
                 .replace('<!--%%STILE%%-->',
                          '<link rel="stylesheet" href="/stile.css?v=%s">' % impronta(stile))
                 .replace('<!--%%PROGRAMMA%%-->',
                          # il segno "generato" serve al controllo di versione
                          # del Televideo e alle verifiche del sito specchio
                          '<script>var PAGINA = {"generato":"%s"};</script>\n'
                          '<script src="/televideo.js?v=%s"></script>'
                          % (v, impronta(programma))))
    e = lambda s: html.escape(s, quote=True)

    def monta(indirizzo, num, titolo_pieno, descrizione, persona, h1, extra_home=''):
        return (involucro
                .replace('%%TITOLO%%', e(titolo_pieno))
                .replace('<!--%%CANONICO%%-->',
                         testa(indirizzo, titolo_pieno, descrizione, persona, dati, extra_home))
                .replace('<!--%%ANTEPRIMA%%-->',
                         anteprima(indirizzo, titolo_pieno, descrizione, num))
                .replace('<!--%%INTESTAZIONE%%-->',
                         '<h1 class="solo-lettori">%s</h1>' % e(h1)))

    file = {}
    file['index.html'] = monta('/', 100, titolo_home, descr_home, None,
                               'Prima Repubblica Tracker: chi è ancora vivo fra i '
                               'parlamentari della Prima Repubblica',
                               strutturati_home)
    mappa = ['/']
    for indirizzo, num, titolo, descrizione, persona in elenco_schermate:
        pieno = '%s | %s' % (titolo, SITO)
        file[indirizzo.strip('/') + '/index.html'] = monta(
            indirizzo, num, pieno, descrizione, persona, titolo)
        if num not in FUORI_DAI_MOTORI:
            mappa.append(indirizzo)

    # Per un indirizzo che non esiste GitHub Pages serve 404.html: e' il
    # Televideo stesso, che legge l'indirizzo e, se lo riconosce (un elenco per
    # un partito che oggi non ha pagina), apre la schermata giusta.
    pagina_404 = monta('/', 0, SITO, descr_home, None, SITO)
    pagina_404 = re.sub(r'<link rel="canonical"[^>]*>\n?', '', pagina_404)
    file['404.html'] = pagina_404.replace(
        '<meta name="description"', '<meta name="robots" content="noindex">\n'
        '<meta name="description"', 1)

    # l'elenco delle proposte di legge, un file per scheda
    for p in dati['persone']:
        if titoli_proposte and p['q'] in titoli_proposte:
            file['onorevole/%s/proposte.json' % p['u']] = json.dumps(
                titoli_proposte[p['q']], ensure_ascii=False, separators=(',', ':'))

    file['stile.css'] = stile
    file['televideo.js'] = programma

    # La mappa del sito: tutte le pagine da far trovare. La data c'e' solo
    # sull'indice, l'unica pagina che cambia davvero ogni giorno: una data
    # uguale su cinquemila pagine Google impara presto a non crederci.
    voci = []
    for x in mappa:
        voci.append('  <url><loc>%s%s</loc>%s</url>' % (
            INDIRIZZO, html.escape(x),
            '<lastmod>%s</lastmod>' % v if x == '/' else ''))
    file['sitemap.xml'] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                           + '\n'.join(voci) + '\n</urlset>\n')

    os.makedirs(os.path.dirname(uscita_archivio), exist_ok=True)
    with tarfile.open(uscita_archivio, 'w:gz') as tar:
        for nome in sorted(file):
            dati_file = file[nome].encode('utf-8')
            info = tarfile.TarInfo(nome)
            info.size = len(dati_file)
            info.mode = 0o644
            info.mtime = 0
            tar.addfile(info, io.BytesIO(dati_file))
    return len(file), len(mappa)
