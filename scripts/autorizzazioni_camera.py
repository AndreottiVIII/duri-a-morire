"""Le domande di autorizzazione a procedere e all'arresto contro i deputati,
dalle Banche dati professionali della Camera (bdp.camera.it, ex 3270).

Per la IX, la X e la XI legislatura (1983-1994) l'archivio dell'attivita'
non legislativa registra ogni domanda annunziata in Assemblea: contro chi
(cognome e gruppo), per quale reato, il numero del documento (doc. IV) e,
quando c'e', com'e' finita ("AUTORIZZAZIONE CONCESSA IL 24 GIUGNO 1992").
Prima del 1983 questo archivio non c'e'.

Si lancia a mano, una pagina al secondo: le schede sono un migliaio e
mezzo e il server e' della Camera, non nostro. Riprende da dove si era
fermato. Scrive data/registri/camera_autorizzazioni.json.
"""
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request

QUI = os.path.dirname(os.path.abspath(__file__))
USCITA = os.path.join(QUI, '..', 'data', 'registri', 'camera_autorizzazioni.json')
BASE = 'https://bdp.camera.it/init/di%s/'
LEGISLATURE = {'09': 'IX', '10': 'X', '11': 'XI'}
TIPI = {'procedere': 'Domande di autorizzazioni a procedere annunziate',
        'arresto': "Domande di autorizzazione all'arresto annunziate"}
PAUSA = 1.0


def leggi(url):
    for tentativo in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'primarepubblica.net'})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception:
            time.sleep(10 * (tentativo + 1))
    raise RuntimeError('non risponde: ' + url)


def testo(s):
    t = html.unescape(re.sub(r'<[^>]+>', '\n', s))
    return re.sub(r'\n\s*\n+', '\n', t)


def schede_di(leg, tipo):
    """Gli id delle schede di una ricerca, pagina per pagina (30 a pagina)."""
    ids, pagina = [], 0
    while True:
        q = {'attivita': TIPI[tipo]}
        if pagina:
            q['page'] = pagina
        s = leggi(BASE % leg + 'ricercaAttivita?' + urllib.parse.urlencode(q))
        nuovi = re.findall(r'/init/di%s/scheda/(\d+)' % leg, s)
        if not nuovi:
            break
        ids += [i for i in nuovi if i not in ids]
        if 'successivo' not in s:
            break
        pagina += 1
        time.sleep(PAUSA)
    return ids


def campo(t, nome, dopo):
    m = re.search(r'\n%s:\s*\n(.*?)\n%s:' % (nome, dopo), t, re.S)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''


def scheda(leg, id_):
    t = testo(leggi(BASE % leg + 'scheda/' + id_))
    argomento = campo(t, 'Argomento', 'Interventi')
    contro = campo(t, 'Contro', 'Presentatori')
    data = campo(t, 'Data', 'Argomento').split(' ')[0]
    doc = re.search(r'doc\.\s*IV(?:-ter)?,\s*n\.\s*(\d+)', argomento)
    # com'e' finita sta in maiuscolo dopo il numero del documento
    esito = argomento[doc.end():].lstrip(').; ') if doc else ''
    return {'leg': LEGISLATURE[leg], 'id': id_, 'data': data,
            'doc': doc.group(1) if doc else '', 'contro': contro,
            'argomento': argomento, 'esito': esito}


def main():
    fatto = json.load(open(USCITA, encoding='utf-8')) if os.path.exists(USCITA) else []
    visti = {(r['leg'], r['id']) for r in fatto}
    for leg in LEGISLATURE:
        for tipo in TIPI:
            ids = schede_di(leg, tipo)
            print('%s %s: %d domande' % (LEGISLATURE[leg], tipo, len(ids)), flush=True)
            for n, id_ in enumerate(ids, 1):
                if (LEGISLATURE[leg], id_) in visti:
                    continue
                r = scheda(leg, id_)
                r['tipo'] = tipo
                fatto.append(r)
                visti.add((r['leg'], id_))
                if n % 50 == 0:
                    json.dump(fatto, open(USCITA, 'w', encoding='utf-8'),
                              ensure_ascii=False, indent=0)
                    print('  %d/%d' % (n, len(ids)), flush=True)
                time.sleep(PAUSA)
            json.dump(fatto, open(USCITA, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('fatto: %d domande' % len(fatto))


def _norm(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', s or '').upper()
    return re.sub(r'[^A-Z]', '', ''.join(c for c in s if not unicodedata.combining(c)))


def esito(r):
    e = r.get('esito', '').upper()
    if 'CONCESSA' in e:
        return 'concessa'
    if 'NEGATA' in e:
        return 'negata'
    if 'RESTITUZIONE' in e or 'RINVIO' in e:
        return 'restituita'
    return ''


def aggancia(persone, anagrafe_camera, domande=None):
    """Contro chi: 'CASALINUOVO (PSI), PERUGINI (DC)'. Il cognome deve essere
    di un solo deputato di quella legislatura; se sono due, decidono il nome
    (quando c'e') e il gruppo di allora. Altrimenti la domanda resta fuori.
    p['autorizzazioni'] = [[leg, data, tipo, doc, esito, reato]]."""
    if domande is None:
        domande = json.load(open(USCITA, encoding='utf-8')) if os.path.exists(USCITA) else []
    per_cognome = {}
    for p in persone.values():
        v = anagrafe_camera.get(p.get('anagrafe_camera') or '')
        if v:
            per_cognome.setdefault(_norm(v['cognome']), []).append((p, v))
    trovate = mancate = 0
    for d in domande:
        contro = re.sub(r'\.\s*domanda annunziata.*$', '', d['contro'])
        reato = re.sub(r'\s*\(doc\..*$', '', d['argomento']).strip()
        for chi in re.findall(r'([^,(]+?)\s*\(([^)]*)\)', contro):
            nome, gruppo = chi[0].strip(), _norm(chi[1])
            parti = nome.split(' ')
            cognome = ' '.join(x for x in parti if x.isupper() and len(x) > 1) or nome
            battesimo = _norm(' '.join(x for x in parti if not x.isupper()))
            tutti = [(p, v) for p, v in per_cognome.get(_norm(cognome), [])
                     if d['leg'] in (p.get('mandati') or [])
                     and (p.get('elezioni') or {}).get(d['leg'], ['C'])[0] == 'C']
            if len(tutti) > 1 and battesimo:
                tutti = [(p, v) for p, v in tutti if _norm(v['nome']).startswith(battesimo)]
            if len(tutti) > 1:
                tutti = [(p, v) for p, v in tutti
                         if any(_norm(g[2]) == gruppo for g in p.get('gruppi') or []
                                if g[0] == d['leg'])]
            if len(tutti) == 1:
                p = tutti[0][0]
                riga = [d['leg'], d['data'], d['tipo'], d['doc'], esito(d), reato]
                if riga not in p.setdefault('autorizzazioni', []):
                    p['autorizzazioni'].append(riga)
                trovate += 1
            else:
                mancate += 1
    print('  autorizzazioni a procedere: %d agganciate, %d no' % (trovate, mancate))
    return trovate, mancate


if __name__ == '__main__':
    main()
