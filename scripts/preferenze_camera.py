# -*- coding: utf-8 -*-
"""I voti di preferenza alla Camera, dal 1948 al 1992.

Vengono dall'archivio storico delle elezioni del Ministero dell'Interno
(Eligendo), che per ogni elezione pubblica un pacchetto con il file
cameraAAAA_preferenze.txt: circoscrizione, lista, voti della lista, cognome
e nome del candidato, se e' stato eletto e le sue preferenze.

L'aggancio ai nostri deputati usa il nome come lo scrive la Camera (lo stesso
stile del Ministero: SALVATORE FORMICA, non Rino), la legislatura che
quell'elezione ha aperto e la circoscrizione in cui la Camera lo da' eletto.
Tre cose insieme: un omonimo nella stessa circoscrizione e nella stessa
elezione e' quasi impossibile, e se capita la riga resta fuori.

Come gli altri pacchetti, si riscarica una volta a settimana e la versione
ridotta resta in data/registri/camera_preferenze.json.
"""
import io
import json
import os
import re
import sys
import unicodedata
import urllib.request
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import camera_anagrafe

QUI = os.path.dirname(os.path.abspath(__file__))
ISTANTANEA = os.path.join(QUI, '..', 'data', 'registri', 'camera_preferenze.json')
PACCHETTO = 'https://elezionistorico.interno.gov.it/daithome/documenti/opendata/camera/camera-%s.zip'

ELEZIONI = [('19480418', 'I'), ('19530607', 'II'), ('19580525', 'III'),
            ('19630428', 'IV'), ('19680519', 'V'), ('19720507', 'VI'),
            ('19760620', 'VII'), ('19790603', 'VIII'), ('19830626', 'IX'),
            ('19870614', 'X'), ('19920405', 'XI')]


def chiave(testo):
    """Nome ridotto all'osso. Gli apostrofi spariscono, perche' il Ministero
    scrive DAMICO dove la Camera scrive D'AMICO; "detto Rino" non e' il nome."""
    t = re.sub(r'\b(DETTO|DETTA)\b.*$', '', (testo or '').upper())
    t = unicodedata.normalize('NFKD', t.lower())
    t = ''.join(c for c in t if not unicodedata.combining(c)).replace("'", '').replace('’', '')
    return ' '.join(sorted(re.findall(r'[a-z0-9]+', t)))


def _campi(riga):
    return [c.strip().strip('"') for c in riga.rstrip('\r\n').split(';')]


def costruisci(nomi=None):
    fuori = []
    for data, leg in ELEZIONI:
        r = urllib.request.Request(PACCHETTO % data,
                                   headers={'User-Agent': 'DuriAMorire/0.1 (progetto personale)'})
        with zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(r, timeout=300).read())) as z:
            nome = next(n for n in z.namelist() if 'preferenze' in n.lower())
            testo = z.read(nome).decode('latin-1')
        righe = testo.splitlines()
        intestazione = [h.lower() for h in _campi(righe[0])]
        i = {h: n for n, h in enumerate(intestazione)}
        for riga in righe[1:]:
            c = _campi(riga)
            if len(c) < len(intestazione):
                continue
            try:
                pref = int(c[i['preferenze']] or 0)
            except ValueError:
                continue
            k = chiave(c[i['nome']] + ' ' + c[i['cognome']])
            # dei 75.000 candidati servono solo quelli col nome di uno dei nostri
            if nomi is not None and k not in nomi:
                continue
            fuori.append({'leg': leg, 'anno': data[:4],
                          'circ': c[i['circoscrizione']].upper(),
                          'lista': c[i['descrlista']],
                          'chiave': k,
                          'eletto': c[i['codtipoeletto']] == 'E',
                          'preferenze': pref})
    return fuori


def preferenze(oggi, anagrafe_camera=None, forza=False):
    vecchia = json.load(open(ISTANTANEA, encoding='utf-8')) if os.path.exists(ISTANTANEA) else None
    if vecchia and not forza:
        quando = vecchia.get('_scaricato', '')
        if quando and (oggi - camera_anagrafe._giorno(quando)).days < \
                camera_anagrafe.GIORNI_FRA_UN_GIRO_E_LALTRO:
            print('  preferenze del %s: ancora buone' % quando)
            return vecchia
    try:
        nomi = None
        if anagrafe_camera:
            nomi = {chiave(v['nome'] + ' ' + v['cognome'])
                    for k, v in anagrafe_camera.items() if not k.startswith('_')}
        nuova = {'candidati': costruisci(nomi), '_scaricato': oggi.isoformat()}
    except Exception as e:
        sys.stderr.write('  preferenze non scaricate (%s): uso la copia versionata.\n' % e)
        return vecchia or {'candidati': []}
    if vecchia and len(nuova['candidati']) < len(vecchia['candidati']) * 0.8:
        sys.stderr.write('  ATTENZIONE: preferenze molto piu\' magre del solito: '
                         'uso la copia versionata.\n')
        return vecchia
    json.dump(nuova, open(ISTANTANEA, 'w', encoding='utf-8'), ensure_ascii=False,
              separators=(',', ':'))
    return nuova


