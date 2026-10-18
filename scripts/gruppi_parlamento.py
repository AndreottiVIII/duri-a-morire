"""I gruppi parlamentari di ogni legislatura, con le date dei passaggi.

Alla Camera dall'endpoint di dati.camera.it (ocd:aderisce: il gruppo col
periodo, "PARTITO SOCIALISTA ITALIANO (30.04.1992-20.05.1993)", e la sigla
del gruppo); al Senato da dati.senato.it, col nome che il gruppo aveva in
quei giorni. Servono alla scheda per dire chi ha cambiato gruppo, e quando:
non fanno statistica.

Come gli altri registri si riscarica una volta a settimana; la copia ridotta
resta in data/registri/gruppi_parlamento.json.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import camera
import camera_anagrafe
import senato

QUI = os.path.dirname(os.path.abspath(__file__))
ISTANTANEA = os.path.join(QUI, '..', 'data', 'registri', 'gruppi_parlamento.json')
ROMANI = ['Costituente', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI']

# Le adesioni stanno dalla parte del gruppo: ocd:siComponeDi, con il
# deputato e le date. Dal lato del deputato (ocd:aderisce) l'endpoint le ha
# solo per la X e la XI legislatura. Per i gruppi le legislature sotto la
# decima hanno lo zero davanti: repubblica_02.
Q_CAMERA = """
PREFIX ocd: <http://dati.camera.it/ocd/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT DISTINCT ?dep ?gl ?sig ?s ?e WHERE {
  ?g a ocd:gruppoParlamentare ;
     ocd:rif_leg ?leg ;
     rdfs:label ?gl ;
     ocd:siComponeDi ?x .
  ?x ocd:rif_deputato ?dep ; ocd:startDate ?s .
  OPTIONAL { ?x ocd:endDate ?e }
  OPTIONAL { ?g dcterms:alternative ?sig }
  VALUES ?leg { <http://dati.camera.it/ocd/legislatura.rdf/repubblica_%d>
                <http://dati.camera.it/ocd/legislatura.rdf/repubblica_%02d> }
}
"""

Q_SENATO = """PREFIX osr: <http://dati.senato.it/osr/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX ocd: <http://dati.camera.it/ocd/>
SELECT DISTINCT ?nome ?cognome ?gr ?i ?f WHERE {
  ?s a osr:Senatore ; foaf:firstName ?nome ; foaf:lastName ?cognome ; ocd:aderisce ?a .
  ?a osr:gruppo ?gr ; osr:legislatura %d ; osr:inizio ?i .
  OPTIONAL { ?a osr:fine ?f }
}"""


def _v(r, k):
    return (r.get(k, {}).get('value') or '').strip()


def _camera():
    fuori = {}
    for n, leg in enumerate(ROMANI):
        righe = camera.interroga(Q_CAMERA % (n, n))
        if len(righe) >= 10000:
            raise RuntimeError('risposta della Camera tagliata')
        for r in righe:
            nome = re.sub(r'\s*\([^)]*\)\s*$', '', _v(r, 'gl'))
            nome = re.sub(r'\s*\([^)]*\)\s*$', '', nome).strip()
            riga = [leg, _v(r, 'sig') or nome, camera.data_iso(_v(r, 's')) or '',
                    camera.data_iso(_v(r, 'e')) or '']
            pid = camera.id_persona(_v(r, 'dep'))
            if riga not in fuori.setdefault(pid, []):
                fuori[pid].append(riga)
        time.sleep(0.5)
    return fuori


def _senato():
    nomi = {}
    for r in senato.interroga(senato.Q_DENOMINAZIONI):
        t = _v(r, 'breve') or _v(r, 'titolo')
        if t:
            nomi.setdefault(_v(r, 'gr'), []).append((_v(r, 'dInizio')[:10], _v(r, 'dFine')[:10], t))
    fuori = []
    for n in range(1, len(ROMANI)):
        righe = senato.interroga(Q_SENATO % n)
        if len(righe) >= 10000:
            raise RuntimeError('risposta del Senato tagliata')
        for r in righe:
            giorno = _v(r, 'i')[:10]
            tutti = nomi.get(_v(r, 'gr')) or []
            nome = next((t for da, a, t in tutti
                         if not (da and giorno and da > giorno) and not (a and giorno and a < giorno)),
                        tutti[0][2] if tutti else '')
            if nome:
                fuori.append({'chiave': camera.chiave(_v(r, 'nome'), _v(r, 'cognome')),
                              'leg': ROMANI[n], 'gruppo': nome.upper(),
                              'da': giorno, 'a': _v(r, 'f')[:10]})
        time.sleep(0.5)
    return fuori


def gruppi(oggi, forza=False):
    vecchia = json.load(open(ISTANTANEA, encoding='utf-8')) if os.path.exists(ISTANTANEA) else None
    if vecchia and not forza:
        quando = vecchia.get('_scaricato', '')
        if quando and (oggi - camera_anagrafe._giorno(quando)).days < \
                camera_anagrafe.GIORNI_FRA_UN_GIRO_E_LALTRO:
            print('  gruppi parlamentari del %s: ancora buoni' % quando)
            return vecchia
    try:
        nuova = {'camera': _camera(), 'senato': _senato(), '_scaricato': oggi.isoformat()}
    except Exception as e:
        sys.stderr.write('  gruppi non scaricati (%s): uso la copia versionata.\n' % e)
        return vecchia or {'camera': {}, 'senato': []}
    if vecchia and (len(nuova['camera']) < len(vecchia['camera']) * 0.8
                    or len(nuova['senato']) < len(vecchia['senato']) * 0.8):
        sys.stderr.write('  ATTENZIONE: gruppi molto piu\' magri del solito: '
                         'uso la copia versionata.\n')
        return vecchia
    json.dump(nuova, open(ISTANTANEA, 'w', encoding='utf-8'), ensure_ascii=False,
              sort_keys=True, separators=(',', ':'))
    return nuova


def aggancia(persone, dati, alias=None):
    """Alla Camera per identificativo; al Senato per nome e legislatura, e
    solo se la persona e' una. p['gruppi'] = [[leg, ramo, sigla, da, a]]."""
    per_chiave = {}
    for p in persone.values():
        nomi = {re.sub(r'\s*\([^)]*\)', '', p['nome'] or '')}
        if alias and alias.get(p['qid']):
            nomi.add(alias[p['qid']])
        for n in nomi:
            per_chiave.setdefault(camera.chiave(n), []).append(p)
    quanti = 0
    for p in persone.values():
        pid = p.get('anagrafe_camera') or p.get('id_camera')
        for leg, sigla, da, a in dati.get('camera', {}).get(pid or '', []):
            p.setdefault('gruppi', []).append([leg, 'C', sigla, da, a])
            quanti += 1
    for c in dati.get('senato', []):
        candidati = {id(p): p for p in per_chiave.get(c['chiave'], []) if c['leg'] in p['mandati']}
        if len(candidati) == 1:
            p = next(iter(candidati.values()))
            riga = [c['leg'], 'S', c['gruppo'], c['da'], c['a']]
            if riga not in p.setdefault('gruppi', []):
                p['gruppi'].append(riga)
                quanti += 1
    for p in persone.values():
        if p.get('gruppi'):
            p['gruppi'].sort(key=lambda g: (ROMANI.index(g[0]) if g[0] in ROMANI else 99, g[3] or ''))
    print('  gruppi parlamentari: %d adesioni' % quanti)
