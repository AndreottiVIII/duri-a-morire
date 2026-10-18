# -*- coding: utf-8 -*-
"""L'anagrafe della Camera: chi era, cosa aveva studiato, che faceva, e gli
incarichi di governo con il nome del ministero com'era allora.

Viene dai pacchetti che la Camera pubblica interi, uno per tipo di dato
(dati.camera.it/ocd/dump/), e non dal servizio di interrogazione: quello a
volte resta fermo per giorni, i pacchetti si scaricano lo stesso. Ne servono
tre:

  persona.rdf        nome, sesso, studi e professione, foto, legislature
                     alla Camera e al Senato, Consulta Nazionale
  membroGoverno.rdf  ogni incarico di governo: ruolo, ministero, date
  governo.rdf        il nome di ogni governo

Il pacchetto delle persone copre anche i senatori, e chi e' stato solo al
governo senza seggio. Dalla Camera esce una versione ridotta, solo per chi
rientra nel nostro perimetro, che resta versionata in data/registri/: se un
giorno i pacchetti non arrivano si usa l'ultima copia buona.
"""
import io
import json
import os
import re
import sys
import urllib.request
import zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(QUI, '..', 'data', 'cache', 'camera_dump')
ISTANTANEA = os.path.join(QUI, '..', 'data', 'registri', 'camera_anagrafe.json')
DUMP = 'https://dati.camera.it/ocd/dump/%s.rdf.zip'

ROMANI = ['Costituente', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX',
          'X', 'XI']
# I due governi del perimetro che non sono legislature: i loro tecnici un
# seggio non l'hanno mai avuto, e si riconoscono dal governo.
GOVERNI_PERIMETRO = {'Ciampi': 'Governo Ciampi', 'Dini': 'Governo Dini'}

RIGA = re.compile(r'^(\S+)\t<([^>]+)>\t(.*) \.\s*$')

GIORNI_FRA_UN_GIRO_E_LALTRO = 7


def _giorno(iso):
    import datetime
    return datetime.date(int(iso[:4]), int(iso[5:7]), int(iso[8:10]))


def _scarica(nome):
    os.makedirs(CACHE, exist_ok=True)
    r = urllib.request.Request(DUMP % nome, headers={
        'User-Agent': 'DuriAMorire/0.1 (progetto personale)'})
    dati = urllib.request.urlopen(r, timeout=300).read()
    with zipfile.ZipFile(io.BytesIO(dati)) as z:
        testo = z.read(z.namelist()[0]).decode('utf-8')
    open(os.path.join(CACHE, nome + '.rdf'), 'w', encoding='utf-8').write(testo)
    return testo


def _letterale(o):
    o = o.strip()
    if o.startswith('<'):
        return o[1:-1]
    if o.startswith('"'):
        s = o[1:o.rindex('"')]
        s = re.sub(r'\\u([0-9A-Fa-f]{4})', lambda m: chr(int(m.group(1), 16)), s)
        return s.replace('\\"', '"').replace('\\n', ' ')
    return o


def _triple(testo, prefisso):
    for riga in testo.splitlines():
        if not riga.startswith(prefisso):
            continue
        m = RIGA.match(riga)
        if m:
            yield m.group(1)[1:-1], m.group(2).rsplit('/', 1)[-1].split('#')[-1], \
                _letterale(m.group(3))


def _data(s):
    s = (s or '').strip()
    return '%s-%s-%s' % (s[:4], s[4:6], s[6:8]) if len(s) == 8 and s.isdigit() else None


def _pulisci(testo):
    """'<p>Laurea in lettere; insegnante.</p>' -> 'Laurea in lettere; insegnante'."""
    t = re.sub(r'<[^>]+>', ' ', testo or '')
    t = re.sub(r'\s+', ' ', t).strip().rstrip('.;, ').strip()
    t = re.sub(r'\s*;\s*', '; ', t)
    return t[:1].upper() + t[1:] if t else ''


PICCOLE_LUOGHI = {'di', 'del', 'della', 'dei', 'e', 'nell', 'nella', 'sul', 'in', 'd'}


