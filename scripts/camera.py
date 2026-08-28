# -*- coding: utf-8 -*-
"""Seconda fonte: gli open data della Camera dei deputati.

Wikidata e' rapida sui personaggi noti e cieca sui deputati di seconda fila:
di parecchi non registra la morte, e quelli restavano per sempre fra i viventi.
La Camera invece tiene il registro dei propri ex, decessi compresi.

L'aggancio e' per nome PIU' legislatura in comune, mai per data di nascita.
Il solo nome non basta, perche' la Camera arriva fino al Regno e c'e' un
Giuseppe Vacca del 1810. La data di nascita non serve e anzi danneggia, perche'
a volte e' Wikidata a sbagliarla: Giovanni Battista Melis li' risulta del 1922,
alla Camera del 1904, ed e' la Camera ad avere ragione.

Dentro la Camera invece l'aggancio e' esatto: l'URI del deputato per una data
legislatura (d19930_4) contiene l'identificativo della persona (p19930), che
porta le date. Nessuna euristica.
"""
import urllib.request, urllib.parse, json, os, re, sys, time, unicodedata

ENDPOINT = 'https://dati.camera.it/sparql'
QUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(QUI, '..', 'data', 'cache', 'camera_registro.json')

LEGISLATURE = [
    ('Costituente', 'costituente'),
    ('I', 'repubblica_01'), ('II', 'repubblica_02'), ('III', 'repubblica_03'),
    ('IV', 'repubblica_04'), ('V', 'repubblica_05'), ('VI', 'repubblica_06'),
    ('VII', 'repubblica_07'), ('VIII', 'repubblica_08'), ('IX', 'repubblica_09'),
    ('X', 'repubblica_10'), ('XI', 'repubblica_11'),
]

Q_DEPUTATI = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX ocd: <http://dati.camera.it/ocd/>
SELECT DISTINCT ?dep ?cognome ?nome WHERE {
  ?dep a ocd:deputato ;
       ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/%s> ;
       foaf:surname ?cognome ; foaf:firstName ?nome .
}
"""

Q_DECESSI = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX bio: <http://purl.org/vocab/bio/0.1/>
SELECT DISTINCT ?pers ?morte WHERE {
  ?pers a foaf:Person ; bio:Death ?d . ?d bio:date ?morte .
}
"""

# Le nascite vanno chieste per tutti, non solo per i defunti: servono a
# riconoscere i viventi che le due fonti chiamano in modo diverso.
Q_NASCITE = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX bio: <http://purl.org/vocab/bio/0.1/>
SELECT DISTINCT ?pers ?nascita WHERE {
  ?pers a foaf:Person ; bio:Birth ?b . ?b bio:date ?nascita .
}
"""


def interroga(query, tentativi=4):
    ultimo = None
    for i in range(tentativi):
        try:
            u = ENDPOINT + '?' + urllib.parse.urlencode(
                {'query': query, 'format': 'application/sparql-results+json'})
            r = urllib.request.Request(u, headers={
                'User-Agent': 'DuriAMorire/0.1 (progetto personale)',
                'Accept': 'application/sparql-results+json'})
            return json.load(urllib.request.urlopen(r, timeout=300))['results']['bindings']
        except Exception as e:
            ultimo = e
            sys.stderr.write('  ritento (%d): %s\n' % (i + 1, e))
            time.sleep(5 * (i + 1))
    raise ultimo


def chiave(nome, cognome=''):
    """Nome e cognome ridotti all'osso: niente accenti, niente maiuscole,
    ordine indifferente. 'SASSO GIUSEPPE' e 'Giuseppe Sasso' coincidono."""
    s = unicodedata.normalize('NFKD', (nome or '') + ' ' + (cognome or '')).lower()
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return ' '.join(sorted(''.join(c if c.isalnum() else ' ' for c in s).split()))


def data_iso(v):
    """La Camera scrive le date come 20150121, e a volte solo l'anno."""
    v = (v or '').strip()
    if len(v) == 8 and v.isdigit():
        return '%s-%s-%s' % (v[0:4], v[4:6], v[6:8])
    if len(v) == 4 and v.isdigit():
        return v
    return None


def id_persona(uri_deputato):
    """Da .../deputato.rdf/d19930_4 all'identificativo persona 19930."""
    m = re.search(r'/d(\d+)_', uri_deputato or '')
    return m.group(1) if m else None


