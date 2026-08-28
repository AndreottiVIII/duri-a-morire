# -*- coding: utf-8 -*-
"""Scarica da Wikidata l'elenco grande: Costituente, legislature I-XI,
piu' i ministri dei governi Ciampi e Dini anche se mai eletti.

Le date arrivano con la loro precisione: su Wikidata un anno secco viene
servito come 1 gennaio, e preso alla lettera produrrebbe compleanni inventati.
"""
import sys, os, json, time, datetime, re, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wd, camera, senato

QUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(QUI, '..', 'data', 'cache')
USCITA = os.path.join(QUI, '..', 'data', 'elenco.json')

# Soglia oltre la quale un vivente senza data di morte e' un buco nei dati.
ETA_MASSIMA_CREDIBILE = 106

COSTITUENTE = ('Costituente', 'Q3705737', '1946-1948')

LEGISLATURE = [
    ('I',    'Q3790289', '1948-1953'), ('II',   'Q3788583', '1953-1958'),
    ('III',  'Q3788564', '1958-1963'), ('IV',   'Q3789944', '1963-1968'),
    ('V',    'Q4007102', '1968-1972'), ('VI',   'Q4007008', '1972-1976'),
    ('VII',  'Q4006990', '1976-1979'), ('VIII', 'Q4006975', '1979-1983'),
    ('IX',   'Q3790001', '1983-1987'), ('X',    'Q4021692', '1987-1992'),
    ('XI',   'Q4021369', '1992-1994'),
]

GOVERNI = [('Ciampi', 'Q2237427', '1993-1994'), ('Dini', 'Q2294580', '1995-1996')]

DATE = """
  OPTIONAL { ?p p:P569/psv:P569 [ wikibase:timeValue ?nascita ; wikibase:timePrecision ?precN ] }
  OPTIONAL { ?p p:P570/psv:P570 [ wikibase:timeValue ?morte   ; wikibase:timePrecision ?precM ] }
  OPTIONAL { ?p wdt:P18 ?foto }
  OPTIONAL { ?art schema:about ?p ; schema:isPartOf <https://it.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
"""

Q_LEGISLATURA = """SELECT ?p ?pLabel ?nascita ?precN ?morte ?precM ?foto ?art ?posLabel WHERE {
  ?p p:P39 ?st . ?st ps:P39 ?pos ; pq:P2937 wd:%s .
""" + DATE + "}"

Q_COSTITUENTE = """SELECT ?p ?pLabel ?nascita ?precN ?morte ?precM ?foto ?art ?posLabel WHERE {
  ?p p:P39 ?st . ?st ps:P39 ?pos . VALUES ?pos { wd:%s }
""" + DATE + "}"

Q_GOVERNO = """SELECT ?p ?pLabel ?nascita ?precN ?morte ?precM ?foto ?art ?posLabel WHERE {
  ?p p:P39 ?st . ?st ps:P39 ?pos .
  { ?st pq:P5054 wd:%(g)s } UNION { ?st pq:P642 wd:%(g)s } UNION { ?st pq:P361 wd:%(g)s }
""" + DATE + "}"

Q_PARTITI = """SELECT ?p ?partitoLabel WHERE {
  ?p p:P39 ?st . ?st pq:P2937 wd:%s . ?p wdt:P102 ?partito .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}"""


# Le risposte restano su disco per non ribussare a Wikidata dodici volte di
# fila, ma scadono: una cache eterna farebbe girare a vuoto il lavoro notturno,
# che si aggiornerebbe solo in apparenza.
SCADENZA_ORE = 12
FRESCO = '--fresco' in sys.argv


def cache_o_query(nome, query):
    os.makedirs(CACHE, exist_ok=True)
    f = os.path.join(CACHE, nome + '.json')
    if os.path.exists(f) and not FRESCO:
        eta_ore = (time.time() - os.path.getmtime(f)) / 3600.0
        if eta_ore < SCADENZA_ORE:
            return json.load(open(f, encoding='utf-8'))
    righe = wd.sparql(query)
    json.dump(righe, open(f, 'w', encoding='utf-8'))
    time.sleep(1)
    return righe