def nome_di_luogo(testo):
    """'REGGIO NELL'EMILIA' -> "Reggio nell'Emilia"; 'BARI' -> 'Bari'."""
    t = (testo or '').strip()
    # il collegio dei resti nazionali la Camera lo scrive in due modi
    if t.upper() == 'CUN' or t.upper().startswith('COLLEGIO UNICO'):
        return 'Collegio unico nazionale'
    parole = re.split(r"([ '\-/])", t.lower())
    fuori = []
    for i, w in enumerate(parole):
        fuori.append(w if (w in PICCOLE_LUOGHI and i > 0) else w[:1].upper() + w[1:])
    return ''.join(fuori)


def _nome_governo(titolo, conta):
    """'I Governo Goria (28.07.1987 - 13.04.1988)' -> 'Goria'; 'VII Governo
    Andreotti (...)' -> 'Andreotti VII'. Il numero solo dove serve."""
    t = re.sub(r'\s*\(.*$', '', titolo or '').strip()
    m = re.match(r'^([IVXL]+)\s+Governo\s+(.+)$', t)
    if m:
        ordine, chi = m.groups()
    else:
        ordine, chi = 'I', re.sub(r'^Governo\s+', '', t)
    return chi if conta.get(chi, 0) <= 1 else '%s %s' % (chi, ordine)


def costruisci():
    """Scarica i tre pacchetti e ne ricava la versione ridotta."""
    persona = _scarica('persona')
    membri = _scarica('membroGoverno')
    governi = _scarica('governo')

    titoli_gov = {}
    for s, p, o in _triple(governi, '<http://dati.camera.it/ocd/governo.rdf/'):
        if p == 'title':
            titoli_gov[s.rsplit('/', 1)[-1]] = o
    conta = {}
    for t in titoli_gov.values():
        chi = re.sub(r'^([IVXL]+\s+)?Governo\s+', '', re.sub(r'\s*\(.*$', '', t)).strip()
        conta[chi] = conta.get(chi, 0) + 1
    nome_gov = {g: _nome_governo(t, conta) for g, t in titoli_gov.items()}

    incarichi = {}
    voci = {}
    for s, p, o in _triple(membri, '<http://dati.camera.it/ocd/membroGoverno.rdf/'):
        voci.setdefault(s, {})[p] = o
    for v in voci.values():
        pid = (v.get('rif_persona') or '').rsplit('/p', 1)[-1]
        if not pid.isdigit() or not v.get('title'):
            continue
        carica = re.sub(r'\s*\([^)]*\)\s*$', '', v['title']).strip()
        if v.get('interim') == '1':
            carica += ' (ad interim)'
        incarichi.setdefault(pid, []).append({
            'carica': carica,
            'da': _data(v.get('startDate')),
            'a': _data(v.get('endDate')),
            'governo': nome_gov.get((v.get('rif_governo') or '').rsplit('/', 1)[-1], ''),
        })

    persone = {}
    for s, p, o in _triple(persona, '<http://dati.camera.it/ocd/persona.rdf/p'):
        pid = s.rsplit('/p', 1)[-1]
        if not pid.isdigit():
            continue
        x = persone.setdefault(pid, {'leg': set()})
        if p in ('rif_mandatoCamera', 'rif_mandatoSenato'):
            m = re.search(r'/m[cs](\d+)_', o)
            if m and int(m.group(1)) < len(ROMANI):
                x['leg'].add(ROMANI[int(m.group(1))])
        elif p in ('firstName', 'surname', 'gender', 'description', 'depiction'):
            x[p] = o
        elif p == 'membroConsulta' and o == 'true':
            x['consulta'] = 1

    # Dove e' stato eletto, legislatura per legislatura: "BARI", "PARMA".
    # L'identificativo dell'elezione porta gia' legislatura e persona:
    # e10_23510_19870625.
    elezioni = _scarica('elezione')
    for s, p, o in _triple(elezioni, '<http://dati.camera.it/ocd/elezione.rdf/e'):
        m = re.search(r'/e(\d+)_(\d+)_', s)
        if p == 'coverage' and m and int(m.group(1)) < len(ROMANI) and m.group(2) in persone:
            persone[m.group(2)].setdefault('elezioni', {})[ROMANI[int(m.group(1))]] = \
                nome_di_luogo(o)

    # Solo chi tocca il nostro perimetro: una legislatura fino all'XI, la
    # Consulta, o un posto nei governi Ciampi e Dini.
    fuori = {}
    for pid, x in persone.items():
        gov = sorted(incarichi.get(pid, []), key=lambda i: i['da'] or '')
        nel_perimetro = x['leg'] or x.get('consulta') or any(
            i['governo'].split(' ')[0] in GOVERNI_PERIMETRO for i in gov)
        if not nel_perimetro:
            continue
        voce = {'nome': x.get('firstName', ''), 'cognome': x.get('surname', ''),
                'leg': sorted(x['leg'], key=ROMANI.index)}
        if x.get('gender') == 'female':
            voce['donna'] = 1
        if x.get('description') and _pulisci(x['description']):
            voce['studi'] = _pulisci(x['description'])
        if x.get('depiction'):
            voce['foto'] = x['depiction'].replace('http://', 'https://')
        if x.get('consulta'):
            voce['consulta'] = 1
        if x.get('elezioni'):
            voce['elezioni'] = x['elezioni']
        if gov:
            voce['governo'] = gov
        fuori[pid] = voce
    return fuori


