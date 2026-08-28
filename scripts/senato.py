# -*- coding: utf-8 -*-
"""Terza fonte: gli open data del Senato della Repubblica.

La Camera copre i propri deputati e ignora i senatori. Questo chiude il buco
dall'altra parte del Parlamento: stessa idea, stessa cautela sugli omonimi.
"""
import urllib.request, urllib.parse, json, os, sys, time

ENDPOINT = 'https://dati.senato.it/sparql'
QUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(QUI, '..', 'data', 'cache', 'senato_decessi.json')

Q_DECESSI = """
PREFIX osr: <http://dati.senato.it/osr/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT DISTINCT ?nome ?cognome ?nascita ?morte WHERE {
  ?s a osr:Senatore ; foaf:firstName ?nome ; foaf:lastName ?cognome ;
     osr:dataMorte ?morte .
  OPTIONAL { ?s osr:dataNascita ?nascita }
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


def data_iso(v):
    """Il Senato scrive gia' in forma ISO, ma non si sa mai."""
    v = (v or '').strip()[:10]
    if len(v) == 10 and v[4] == '-' and v[7] == '-':
        return v
    if len(v) >= 4 and v[:4].isdigit():
        return v[:4]
    return None


def decessi(usa_cache=True):
    """Ritorna {chiave nome: {'morte': iso, 'nascita': iso}}."""
    import camera  # la chiave dei nomi e' la stessa, meglio non duplicarla
    if usa_cache and os.path.exists(CACHE):
        return json.load(open(CACHE, encoding='utf-8'))
    fuori = {}
    for r in interroga(Q_DECESSI):
        m = data_iso(r.get('morte', {}).get('value'))
        if not m:
            continue
        k = camera.chiave(r.get('nome', {}).get('value'),
                          r.get('cognome', {}).get('value'))
        if not k:
            continue
        fuori[k] = {'morte': m,
                    'nascita': data_iso(r.get('nascita', {}).get('value'))}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(fuori, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    return fuori


if __name__ == '__main__':
    sys.path.insert(0, QUI)
    d = decessi(usa_cache=False)
    print('decessi noti al Senato: %d' % len(d))
    print('con anche la nascita: %d' % sum(1 for v in d.values() if v['nascita']))