def data(riga, campo, campo_prec):
    """Ritorna (testo, precisione) rispettando la precisione dichiarata."""
    t = wd.v(riga, campo)
    if not t:
        return None, None
    prec = int(wd.v(riga, campo_prec) or 11)
    anno, mese, giorno = t[0:4], t[5:7], t[8:10]
    if prec >= 11:
        return '%s-%s-%s' % (anno, mese, giorno), 'giorno'
    if prec == 10:
        return '%s-%s' % (anno, mese), 'mese'
    return anno, 'anno'


def assorbi(persone, righe, etichetta_mandato):
    for r in righe:
        q = wd.qid(r, 'p')
        if not q:
            continue
        p = persone.setdefault(q, {
            'qid': q, 'nome': None, 'nascita': None, 'prec_nascita': None,
            'morte': None, 'prec_morte': None, 'foto': None, 'wikipedia': None,
            'mandati': [], 'cariche': set(), 'partiti': set()})
        p['nome'] = p['nome'] or wd.v(r, 'pLabel')
        n, pn = data(r, 'nascita', 'precN')
        if n and not p['nascita']:
            p['nascita'], p['prec_nascita'] = n, pn
        m, pm = data(r, 'morte', 'precM')
        if m and not p['morte']:
            p['morte'], p['prec_morte'] = m, pm
        p['foto'] = p['foto'] or wd.v(r, 'foto')
        p['wikipedia'] = p['wikipedia'] or wd.v(r, 'art')
        if etichetta_mandato not in p['mandati']:
            p['mandati'].append(etichetta_mandato)
        pos = wd.v(r, 'posLabel')
        if pos:
            p['cariche'].add(pos)


def nome_leggibile(p, curato):
    """Quando su Wikidata manca l'etichetta, il servizio restituisce il codice
    (un 'Q2460954' al posto di Giorgio La Malfa). Si ripiega sul nome curato a
    mano, e in mancanza di quello sul titolo della voce di Wikipedia."""
    if not re.match(r'^Q\d+$', p['nome'] or ''):
        return p['nome']
    if curato and curato.get('nome'):
        return curato['nome']
    if p.get('wikipedia'):
        titolo = urllib.parse.unquote(p['wikipedia'].rsplit('/', 1)[-1]).replace('_', ' ')
        return re.sub(r'\s*\([^)]*\)$', '', titolo)  # via il "(politico)"
    return p['nome']


def stato_di(p, oggi):
    """Vivente, deceduto, o sorte ignota.

    Chi supera l'eta' massima credibile senza che ne' Wikidata ne' i registri
    di Camera e Senato ne segnino la morte non e' un vivente: e' un morto di
    cui nessuno ha scritto la data. Tre fonti che tacciono su un uomo di
    centoventiquattro anni non lasciano molto spazio al dubbio, e tenerlo fra
    i vivi falserebbe ogni conto. La data resta ignota, e la scheda lo dice.

    Nessuna delle tre fonti li da' per morti, e nessuna delle tre puo' dirlo:
    la data non esiste da nessuna parte, nemmeno la voce di Wikipedia di Enrico
    Parri sa cosa scrivere dopo il trattino. Si potrebbe presumere la morte a
    centoventiquattro anni, ma sarebbe una nostra deduzione spacciata per un
    fatto: meglio il limbo dichiarato, che e' la verita' sui dati.
    """
    if p['morte']:
        return 'deceduto'
    if not p['nascita']:
        return 'ignoto'
    if oggi.year - int(p['nascita'][:4]) > ETA_MASSIMA_CREDIBILE:
        return 'ignoto'
    return 'vivente'


Q_CARICHE = """SELECT ?p ?posLabel ?inizio ?fine WHERE {
  VALUES ?p { %s }
  ?p p:P39 ?st . ?st ps:P39 ?pos .
  OPTIONAL { ?st pq:P580 ?inizio }
  OPTIONAL { ?st pq:P582 ?fine }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}"""

# Il seggio non e' una carica: i mandati hanno gia' la loro riga.
SEGGI = ('deputato', 'senatore', 'membro del parlamento', 'member of')

CODE_INUTILI = (' della repubblica italiana', ' della repubblica',
                " del regno d'italia", ' italiano', ' italiana')


