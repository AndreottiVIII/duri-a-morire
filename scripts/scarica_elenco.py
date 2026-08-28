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
    if p['morte']:
        return 'deceduto'
    if not p['nascita']:
        return 'ignoto'
    if oggi.year - int(p['nascita'][:4]) > ETA_MASSIMA_CREDIBILE:
        return 'ignoto'
    return 'vivente'


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
    for etichetta, modulo in [('Camera dei deputati', camera), ('Senato', senato)]:
        print('Incrocio con gli open data: %s...' % etichetta)
        try:
            registro = modulo.decessi()
        except Exception as e:
            print('  non raggiungibile (%s): si prosegue senza.' % e)
            continue
        recuperati = 0
        for p in persone.values():
            if p['morte']:
                continue
            v = registro.get(camera.chiave(p['nome'], ''))
            # L'anno di nascita deve coincidere, altrimenti si finisce per
            # seppellire un vivo al posto del suo omonimo deputato del Regno.
            if not v or not v['nascita'] or not p['nascita']:
                continue
            if v['nascita'][:4] != p['nascita'][:4]:
                continue
            p['morte'] = v['morte']
            p['prec_morte'] = 'giorno' if len(v['morte']) == 10 else 'anno'
            p['fonte_morte'] = etichetta
            recuperati += 1
        print('  %d decessi che Wikidata non registrava' % recuperati)

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
