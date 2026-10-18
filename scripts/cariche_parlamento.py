# -*- coding: utf-8 -*-
"""Le cariche dentro il Parlamento: chi ha presieduto la Camera o il Senato,
chi ne e' stato vicepresidente o questore, chi ha presieduto una commissione
o un gruppo parlamentare.

Due fonti, una per ramo, e nessuna sovrapposizione:

  Camera  i pacchetti ufficioParlamentare.rdf (presidenze, commissioni) e
          incarico.rdf (presidenti di gruppo), da dati.camera.it/ocd/dump/
  Senato  il servizio di interrogazione: Consiglio di Presidenza,
          commissioni, gruppi

Si tengono solo le cariche che dicono qualcosa: presidente, vicepresidente e
questore dell'assemblea, presidente di commissione (permanente, d'inchiesta,
bicamerale) e di gruppo. Restano fuori i ruoli minori (segretari,
vicepresidenti di commissione, capigruppo in commissione), le giunte, i
comitati, le delegazioni, e le commissioni speciali nate per una legge sola.

Come l'anagrafe della Camera, si riscarica una volta a settimana e la
versione ridotta resta versionata in data/registri/cariche_parlamento.json.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import camera_anagrafe
import senato

QUI = os.path.dirname(os.path.abspath(__file__))
ISTANTANEA = os.path.join(QUI, '..', 'data', 'registri', 'cariche_parlamento.json')
ROMANI = camera_anagrafe.ROMANI

PICCOLE = {'di', 'del', 'della', 'dello', 'dei', 'degli', 'delle', 'e', 'ed',
           'per', 'il', 'la', 'lo', 'i', 'gli', 'le', 'in', 'a', 'al', 'alla',
           'alle', 'ai', 'agli', 'allo', 'sul', 'sulla', 'sullo', 'sui', 'sugli',
           'sulle', 'su', 'con', 'tra', 'fra', 'da', 'dal', 'dalla', 'nel',
           'nella', 'nei', 'nelle', 'o', 'ad', 'od'}

# Un incarico di pochi giorni e' quasi sempre una formalita' (la commissione
# d'indagine su un'accusa fra due deputati, durata tre giorni) o un interim di
# passaggio: sotto questa soglia non entra.
GIORNI_MINIMI = 30


def bel_nome(testo):
    """'COMMISSIONE PARLAMENTARE D'INCHIESTA SUL CASO MORO' -> 'Commissione
    Parlamentare d'Inchiesta sul Caso Moro'. Le maiuscole su tutte le parole
    tengono i nomi propri (Moro, P2, Rai) senza doverli riconoscere."""
    t = re.sub(r"(\w)' (?=\w)", r"\1'", (testo or '').strip())
    # "I COMMISSIONE (AFFARI COSTITUZIONALI": la parentesi, tagliata alla prima
    # virgola, resterebbe aperta
    t = re.sub(r'\s+', ' ', t.replace('(', ' ').replace(')', ' ')).strip()
    fuori = []
    for i, parola in enumerate(t.split()):
        # il numero romano sta solo in testa ("I Commissione"): altrove "IL"
        # e' un articolo
        if (i == 0 and re.fullmatch(r'[IVXL]+', parola)) or re.search(r'\d', parola):
            fuori.append(parola)
            continue
        pezzi = re.split(r"(['’])", parola.lower())
        pezzi = [p if (p in PICCOLE and i > 0) or p in ("'", '’') else p[:1].upper() + p[1:]
                 for p in pezzi]
        # d'Inchiesta, dell'Interno: l'articolo resta minuscolo
        if len(pezzi) >= 3 and pezzi[0].lower() in {'d', 'dell', 'all', 'nell', 'l', 'sull', 'dall'}:
            pezzi[0] = pezzi[0].lower()
        fuori.append(''.join(pezzi))
    return ' '.join(fuori)


def troppo_breve(da, a):
    if not (da and a and len(da) >= 10 and len(a) >= 10):
        return False
    return (camera_anagrafe._giorno(a) - camera_anagrafe._giorno(da)).days < GIORNI_MINIMI


# ---------------------------------------------------------------- Camera

def _camera():
    uffici = camera_anagrafe._scarica('ufficioParlamentare')
    incarichi = camera_anagrafe._scarica('incarico')
    fuori = {}

    def aggiungi(pid, carica, da, a):
        if not troppo_breve(da, a):
            fuori.setdefault(pid, []).append({'carica': carica, 'da': da, 'a': a})

    voci = {}
    for s, p, o in camera_anagrafe._triple(uffici, '<http://dati.camera.it/ocd/ufficioParlamentare.rdf/'):
        voci.setdefault(s, {})[p] = o
    for v in voci.values():
        m = re.search(r'/d(\d+)_', v.get('rif_deputato', ''))
        if not m or not v.get('title'):
            continue
        ruolo = (v.get('carica') or '').upper()
        organo = re.match(r'^[A-Z\' ]+? di (.+?), [^,]+ \(', v['title'])
        organo = organo.group(1) if organo else ''
        da, a = camera_anagrafe._data(v.get('startDate')), camera_anagrafe._data(v.get('endDate'))
        if organo.startswith('UFFICIO DI PRESIDENZA'):
            nome = {'PRESIDENTE': 'Presidente della Camera',
                    'VICEPRESIDENTE': 'Vicepresidente della Camera',
                    'QUESTORE': 'Questore della Camera'}.get(ruolo)
            if nome:
                aggiungi(m.group(1), nome, da, a)
        elif ruolo == 'PRESIDENTE' and 'COMMISSIONE' in organo \
                and 'PER L\'ESAME D' not in organo:
            # i nomi lunghi si fermano alla prima virgola: "I Commissione
            # Affari Costituzionali", non tutto l'elenco delle materie
            aggiungi(m.group(1), 'Presidente della ' + bel_nome(organo.split(',')[0]), da, a)

    voci = {}
    for s, p, o in camera_anagrafe._triple(incarichi, '<http://dati.camera.it/ocd/incarico.rdf/'):
        voci.setdefault(s, {})[p] = o
    for v in voci.values():
        m = re.search(r'/d(\d+)_', v.get('rif_deputato', ''))
        if not m or (v.get('ruolo') or '').upper() != 'PRESIDENTE':
            continue
        gruppo = re.match(r'^PRESIDENTE del gruppo (.+?), [^,]+ \(', v.get('title', ''))
        if gruppo:
            aggiungi(m.group(1), 'Presidente del Gruppo ' + bel_nome(gruppo.group(1)),
                     camera_anagrafe._data(v.get('startDate')),
                     camera_anagrafe._data(v.get('endDate')))
    return fuori


# ---------------------------------------------------------------- Senato

PREFISSI = '''PREFIX osr: <http://dati.senato.it/osr/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX ocd: <http://dati.camera.it/ocd/>
'''

Q_PRESIDENZA = PREFISSI + '''SELECT ?nome ?cognome ?o ?c ?i ?f WHERE {
  ?s a osr:Senatore ; foaf:firstName ?nome ; foaf:lastName ?cognome ; osr:afferisce ?a .
  ?a osr:organo ?o ; osr:carica ?c ; osr:inizio ?i .
  OPTIONAL { ?a osr:fine ?f }
  FILTER(STR(?c) IN ("Presidente del Senato", "Vice Presidente del Senato", "Questore del Senato"))
}'''

Q_COMMISSIONI = PREFISSI + '''SELECT ?nome ?cognome ?l ?co ?i ?f WHERE {
  ?s a osr:Senatore ; foaf:firstName ?nome ; foaf:lastName ?cognome ; osr:afferisce ?a .
  ?a osr:commissione ?co ; osr:carica ?c ; osr:legislatura ?l ; osr:inizio ?i .
  FILTER(STR(?c) = "Presidente")
  OPTIONAL { ?a osr:fine ?f }
  FILTER(?l <= 11)
}'''

# Come si chiamava ogni commissione, periodo per periodo: la 3ª permanente era
# "Affari esteri e colonie" fino al 1958, poi "Affari esteri". E il numero
# stesso e' cambiato con le riforme dei regolamenti.
Q_NOMI_COMMISSIONI = PREFISSI + '''SELECT ?co ?t ?b ?di ?df WHERE {
  ?co a osr:Commissione .
  { ?co osr:denominazione ?d . ?d osr:titolo ?t .
    OPTIONAL { ?d osr:titoloBreve ?b } OPTIONAL { ?d osr:inizio ?di } OPTIONAL { ?d osr:fine ?df } }
  UNION { ?co osr:titolo ?t . OPTIONAL { ?co osr:titoloBreve ?b } }
}'''

Q_GRUPPI = PREFISSI + '''SELECT ?nome ?cognome ?l ?gr ?i ?f WHERE {
  ?s a osr:Senatore ; foaf:firstName ?nome ; foaf:lastName ?cognome ; ocd:aderisce ?a .
  ?a osr:carica ?c ; osr:gruppo ?gr ; osr:legislatura ?l ; osr:inizio ?i .
  FILTER(STR(?c) = "Presidente")
  OPTIONAL { ?a osr:fine ?f }
  FILTER(?l <= 11)
}'''


# Come ogni senatore e' entrato, legislatura per legislatura: eletto in una
# regione, a vita per nomina del Presidente, o di diritto da ex Presidente.
# Una legislatura per volta: tutte insieme sbattono contro il tetto di
# diecimila righe del Senato, che taglia senza dirlo.
# Con il mandato vengono anche il numero del senatore (per il collegamento
# alla sua scheda sul sito del Senato), la foto ufficiale e la professione.
Q_MANDATI = PREFISSI + '''PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?s ?nome ?cognome ?tipo ?reg ?foto ?prof WHERE {
  ?s a osr:Senatore ; foaf:firstName ?nome ; foaf:lastName ?cognome ; osr:mandato ?m .
  ?m osr:legislatura %d ; osr:tipoMandato ?tipo .
  OPTIONAL { ?m osr:regioneElezione ?reg }
  OPTIONAL { ?s foaf:depiction ?foto }
  OPTIONAL { ?s osr:professione ?x . ?x rdfs:label ?prof }
}'''


def _interroga_intera(query):
    righe = senato.interroga(query)
    if len(righe) >= 10000:
        raise RuntimeError('risposta del Senato tagliata a %d righe' % len(righe))
    return righe


def _v(r, k):
    return (r.get(k, {}).get('value') or '').strip()


def _senato():
    import camera
    fuori = []

    def aggiungi(r, leg, carica):
        if not leg or leg >= len(ROMANI) or troppo_breve(_v(r, 'i')[:10], _v(r, 'f')[:10]):
            return
        fuori.append({'chiave': camera.chiave(_v(r, 'nome'), _v(r, 'cognome')),
                      'leg': ROMANI[leg], 'carica': carica,
                      'da': _v(r, 'i')[:10] or None, 'a': _v(r, 'f')[:10] or None})

    for r in _interroga_intera(Q_PRESIDENZA):
        # l'organo e' la presidenza di quella legislatura: .../presidenza/5
        leg = int(_v(r, 'o').rsplit('/', 1)[-1] or 0)
        aggiungi(r, leg, {'Presidente del Senato': 'Presidente del Senato',
                          'Vice Presidente del Senato': 'Vicepresidente del Senato',
                          'Questore del Senato': 'Questore del Senato'}[_v(r, 'c')])
    time.sleep(0.5)
    nomi_comm = {}
    for r in _interroga_intera(Q_NOMI_COMMISSIONI):
        nomi_comm.setdefault(_v(r, 'co'), []).append(
            (_v(r, 'di')[:10], _v(r, 'df')[:10], _v(r, 't'), _v(r, 'b')))

    def nome_commissione(co, giorno):
        nomi = nomi_comm.get(co) or []
        # prima i nomi datati in vigore quel giorno, poi qualunque
        validi = [n for n in nomi if n[0] and not (giorno and n[0] > giorno)
                  and not (n[1] and giorno and n[1] < giorno)] or nomi
        if not validi:
            return ''
        da, a, titolo, breve = validi[0]
        # "3ª Commissione permanente" da sola non dice niente: ci va la materia
        if 'permanente' in titolo.lower() and breve:
            return '%s (%s)' % (bel_nome(titolo), bel_nome(breve))
        return bel_nome(titolo)

    time.sleep(0.5)
    for r in _interroga_intera(Q_COMMISSIONI):
        titolo = nome_commissione(_v(r, 'co'), _v(r, 'i')[:10])
        if 'Commissione' not in titolo or "per l'esame d" in titolo.lower():
            continue
        aggiungi(r, int(float(_v(r, 'l'))), 'Presidente della ' + titolo)
    time.sleep(0.5)
    # il gruppo col nome che aveva il giorno in cui la presidenza comincia
    denominazioni = {}
    for r in senato.interroga(senato.Q_DENOMINAZIONI):
        # il nome intero: la sigla breve, ridotta a maiuscole iniziali,
        # diventerebbe "Gruppo Dc"
        t = _v(r, 'titolo') or _v(r, 'breve')
        if t:
            denominazioni.setdefault(_v(r, 'gr'), []).append(
                (_v(r, 'dInizio')[:10], _v(r, 'dFine')[:10], t))
    for r in _interroga_intera(Q_GRUPPI):
        giorno = _v(r, 'i')[:10]
        nomi = denominazioni.get(_v(r, 'gr')) or []
        nome = next((t for da, a, t in nomi
                     if not (da and giorno and da > giorno) and not (a and giorno and a < giorno)),
                    nomi[0][2] if nomi else '')
        if nome:
            aggiungi(r, int(float(_v(r, 'l'))), 'Presidente del Gruppo ' + bel_nome(nome))
    return fuori


def _mandati_senato():
    import camera
    fuori = []
    for leg in range(1, len(ROMANI)):
        for r in _interroga_intera(Q_MANDATI % leg):
            tipo = _v(r, 'tipo').lower()
            luogo = ('a vita' if 'a vita' in tipo and 'diritto' not in tipo
                     else 'di diritto' if 'diritto' in tipo else _v(r, 'reg'))
            fuori.append({'chiave': camera.chiave(_v(r, 'nome'), _v(r, 'cognome')),
                          'leg': ROMANI[leg], 'luogo': luogo,
                          'id': '%d:%s' % (leg, _v(r, 's').rsplit('/', 1)[-1]),
                          # il Senato scrive "leg/8/", ma la foto sta in "leg/08/"
                          'foto': re.sub(r'/leg/(\d)/', r'/leg/0\1/',
                                         _v(r, 'foto').replace('http://', 'https://')),
                          'professione': _v(r, 'prof')})
        time.sleep(0.3)
    # ogni senatore torna piu' volte nella risposta: una riga per persona e
    # legislatura, preferendo quella che dice qualcosa
    unici = {}
    for x in fuori:
        k = (x['chiave'], x['leg'])
        if k not in unici:
            unici[k] = x
            continue
        # le righe ripetute si completano a vicenda
        for campo in ('luogo', 'foto', 'professione'):
            if x.get(campo) and not unici[k].get(campo):
                unici[k][campo] = x[campo]
    return sorted(unici.values(), key=lambda x: (x['leg'], x['chiave']))


# ---------------------------------------------------------------- insieme

def cariche(oggi, forza=False):
    vecchia = json.load(open(ISTANTANEA, encoding='utf-8')) if os.path.exists(ISTANTANEA) else None
    if vecchia and not forza:
        quando = vecchia.get('_scaricato', '')
        if quando and (oggi - camera_anagrafe._giorno(quando)).days < \
                camera_anagrafe.GIORNI_FRA_UN_GIRO_E_LALTRO:
            print('  cariche parlamentari del %s: ancora buone' % quando)
            return vecchia
    try:
        nuova = {'camera': _camera(), 'senato': _senato(), 'mandati_senato': _mandati_senato(),
                 '_scaricato': oggi.isoformat()}
    except Exception as e:
        sys.stderr.write('  cariche parlamentari non scaricate (%s): '
                         'uso la copia versionata.\n' % e)
        return vecchia or {'camera': {}, 'senato': []}
    if vecchia and (len(nuova['camera']) < len(vecchia['camera']) * 0.8
                    or len(nuova['senato']) < len(vecchia['senato']) * 0.8):
        sys.stderr.write('  ATTENZIONE: cariche parlamentari molto piu\' magre del '
                         'solito: uso la copia versionata.\n')
        return vecchia
    json.dump(nuova, open(ISTANTANEA, 'w', encoding='utf-8'), ensure_ascii=False,
              sort_keys=True, separators=(',', ':'))
    return nuova


def aggancia(persone, dati, chiave, alias=None):
    """Alla Camera la persona si riconosce dal suo identificativo; al Senato
    dal nome piu' la legislatura in cui ha tenuto la carica, che deve essere
    una delle sue. Due omonimi possibili: meglio niente che lo sbagliato."""
    # Chi ha il numero del Senato si trova solo con la chiave che il Senato
    # gli da'; e quella chiave non va a nessun altro, nemmeno a un omonimo.
    per_chiave = {}
    prese = {p['chiave_senato'] for p in persone.values() if p.get('chiave_senato')}
    for p in persone.values():
        if p.get('chiave_senato'):
            per_chiave.setdefault(p['chiave_senato'], []).append(p)
            continue
        nomi = {re.sub(r'\s*\([^)]*\)', '', p['nome'] or '')}
        if alias and alias.get(p['qid']):
            nomi.add(alias[p['qid']])
        for n in nomi:
            if chiave(n) not in prese:
                per_chiave.setdefault(chiave(n), []).append(p)
    contate = 0

    def metti(p, c):
        # la stessa carica puo' arrivare due volte (le commissioni bicamerali
        # stanno in tutti e due i registri): una sola
        nonlocal contate
        visti = {(x['carica'].lower(), x['da']) for x in p.get('incarichi_parlamento', [])}
        if (c['carica'].lower(), c['da']) not in visti:
            p.setdefault('incarichi_parlamento', []).append(
                {'carica': c['carica'], 'da': c['da'], 'a': c['a']})
            contate += 1

    for p in persone.values():
        pid = p.get('anagrafe_camera') or p.get('id_camera')
        for c in dati.get('camera', {}).get(pid or '', []):
            metti(p, c)
    for c in dati.get('senato', []):
        candidati = {id(p): p for p in per_chiave.get(c['chiave'], []) if c['leg'] in p['mandati']}
        if len(candidati) == 1:
            metti(next(iter(candidati.values())), c)
    # Dove e come e' stato eletto al Senato, accanto alle elezioni alla
    # Camera; e per chi alla Camera non e' mai stato, la professione e la foto
    # ufficiale che il Senato registra, come per i deputati fa la Camera.
    ordine = {l: i for i, l in enumerate(ROMANI)}
    for c in sorted(dati.get('mandati_senato', []), key=lambda c: ordine.get(c['leg'], 0)):
        candidati = {id(p): p for p in per_chiave.get(c['chiave'], []) if c['leg'] in p['mandati']}
        if len(candidati) != 1:
            continue
        p = next(iter(candidati.values()))
        if c['luogo']:
            p.setdefault('elezioni', {})[c['leg']] = ['S', c['luogo']]
        if c.get('id'):
            p['scheda_senato'] = c['id']          # l'ultima legislatura vince
        if c.get('professione') and not p.get('studi'):
            p['studi'] = c['professione']
        # Le foto del Senato si aprono dal suo sito ma non si lasciano mostrare
        # dentro altri siti: qui sarebbero immagini rotte, e non si usano.
    print('  %d cariche parlamentari, per %d schede' % (
        contate, sum(1 for p in persone.values() if p.get('incarichi_parlamento'))))