def anagrafe(oggi, forza=False):
    """La versione ridotta. Studi, governi e Consulta della Prima Repubblica
    sono storia chiusa e cambiano di rado: i pacchetti si riscaricano una
    volta a settimana, gli altri giorni basta la copia versionata. Se i
    pacchetti non arrivano, o arrivano molto piu' magri del solito, vince la
    copia: e' un guasto travestito da successo."""
    vecchia = None
    if os.path.exists(ISTANTANEA):
        vecchia = json.load(open(ISTANTANEA, encoding='utf-8'))
    if vecchia and not forza:
        quando = vecchia.get('_scaricato', '')
        if quando and (oggi - _giorno(quando)).days < GIORNI_FRA_UN_GIRO_E_LALTRO:
            print('  anagrafe della Camera del %s: ancora buona' % quando)
            return vecchia
    try:
        nuova = costruisci()
        nuova['_scaricato'] = oggi.isoformat()
    except Exception as e:
        sys.stderr.write('  anagrafe della Camera non scaricata (%s): '
                         'uso la copia versionata.\n' % e)
        return vecchia or {}
    if vecchia and len(nuova) < len(vecchia) * 0.8:
        sys.stderr.write('  ATTENZIONE: anagrafe della Camera con %d voci contro '
                         'le %d note: uso la copia versionata.\n'
                         % (len(nuova), len(vecchia)))
        return vecchia
    os.makedirs(os.path.dirname(ISTANTANEA), exist_ok=True)
    json.dump(nuova, open(ISTANTANEA, 'w', encoding='utf-8'), ensure_ascii=False,
              sort_keys=True, separators=(',', ':'))
    return nuova


# Per molti deputati dei primi anni la Camera non ha la foto e serve al suo
# posto un'immagine con scritto "Immagine non disponibile", sempre la stessa;
# per altri il collegamento non porta a niente. Ogni foto si controlla una
# volta sola, e l'esito resta in data/registri/camera_foto.json.
SEGNAPOSTO = {'93274d1b9187'}
ESITI_FOTO = os.path.join(QUI, '..', 'data', 'registri', 'camera_foto.json')


def foto_vere(indirizzi):
    import hashlib
    import concurrent.futures
    esiti = json.load(open(ESITI_FOTO, encoding='utf-8')) if os.path.exists(ESITI_FOTO) else {}

    def prova(u):
        try:
            r = urllib.request.Request(u, headers={
                'User-Agent': 'DuriAMorire/0.1 (progetto personale)'})
            b = urllib.request.urlopen(r, timeout=60).read()
        except Exception:
            return u, False
        return u, len(b) > 3000 and hashlib.sha1(b).hexdigest()[:12] not in SEGNAPOSTO

    nuovi = sorted({u for u in indirizzi if u not in esiti})
    if nuovi:
        with concurrent.futures.ThreadPoolExecutor(6) as ex:
            for u, ok in ex.map(prova, nuovi):
                esiti[u] = ok
        json.dump(esiti, open(ESITI_FOTO, 'w', encoding='utf-8'), sort_keys=True, indent=0)
    print('  foto della Camera: %d controllate ora, %d vere su %d'
          % (len(nuovi), sum(1 for u in indirizzi if esiti.get(u)), len(set(indirizzi))))
    return {u for u in indirizzi if esiti.get(u)}


