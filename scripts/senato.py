# -*- coding: utf-8 -*-
"""Terza fonte: gli open data del Senato della Repubblica.

La Camera copre i propri deputati e ignora i senatori: questo chiude il buco
dall'altra parte del Parlamento. Stessa regola d'aggancio, nome piu' legislatura
in comune, e la data di nascita tenuta fuori dalla decisione.

Il Senato non ha avuto Costituente, e numera le legislature con le cifre.
"""
import urllib.request, urllib.parse, json, os, sys, time

ENDPOINT = 'https://dati.senato.it/sparql'
QUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(QUI, '..', 'data', 'cache', 'senato_registro.json')

LEGISLATURE = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII',
               8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI'}

Q_SENATORI = """
PREFIX osr: <http://dati.senato.it/osr/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT DISTINCT ?nome ?cognome ?leg ?nascita ?morte WHERE {
  ?s a osr:Senatore ; foaf:firstName ?nome ; foaf:lastName ?cognome ;
     osr:mandato ?m .
  ?m osr:legislatura ?leg .
  FILTER(?leg <= 11)
  OPTIONAL { ?s osr:dataNascita ?nascita }
  OPTIONAL { ?s osr:dataMorte ?morte }
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
    v = (v or '').strip()[:10]
    if len(v) == 10 and v[4] == '-' and v[7] == '-':
        return v
    if len(v) >= 4 and v[:4].isdigit():
        return v[:4]
    return None


def registro(usa_cache=True):
    """{chiave nome: {mandato: {'morte':…, 'nascita':…}}}"""
    import camera
    if usa_cache and os.path.exists(CACHE):
        return json.load(open(CACHE, encoding='utf-8'))
    fuori = {}
    for r in interroga(Q_SENATORI):
        mandato = LEGISLATURE.get(int(float(r['leg']['value'])))
        if not mandato:
            continue
        k = camera.chiave(r.get('nome', {}).get('value'),
                          r.get('cognome', {}).get('value'))
        if not k:
            continue
        fuori.setdefault(k, {})[mandato] = {
            'morte': data_iso(r.get('morte', {}).get('value')),
            'nascita': data_iso(r.get('nascita', {}).get('value'))}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(fuori, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    return fuori


def cerca(reg, nome, mandati):
    import camera
    return camera.cerca(reg, nome, mandati)


def indice_per_data(reg):
    import camera
    return camera.indice_per_data(reg)


def indice_per_mandato(reg):
    import camera
    return camera.indice_per_mandato(reg)


def cerca_ampia(reg, indice, nome, nascita, mandati, per_mandato=None):
    import camera
    return camera.cerca_ampia(reg, indice, nome, nascita, mandati, per_mandato)


if __name__ == '__main__':
    sys.path.insert(0, QUI)
    reg = registro(usa_cache=False)
    con_morte = sum(1 for v in reg.values() if any(x.get('morte') for x in v.values()))
    print('senatori distinti nel perimetro: %d' % len(reg))
    print('di cui con data di morte: %d' % con_morte)
