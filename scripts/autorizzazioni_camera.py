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


if __name__ == '__main__':
    main()
