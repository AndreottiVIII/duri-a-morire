# -*- coding: utf-8 -*-
"""Seconda fonte: gli open data della Camera dei deputati.

Wikidata e' rapida sui personaggi noti e cieca sui deputati di seconda fila:
di parecchi non registra la morte, e quelli restano per sempre fra i viventi.
La Camera invece tiene il registro dei propri ex deputati, decessi compresi.

Qui si scarica quel registro e si prepara per l'incrocio con i nostri nomi.
"""
import urllib.request, urllib.parse, json, os, sys, time, unicodedata

ENDPOINT = 'https://dati.camera.it/sparql'
QUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(QUI, '..', 'data', 'cache', 'camera_decessi.json')

Q_DECESSI = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX bio: <http://purl.org/vocab/bio/0.1/>
SELECT DISTINCT ?cognome ?nome ?nascita ?morte WHERE {
  ?s a foaf:Person ; foaf:surname ?cognome ; foaf:firstName ?nome ;
     bio:Death ?d . ?d bio:date ?morte .
  OPTIONAL { ?s bio:Birth ?b . ?b bio:date ?nascita }
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


def chiave(nome, cognome):
    """Nome e cognome ridotti all'osso, per confronti che reggano accenti,
    apostrofi e MAIUSCOLE della Camera."""
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


def decessi(usa_cache=True):
    """Ritorna {chiave nome: {'morte': iso, 'nascita': iso}}."""
    if usa_cache and os.path.exists(CACHE):
        return json.load(open(CACHE, encoding='utf-8'))
    righe = interroga(Q_DECESSI)
    fuori = {}
    for r in righe:
        m = data_iso(r.get('morte', {}).get('value'))
        if not m:
            continue
        k = chiave(r.get('nome', {}).get('value'), r.get('cognome', {}).get('value'))
        if not k:
            continue
        fuori[k] = {'morte': m,
                    'nascita': data_iso(r.get('nascita', {}).get('value'))}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(fuori, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    return fuori


if __name__ == '__main__':
    d = decessi(usa_cache=False)
    print('decessi noti alla Camera: %d' % len(d))
    print('con anche la nascita: %d' % sum(1 for v in d.values() if v['nascita']))