def ripulisci_carica(etichetta):
    """'ministro della difesa della Repubblica Italiana' -> 'Ministro della difesa'."""
    e = (etichetta or '').strip()
    basso = e.lower()
    for coda in CODE_INUTILI:
        if basso.endswith(coda):
            tagliato = e[:len(e) - len(coda)]
            # 'presidente della Repubblica Italiana' non puo' diventare
            # 'Presidente': senza il seguito la carica non vuol dire niente.
            e = tagliato if len(tagliato.split()) >= 2 else tagliato + ' della Repubblica'
            break
    return e[:1].upper() + e[1:] if e else e


def scarica_cariche(persone, quali):
    """Le cariche datate, prese da Wikidata per chi sta in hall of fame.

    Il cursus scritto a mano e' una sintesi, e le sintesi perdono pezzi: a
    Sergio Mattarella mancavano la vicepresidenza del Consiglio, la Difesa e
    la Consulta. Qui l'elenco arriva completo e con gli anni.
    """
    lista = [q for q in quali if q in persone]
    righe = []
    for i in range(0, len(lista), 60):
        blocco = ' '.join('wd:' + q for q in lista[i:i + 60])
        righe += cache_o_query('cariche_%d' % i, Q_CARICHE % blocco)

    grezze = {}
    for r in righe:
        q = wd.qid(r, 'p')
        etichetta = wd.v(r, 'posLabel')
        if not q or not etichetta or etichetta.lower().startswith(SEGGI):
            continue
        da = (wd.v(r, 'inizio') or '')[:4]
        a = (wd.v(r, 'fine') or '')[:4]
        grezze.setdefault(q, {}).setdefault(ripulisci_carica(etichetta), []).append((da, a))

    for q, cariche in grezze.items():
        fuori = []
        for etichetta, periodi in cariche.items():
            anni = sorted(x for coppia in periodi for x in coppia if x)
            fuori.append({'carica': etichetta,
                          'da': anni[0] if anni else None,
                          'a': anni[-1] if anni and any(p[1] for p in periodi) else None})
        fuori.sort(key=lambda c: c['da'] or '9999')
        persone[q]['cariche_datate'] = fuori
    print('  cariche ricostruite per %d persone' % len(grezze))


def leggi_json(nome):
    percorso = os.path.join(QUI, '..', 'data', nome)
    if not os.path.exists(percorso):
        return {}
    return {k: v for k, v in json.load(open(percorso, encoding='utf-8')).items()
            if not k.startswith('_')}


def fondi_doppioni(persone):
    """Stesso nome e stessa legislatura vuol dire stessa persona.

    Su Wikidata capita che una persona compaia due volte, una col suo record
    completo e una con una scheda spoglia e una data di nascita sbagliata: di
    Giovanni Battista Melis, deputato sardo morto nel 1976, esisteva un secondo
    esemplare nato nel 1922 che nessuno aveva mai fatto morire. Restava fra i
    viventi in eterno.

    Persone diverse con lo stesso nome esistono davvero (due Giuseppe Leoni,
    due Arturo Marzano), ma stanno in legislature diverse: e' la legislatura
    condivisa a fare la differenza fra un'omonimia e un doppione.
    """
    per_nome = {}
    for q, p in persone.items():
        per_nome.setdefault(camera.chiave(p['nome']), []).append(q)

    def valore(q):
        p = persone[q]
        return (1 if p.get('wikipedia') else 0, 1 if p.get('morte') else 0,
                len(p['mandati']))

    fusi = []
    for gruppo in per_nome.values():
        if len(gruppo) < 2:
            continue
        for a in list(gruppo):
            for b in list(gruppo):
                if a >= b or a not in persone or b not in persone:
                    continue
                if not set(persone[a]['mandati']) & set(persone[b]['mandati']):
                    continue
                tieni, scarta = sorted([a, b], key=valore, reverse=True)
                buono, altro = persone[tieni], persone[scarta]
                for campo in ('morte', 'prec_morte', 'nascita', 'prec_nascita',
                              'foto', 'wikipedia', 'fonte_morte'):
                    if not buono.get(campo) and altro.get(campo):
                        buono[campo] = altro[campo]
                for m in altro['mandati']:
                    if m not in buono['mandati']:
                        buono['mandati'].append(m)
                buono['cariche'] = sorted(set(buono['cariche']) | set(altro['cariche']))
                buono['partiti'] = sorted(set(buono['partiti']) | set(altro['partiti']))
                fusi.append((altro['nome'], scarta, tieni))
                del persone[scarta]

    print('Doppioni fusi: %d' % len(fusi))
    for nome, scarta, tieni in fusi:
        print('  %-26s %s assorbito in %s' % (nome, scarta, tieni))


