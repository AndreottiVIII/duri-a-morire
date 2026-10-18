# -*- coding: utf-8 -*-
"""Le proposte di legge presentate alla Camera, dalla I all'XI legislatura.

Vengono dai pacchetti atto-01 ... atto-11 di dati.camera.it/ocd/dump/, uno
per legislatura (per la Costituente non c'e'). Per ogni deputato si contano
le proposte di iniziativa parlamentare firmate per primo e quelle cofirmate,
e si tengono i titoli delle prime. I disegni di legge del governo, che un
ministro firma per l'esecutivo e non per se', si contano a parte.

Il Senato i suoi disegni di legge di quegli anni negli open data non li ha:
la sezione dice "alla Camera" ed e' giusto cosi'.

I pacchetti non cambiano piu' (sono legislature chiuse): si riscaricano una
volta a settimana come il resto dell'anagrafe, e la versione ridotta resta in
data/registri/camera_proposte.json.
"""
import io
import json
import os
import re
import sys
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import camera_anagrafe

QUI = os.path.dirname(os.path.abspath(__file__))
ISTANTANEA = os.path.join(QUI, '..', 'data', 'registri', 'camera_proposte.json')
LEGISLATURE = ['%02d' % n for n in range(1, 12)]


def _locale(tag):
    # alcuni pacchetti dichiarano lo spazio dei nomi dati.intra.camera.it,
    # altri dati.camera.it: conta solo il nome dell'elemento
    return tag.rsplit('}', 1)[-1]


def _figli(el, nome):
    return [x for x in el if _locale(x.tag) == nome]


def _testo(el, nome):
    f = _figli(el, nome)
    return (f[0].text or '').strip() if f else ''


def _pid(el):
    v = next((v for k, v in el.attrib.items() if k.endswith('resource')), '')
    m = re.search(r'/[dp](\d+)(?:_|$)', v)
    return m.group(1) if m else None


def _titolo(t):
    """'IOTTI ed altri: Riforma del diritto di famiglia' -> 'Riforma del
    diritto di famiglia': chi la firma lo dice gia' la scheda."""
    t = re.sub(r'\s+', ' ', t or '').strip()
    m = re.match(r"^[A-ZÀ-Ü' .,-]+?(?: ed altri| e [A-ZÀ-Ü' .-]+)?: (.+)$", t)
    return m.group(1) if m else t


def costruisci():
    fuori = {}
    for leg in LEGISLATURE:
        r = urllib.request.Request(
            'https://dati.camera.it/ocd/dump/atto-%s.rdf.zip' % leg,
            headers={'User-Agent': 'DuriAMorire/0.1 (progetto personale)'})
        with zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(r, timeout=300).read())) as z:
            radice = ET.fromstring(z.read(z.namelist()[0]))
        for el in radice.iter():
            if _locale(el.tag) != 'atto' or _testo(el, 'type') != 'Progetto di Legge':
                continue
            primi = [_pid(x) for x in _figli(el, 'primo_firmatario')]
            altri = [_pid(x) for x in _figli(el, 'altro_firmatario')]
            if _testo(el, 'iniziativa') == 'Parlamentare':
                data = camera_anagrafe._data(_testo(el, 'date')) or ''
                for p in filter(None, primi):
                    v = fuori.setdefault(p, {})
                    v['primo'] = v.get('primo', 0) + 1
                    v.setdefault('titoli', []).append([data, _titolo(_testo(el, 'title'))])
                for p in filter(None, altri):
                    v = fuori.setdefault(p, {})
                    v['cofirmate'] = v.get('cofirmate', 0) + 1
            else:
                for p in filter(None, primi):
                    v = fuori.setdefault(p, {})
                    v['governo'] = v.get('governo', 0) + 1
    for v in fuori.values():
        if v.get('titoli'):
            v['titoli'].sort()
    return fuori


def proposte(oggi, forza=False):
    vecchia = json.load(open(ISTANTANEA, encoding='utf-8')) if os.path.exists(ISTANTANEA) else None
    if vecchia and not forza:
        quando = vecchia.get('_scaricato', '')
        if quando and (oggi - camera_anagrafe._giorno(quando)).days < \
                camera_anagrafe.GIORNI_FRA_UN_GIRO_E_LALTRO:
            print('  proposte di legge del %s: ancora buone' % quando)
            return vecchia
    try:
        nuova = costruisci()
        nuova['_scaricato'] = oggi.isoformat()
    except Exception as e:
        sys.stderr.write('  proposte di legge non scaricate (%s): uso la copia versionata.\n' % e)
        return vecchia or {}
    if vecchia and len(nuova) < len(vecchia) * 0.8:
        sys.stderr.write('  ATTENZIONE: proposte di legge molto piu\' magre del solito: '
                         'uso la copia versionata.\n')
        return vecchia
    json.dump(nuova, open(ISTANTANEA, 'w', encoding='utf-8'), ensure_ascii=False,
              sort_keys=True, separators=(',', ':'))
    return nuova


def aggancia(persone, dati):
    """Per identificativo della Camera: niente nomi da accoppiare."""
    n = 0
    for p in persone.values():
        v = dati.get(p.get('anagrafe_camera') or p.get('id_camera') or '')
        if not v or not (v.get('primo') or v.get('cofirmate')):
            continue
        p['proposte'] = {'primo': v.get('primo', 0), 'cofirmate': v.get('cofirmate', 0)}
        n += 1
    print('  %d schede con proposte di legge alla Camera' % n)