def aggancia(persone, anagrafe_camera, chiave, alias=None):
    """Lega ogni nostra scheda alla sua voce d'anagrafe.

    Chi e' passato dalla Camera ha gia' il suo identificativo, ed e' lo stesso
    dell'anagrafe. Per gli altri, cioe' i senatori che alla Camera non sono
    mai stati e i tecnici di Ciampi e Dini, vale la regola di sempre: nome
    piu' una legislatura (o un governo) in comune. Mai la sola omonimia."""
    per_nome = {}
    for pid, v in anagrafe_camera.items():
        if pid.startswith('_'):
            continue
        per_nome.setdefault(chiave(v['nome'], v['cognome']), []).append(pid)
    agganciati = 0
    for p in persone.values():
        pid = p.get('id_camera') if p.get('id_camera') in anagrafe_camera else None
        if not pid:
            miei = set(p['mandati'])
            candidati = []
            # 'Antonio Calì (politico)': la precisazione di Wikipedia non e' un
            # nome. E il nome con cui la Camera conosce chi Wikidata chiama in
            # un altro modo (Rosa Russo Iervolino per lei e' Rosa Jervolino
            # Russo) sta nel file degli alias.
            nomi = {re.sub(r'\s*\([^)]*\)', '', p['nome'] or '')}
            if alias and alias.get(p['qid']):
                nomi.add(alias[p['qid']])
            per_questi = {c for n in nomi for c in per_nome.get(chiave(n), [])}
            for c in sorted(per_questi):
                v = anagrafe_camera[c]
                suoi = set(v['leg']) | {GOVERNI_PERIMETRO[i['governo'].split(' ')[0]]
                                        for i in v.get('governo', [])
                                        if i['governo'].split(' ')[0] in GOVERNI_PERIMETRO}
                if miei & suoi:
                    candidati.append(c)
            # due omonimi nelle stesse legislature: meglio niente che il sbagliato
            pid = candidati[0] if len(candidati) == 1 else None
        if not pid:
            continue
        v = anagrafe_camera[pid]
        p['anagrafe_camera'] = pid
        p['genere'] = 'f' if v.get('donna') else 'm'
        for campo, mio in (('studi', 'studi'), ('foto', 'foto_camera'),
                           ('consulta', 'consulta'), ('governo', 'incarichi_governo')):
            if v.get(campo):
                p[mio] = v[campo]
        # La pagina sul portale storico della Camera: nome e cognome come li
        # scrive il registro, e la data di nascita. 'D'ALEMA' diventa 'd-alema',
        # l'accento finale di 'SCHIRO'' cade.
        if p.get('id_camera') and len(p.get('nascita_camera') or '') == 10:
            nome = ('%s %s' % (v['nome'], v['cognome'])).lower()
            nome = re.sub(r"'(?=[a-z])", '-', nome).replace("'", '')
            nome = re.sub(r'\s+', '-', nome.strip())
            p['storia_camera'] = '%s-%s' % (nome, p['nascita_camera'].replace('-', ''))
        # le elezioni alla Camera: {legislatura: ['C', luogo]}
        for leg, luogo in (v.get('elezioni') or {}).items():
            p.setdefault('elezioni', {})[leg] = ['C', luogo]
        agganciati += 1
    print('  %d schede legate all\'anagrafe della Camera' % agganciati)
    # La foto della Camera serve solo a chi su Wikimedia non ne ha una: si
    # controllano quelle, e si tengono solo le vere.
    servono = [p['foto_camera'] for p in persone.values()
               if p.get('foto_camera') and not p.get('foto')]
    vere = foto_vere(servono)
    for p in persone.values():
        if p.get('foto_camera') and (p.get('foto') or p['foto_camera'] not in vere):
            del p['foto_camera']
    return agganciati
