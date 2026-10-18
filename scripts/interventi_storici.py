# -*- coding: utf-8 -*-
"""Quanti interventi in aula ha fatto ogni deputato, dal portale storico
della Camera.

Gli open data della Camera registrano chi ha parlato solo dal 2008; per gli
anni prima il conto sta soltanto sulla pagina di ogni deputato del portale
storico (storia.camera.it), che scrive per esempio "visualizza tutti i 9
interventi di Giuseppe Sales". Questo programma le legge una per volta, con
calma: una pagina al secondo, per non pesare sul loro sito. Non fa parte del
lavoro notturno: si lancia a mano, una volta, e il risultato resta in
data/registri/camera_interventi.json. Se si interrompe riprende da dove era.

    python scripts/interventi_storici.py
"""
import json
import os
import re
import sys
import time
import urllib.request

QUI = os.path.dirname(os.path.abspath(__file__))
ELENCO = os.path.join(QUI, '..', 'data', 'elenco.json')
USCITA = os.path.join(QUI, '..', 'data', 'registri', 'camera_interventi.json')
PAUSA = 1.0

INTERVENTI = re.compile(r'visualizza tutti i (\d+) interventi di')
PROGETTI = re.compile(r'visualizza tutti i (\d+) Progetti di legge di')


def leggi(slug):
    r = urllib.request.Request('https://storia.camera.it/deputato/' + slug,
                               headers={'User-Agent': 'DuriAMorire/0.1 (progetto personale)'})
    html = urllib.request.urlopen(r, timeout=60).read().decode('utf-8', 'replace')
    if '/deputato/' + slug not in html:
        return {'errore': 'pagina non trovata'}
    m, n = INTERVENTI.search(html), PROGETTI.search(html)
    return {'interventi': int(m.group(1)) if m else 0,
            'progetti': int(n.group(1)) if n else 0}


def main():
    persone = json.load(open(ELENCO, encoding='utf-8'))['persone']
    slugs = sorted({p['storia_camera'] for p in persone if p.get('storia_camera')})
    fatti = json.load(open(USCITA, encoding='utf-8')) if os.path.exists(USCITA) else {}
    da_fare = [s for s in slugs if s not in fatti or 'errore' in fatti[s]]
    print('%d pagine in tutto, %d da leggere' % (len(slugs), len(da_fare)), flush=True)
    for i, s in enumerate(da_fare, 1):
        try:
            fatti[s] = leggi(s)
        except Exception as e:
            fatti[s] = {'errore': str(e)[:80]}
        if i % 50 == 0 or i == len(da_fare):
            json.dump(fatti, open(USCITA, 'w', encoding='utf-8'), sort_keys=True, indent=0)
            print('  %d/%d' % (i, len(da_fare)), flush=True)
        time.sleep(PAUSA)
    errori = sum(1 for v in fatti.values() if 'errore' in v)
    print('finito: %d pagine lette, %d errori' % (len(fatti), errori), flush=True)


if __name__ == '__main__':
    main()