def registro(usa_cache=True):
    """{chiave nome: {mandato: {'morte':…, 'nascita':…, 'id':…}}}"""
    if usa_cache and os.path.exists(CACHE):
        return json.load(open(CACHE, encoding='utf-8'))

    sys.stderr.write('  decessi registrati...\n')
    def identificativo(r):
        pid = (r['pers']['value'].rsplit('/p', 1) + [''])[1]
        return pid if pid.isdigit() else None

    dati_persona = {}
    for r in interroga(Q_NASCITE):
        pid = identificativo(r)
        if pid:
            dati_persona[pid] = {
                'nascita': data_iso(r.get('nascita', {}).get('value')),
                'morte': None}
    for r in interroga(Q_DECESSI):
        pid = identificativo(r)
        if pid:
            dati_persona.setdefault(pid, {'nascita': None})['morte'] = \
                data_iso(r.get('morte', {}).get('value'))

    fuori = {}
    for mandato, codice in LEGISLATURE:
        righe = interroga(Q_DEPUTATI % codice)
        con_morte = 0
        for r in righe:
            k = chiave(r.get('nome', {}).get('value'), r.get('cognome', {}).get('value'))
            pid = id_persona(r['dep']['value'])
            if not k or not pid:
                continue
            voce = dict(dati_persona.get(pid) or {'morte': None, 'nascita': None})
            voce['id'] = pid
            fuori.setdefault(k, {})[mandato] = voce
            if voce['morte']:
                con_morte += 1
        sys.stderr.write('  %-12s %4d deputati, %4d con data di morte\n'
                         % (mandato, len(righe), con_morte))
        time.sleep(0.5)

    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(fuori, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    return fuori


def indice_per_data(reg):
    """(legislatura, data di nascita) -> voci. Serve a ritrovare chi le due
    fonti chiamano in modo diverso: per la Camera e' VIRGINIO SCOTTI, per
    Wikidata Gerry Scotti, ma la data di nascita e il seggio sono gli stessi."""
    fuori = {}
    for k, voci in reg.items():
        for mandato, v in voci.items():
            if v.get('nascita') and len(v['nascita']) == 10:
                fuori.setdefault((mandato, v['nascita']), []).append((k, v))
    return fuori


def indice_per_mandato(reg):
    """legislatura -> voci, per l'ultimo tentativo a strascico."""
    fuori = {}
    for k, voci in reg.items():
        for mandato, v in voci.items():
            fuori.setdefault(mandato, []).append((k, v))
    return fuori


def cerca_ampia(reg, indice, nome, nascita, mandati, per_mandato=None):
    """Tre tentativi, dal piu' stretto al piu' largo.

    1. nome esatto e legislatura in comune;
    2. legislatura piu' data di nascita esatta, purche' resti almeno un pezzo
       di cognome in comune: senza quel vincolo si accoppierebbe Rosa Russo
       Iervolino col primo Raffaele Russo che passa;
    3. un nome contenuto nell'altro, nella stessa legislatura. Serve ai cognomi
       da sposata, che i registri accorciano: LODI ADRIANA sta dentro Adriana
       Lodi Faustini Fustini. Si pretendono almeno due parole in comune.
    """
    v = cerca(reg, nome, mandati)
    if v:
        return v, 'nome'

    pezzi = {x for x in chiave(nome).split() if len(x) >= 3}
    if nascita and len(nascita) == 10:
        for mandato in mandati:
            for k, voce in indice.get((mandato, nascita), []):
                if pezzi & {x for x in k.split() if len(x) >= 3}:
                    return voce, 'data'

    if per_mandato and len(pezzi) >= 2:
        for mandato in mandati:
            for k, voce in per_mandato.get(mandato, []):
                altri = {x for x in k.split() if len(x) >= 3}
                if len(altri) >= 2 and (altri <= pezzi or pezzi <= altri):
                    return voce, 'nome contenuto'
    return None, None


def cerca(reg, nome, mandati):
    """La voce di quella persona, cercata solo fra le legislature che ha in
    comune col registro. Nessuna legislatura condivisa, nessun aggancio."""
    voci = reg.get(chiave(nome))
    if not voci:
        return None
    comuni = [m for m in mandati if m in voci]
    if not comuni:
        return None
    for m in comuni:
        if voci[m].get('morte'):
            return voci[m]
    return voci[comuni[0]]


if __name__ == '__main__':
    reg = registro(usa_cache=False)
    con_morte = sum(1 for v in reg.values() if any(x.get('morte') for x in v.values()))
    print('deputati distinti nel perimetro: %d' % len(reg))
    print('di cui con data di morte: %d' % con_morte)
