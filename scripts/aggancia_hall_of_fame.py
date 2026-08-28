# -*- coding: utf-8 -*-
"""Aggancia i nomi curati della hall of fame ai record Wikidata.

La lista e' congelata nell'appartenenza: chi c'e' resta, nessuno viene aggiunto
in automatico. Quello che si aggiorna da solo e' lo stato vivo/morto, che
d'ora in poi arriva da Wikidata e non piu' dalla colonna scritta a mano.
"""
import sys, os, json, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import openpyxl, wd

XLSX = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    '..', 'dati-originali', 'Duri a morire - I repubblica 2022.xlsx')
USCITA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '..', 'data', 'hall_of_fame.json')

# Nomi che la ricerca per stringa non risolve da sola: forma estesa o omonimie.
ALIAS = {
    'Vincenza Bono': 'Vincenza Bono Parrino',
}


def leggi_xlsx():
    ws = openpyxl.load_workbook(XLSX, data_only=True)['Sheet1']
    righe = []
    for r in list(ws.iter_rows(values_only=True))[1:]:
        if not r[0] or not str(r[0]).strip():
            continue
        righe.append({
            'nome': str(r[0]).strip(),
            'nato_file': r[1],
            'morto_file': r[2].strftime('%Y-%m-%d') if r[2] else None,
            'partito': (str(r[3]).strip() if r[3] else None),
            'cursus': (str(r[4]).strip() if r[4] else None),
        })
    return righe


def normalizza(s):
    s = unicodedata.normalize('NFKD', s.lower())
    return ''.join(c for c in s if not unicodedata.combining(c)).strip()


def scegli(voce, candidati, ents):
    """Punteggio: l'anno di nascita del file e' il disambiguatore forte."""
    migliore, punteggio_max = None, -1
    for pos, qid in enumerate(candidati):
        ent = ents.get(qid, {})
        if 'Q5' not in [v.get('id') for v in wd.valori(ent, 'P31')]:
            continue  # non e' una persona
        p = 0
        nascita = wd.data_di(ent, 'P569')
        if nascita and voce['nato_file'] and nascita[:4] == str(voce['nato_file']):
            p += 10
        if 'Q38' in [v.get('id') for v in wd.valori(ent, 'P27')]:
            p += 2
        if ent.get('sitelinks', {}).get('itwiki'):
            p += 1
        if normalizza(wd.etichetta(ent) or '') == normalizza(voce['nome']):
            p += 2
        p += max(0, 3 - pos) * 0.1  # a parita', il primo risultato
        if p > punteggio_max:
            migliore, punteggio_max = qid, p
    return migliore, punteggio_max


def main():
    voci = leggi_xlsx()
    print('Nomi nel file: %d' % len(voci))

    tutti_candidati, per_voce = [], {}
    for v in voci:
        c = wd.cerca(ALIAS.get(v['nome'], v['nome']))
        per_voce[v['nome']] = c
        tutti_candidati += c
    print('Candidati Wikidata raccolti: %d' % len(set(tutti_candidati)))

    ents = wd.entita(sorted(set(tutti_candidati)))

    risultato = []
    for v in voci:
        qid, punteggio = scegli(v, per_voce[v['nome']], ents)
        ent = ents.get(qid, {}) if qid else {}
        v.update({
            'wikidata': qid,
            'confidenza': ('alta' if punteggio >= 10 else
                           'da_verificare' if qid else 'non_trovato'),
            'etichetta_wd': wd.etichetta(ent) if qid else None,
            'nascita_wd': wd.data_di(ent, 'P569') if qid else None,
            'morte_wd': wd.data_di(ent, 'P570') if qid else None,
            'foto': (wd.valori(ent, 'P18') or [None])[0] if qid else None,
            'wikipedia': (('https://it.wikipedia.org/wiki/' +
                           ent['sitelinks']['itwiki']['title'].replace(' ', '_'))
                          if ent.get('sitelinks', {}).get('itwiki') else None),
        })
        risultato.append(v)

    with open(USCITA, 'w', encoding='utf-8') as f:
        json.dump(risultato, f, ensure_ascii=False, indent=2)
    print('Scritto %s' % os.path.normpath(USCITA))
    return risultato


if __name__ == '__main__':
    main()