def main():
    persone = {}

    print('Costituente...')
    assorbi(persone, cache_o_query('leg_Costituente', Q_COSTITUENTE % COSTITUENTE[1]),
            COSTITUENTE[0])
    print('  %d persone' % len(persone))

    for nome, q, anni in LEGISLATURE:
        print('Legislatura %s (%s)...' % (nome, anni))
        assorbi(persone, cache_o_query('leg_%s' % nome, Q_LEGISLATURA % q), nome)
        print('  totale cumulato: %d' % len(persone))

    eletti = set(persone)

    for nome, q, anni in GOVERNI:
        print('Governo %s...' % nome)
        assorbi(persone, cache_o_query('gov_%s' % nome, Q_GOVERNO % {'g': q}),
                'Governo ' + nome)
        print('  totale cumulato: %d' % len(persone))

    print('Partiti...')
    for nome, q, anni in LEGISLATURE:
        for r in cache_o_query('part_%s' % nome, Q_PARTITI % q):
            qq = wd.qid(r, 'p')
            if qq in persone and wd.v(r, 'partitoLabel'):
                persone[qq]['partiti'].add(wd.v(r, 'partitoLabel'))

    # Comandano i registri ufficiali: chi loro collocano fuori dal perimetro
    # esce, per quanto Wikidata insista. Le ragioni stanno scritte nel file,
    # una per una, perche' togliere qualcuno da un archivio va motivato.
    esclusi = leggi_json('esclusi.json')
    fuori = [q for q in esclusi if q in persone and not q.startswith('_')]
    for q in fuori:
        print('  escluso %s (%s): %s' % (q, persone[q]['nome'], esclusi[q][:60]))
        del persone[q]
    print('Esclusi dal perimetro: %d' % len(fuori))

    hof = {}
    percorso_hof = os.path.join(QUI, '..', 'data', 'hall_of_fame.json')
    if os.path.exists(percorso_hof):
        hof = {x['wikidata']: x for x in json.load(open(percorso_hof, encoding='utf-8'))
               if x.get('wikidata')}

    oggi = datetime.date.today()
    for q, p in persone.items():
        p['nome'] = nome_leggibile(p, hof.get(q))
        p['cariche'] = sorted(p['cariche'])
        p['partiti'] = sorted(p['partiti'])

    # Seconda fonte. Wikidata dimentica i deputati di seconda fila: Giuseppe
    # Sasso risultava vivo a 106 anni ed era morto nel 2015. La Camera tiene il
    # registro dei propri ex deputati e sa quello che Wikidata ignora.
    # Seconda e terza fonte. Wikidata e' cieca sui deputati di seconda fila e
    # non ne registra il decesso: Giuseppe Sasso risultava vivo a 106 anni ed
    # era morto nel 2015. Camera e Senato tengono il registro dei propri ex.
    #
    # L'aggancio e' per nome PIU' legislatura in comune. Mai per data di
    # nascita: e' proprio quella che a volte sbaglia Wikidata, e usarla come
    # prova d'identita' lascerebbe in vita chi ha la data storta. Giovanni
    # Battista Melis su Wikidata e' del 1922, alla Camera del 1904.
    discordanze, contese = [], []
    alias = leggi_json('alias_registri.json')
    for etichetta, modulo in [('Camera dei deputati', camera), ('Senato', senato)]:
        print('Incrocio con gli open data: %s...' % etichetta)
        try:
            reg = modulo.registro()
        except Exception as e:
            print('  non raggiungibile (%s): si prosegue senza.' % e)
            continue
        indice = modulo.indice_per_data(reg)
        per_mandato = modulo.indice_per_mandato(reg)
        recuperati = 0
        for p in persone.values():
            v, come = modulo.cerca_ampia(reg, indice, p['nome'], p['nascita'],
                                         p['mandati'], per_mandato)
            if not v and alias.get(p['qid']):
                # Gianna Schelotto per i registri e' Giovanna Bochicchio.
                v, come = modulo.cerca_ampia(reg, indice, alias[p['qid']],
                                             p['nascita'], p['mandati'], per_mandato)
            if not v:
                continue
            if come == 'data':
                p['aggancio'] = 'data di nascita'
            if v.get('nascita') and p['nascita'] and v['nascita'][:4] != p['nascita'][:4]:
                discordanze.append((p['nome'], p['nascita'], v['nascita'], etichetta))
                # Sulla nascita crediamo al registro ufficiale, non a Wikidata.
                p['nascita'] = v['nascita']
                p['prec_nascita'] = 'giorno' if len(v['nascita']) == 10 else 'anno'
            if v.get('id'):
                p['id_camera'] = v['id']
            if v.get('uri'):
                p['id_senato'] = v['uri']
            if not v.get('morte'):
                continue
            # Sul decesso comanda il registro: e' l'istituzione che certifica
            # i propri ex, mentre Wikidata la scrive chi passa. Si tiene la
            # data di Wikidata solo quando e' piu' precisa e non contraddice.
            if p['morte']:
                if p['morte'][:4] == v['morte'][:4] and len(p['morte']) >= len(v['morte']):
                    continue
                if p['morte'] != v['morte']:
                    contese.append((p['nome'], p['morte'], v['morte'], etichetta))
            else:
                recuperati += 1
            p['morte'] = v['morte']
            p['prec_morte'] = 'giorno' if len(v['morte']) == 10 else 'anno'
            p['fonte_morte'] = etichetta
        print('  %d decessi che Wikidata non registrava' % recuperati)
    print('  %d date di nascita corrette sui registri ufficiali' % len(discordanze))
    print('  %d date di morte corrette sui registri ufficiali' % len(contese))
    for c in contese[:10]:
        print('    %-26s wikidata %s -> %s (%s)' % (c[0], c[1], c[2], c[3]))
    for d in discordanze[:8]:
        print('    %-26s wikidata %s -> %s (%s)' % (d[0], d[1], d[2], d[3]))

    fondi_doppioni(persone)

    print('Cariche della hall of fame...')
    scarica_cariche(persone, list(hof))

    for q, p in persone.items():
        p['stato'] = stato_di(p, oggi)
        p['non_eletto'] = q not in eletti
        p['hall_of_fame'] = q in hof
        if q in hof:
            p['cursus'] = hof[q].get('cursus')
            p['partito_hof'] = hof[q].get('partito')

    # I 66 curati devono esserci tutti: qualcuno non e' mai stato in Parlamento
    # ne' nei governi Ciampi/Dini, e va aggiunto lo stesso, marcato come tale.
    mancanti = [x for x in hof.values() if x['wikidata'] not in persone]
    for x in mancanti:
        nuovo = {
            'qid': x['wikidata'], 'nome': x['etichetta_wd'],
            'nascita': x['nascita_wd'],
            'prec_nascita': 'giorno' if x['nascita_wd'] and len(x['nascita_wd']) == 10 else 'anno',
            'morte': x['morte_wd'],
            'prec_morte': 'giorno' if x['morte_wd'] and len(x['morte_wd']) == 10 else 'anno',
            'foto': ('http://commons.wikimedia.org/wiki/Special:FilePath/' + x['foto'].replace(' ', '_')) if x['foto'] else None,
            'wikipedia': x['wikipedia'], 'mandati': [], 'cariche': [], 'partiti': [],
            'non_eletto': True, 'hall_of_fame': True,
            'cursus': x.get('cursus'), 'partito_hof': x.get('partito')}
        nuovo['stato'] = stato_di(nuovo, oggi)
        persone[x['wikidata']] = nuovo

    elenco = sorted(persone.values(), key=lambda p: (p['nome'] or '').lower())
    json.dump({'generato': oggi.isoformat(),
               'eta_massima_credibile': ETA_MASSIMA_CREDIBILE,
               'persone': elenco},
              open(USCITA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    from collections import Counter
    c = Counter(p['stato'] for p in elenco)
    print()
    print('TOTALE       %d' % len(elenco))
    print('viventi      %d' % c['vivente'])
    print('deceduti     %d' % c['deceduto'])
    print('sorte ignota %d' % c['ignoto'])
    print('non eletti   %d (dentro ma sulla porta)' % sum(1 for p in elenco if p['non_eletto']))
    print('hall of fame %d' % sum(1 for p in elenco if p['hall_of_fame']))
    print('aggiunti fuori perimetro: %d %s' % (len(mancanti), [x['nome'] for x in mancanti]))


if __name__ == '__main__':
    main()