def aggancia(persone, dati, anagrafe_camera):
    """Per ogni deputato e legislatura: il candidato con lo stesso nome di
    registro, nella stessa elezione, nella circoscrizione in cui la Camera lo
    da' eletto (BARI sta in BARI-FOGGIA)."""
    indice = {}
    for c in dati.get('candidati', []):
        indice.setdefault((c['leg'], c['chiave']), []).append(c)
    trovate = mancate = 0
    for p in persone.values():
        v = anagrafe_camera.get(p.get('anagrafe_camera') or '')
        if not v:
            continue
        k = chiave(v['nome'] + ' ' + v['cognome'])
        for leg, (ramo, luogo) in (p.get('elezioni') or {}).items():
            if ramo != 'C' or leg == 'Costituente':
                continue
            dove = re.sub(r"[^A-Z]", '', luogo.upper())
            candidati = [c for c in indice.get((leg, k), [])
                         if re.sub(r"[^A-Z]", '', c['circ']).startswith(dove[:5])]
            if dove.startswith('COLLEGIOUNICO'):
                candidati = []   # i resti nazionali non hanno preferenze proprie
            elif not candidati and len(indice.get((leg, k), [])) == 1:
                # La Camera lo da' eletto altrove (chi era candidato in piu'
                # circoscrizioni sceglieva dove sedere), ma in tutta Italia, in
                # quell'elezione, un candidato con quel nome c'e' uno solo.
                candidati = indice[(leg, k)]
            if len(candidati) == 1:
                c = candidati[0]
                p.setdefault('preferenze', []).append(
                    [leg, c['anno'], c['circ'], c['lista'], c['preferenze'], c['eletto']])
                trovate += 1
            else:
                mancate += 1
    print('  preferenze: %d elezioni ritrovate, %d no' % (trovate, mancate))
    return trovate, mancate


ANNI_MINIMI = 25   # per la Camera si poteva essere candidati dai 25 anni


def aggancia_sconfitte(persone, dati, anagrafe_camera):
    """Le elezioni alla Camera in cui uno dei nostri si e' candidato e non e'
    entrato. Solo dove l'aggancio e' sicuro: stesso nome di registro, una
    circoscrizione in cui la Camera lo da' eletto almeno un'altra volta, e un
    solo candidato con quel nome li', in quell'elezione. Niente sconfitte
    negli anni in cui sedeva comunque in Parlamento (candidato in due posti,
    eletto nell'altro), ne' prima dei 25 anni o dopo la morte."""
    indice = {}
    for c in dati.get('candidati', []):
        indice.setdefault((c['leg'], c['chiave']), []).append(c)
    trovate = 0
    for p in persone.values():
        v = anagrafe_camera.get(p.get('anagrafe_camera') or '')
        if not v:
            continue
        k = chiave(v['nome'] + ' ' + v['cognome'])
        elezioni = p.get('elezioni') or {}
        dove = {re.sub(r'[^A-Z]', '', luogo.upper())[:5]
                for ramo, luogo in elezioni.values() if ramo == 'C'}
        dove.discard('COLLE')
        seduto = set(elezioni) | set(p.get('mandati') or [])
        nato = int((p.get('nascita') or '0')[:4] or 0)
        morto = int((p.get('morte') or '9999')[:4] or 9999)
        for data, leg in ELEZIONI:
            anno = int(data[:4])
            if leg in seduto or not nato or anno - nato < ANNI_MINIMI or anno > morto:
                continue
            tutti = indice.get((leg, k), [])
            qui = [c for c in tutti if re.sub(r'[^A-Z]', '', c['circ'])[:5] in dove]
            if len(qui) == 1 and not qui[0]['eletto']:
                c = qui[0]
                p.setdefault('sconfitte', []).append(
                    [leg, c['anno'], c['circ'], c['lista'], c['preferenze']])
                trovate += 1
    print('  candidature non elette: %d' % trovate)
    return trovate
