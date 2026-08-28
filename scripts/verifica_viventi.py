# -*- coding: utf-8 -*-
"""Passa in rassegna chi risulta vivente e chiede conto ai registri ufficiali.

Non basta che Wikidata taccia sulla morte di qualcuno: il silenzio non e' una
prova di vita. Qui ogni vivente viene cercato nel registro della Camera o del
Senato, e finisce in una di tre categorie:

  confermato   il registro lo conosce e non lo da' per morto
  non trovato  nessun registro lo aggancia: il suo essere vivo non e' verificato
  fuori        non e' mai stato eletto (i tecnici dei governi Ciampi e Dini)

Chi non torna per nome viene ricercato una seconda volta per legislatura piu'
data di nascita esatta: per la Camera e' VIRGINIO SCOTTI, per Wikidata Gerry
Scotti, ma il seggio e il giorno di nascita sono gli stessi.
"""
import sys, os, json, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import camera, senato

QUI = os.path.dirname(os.path.abspath(__file__))
ELENCO = os.path.join(QUI, '..', 'data', 'elenco.json')


def spoglio(s):
    s = unicodedata.normalize('NFKD', (s or '').lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def main():
    dati = json.load(open(ELENCO, encoding='utf-8'))
    vivi = [p for p in dati['persone'] if p['stato'] == 'vivente']

    registri = []
    for etichetta, modulo in [('Camera', camera), ('Senato', senato)]:
        try:
            reg = modulo.registro()
            registri.append((etichetta, modulo, reg, modulo.indice_per_data(reg),
                             modulo.indice_per_mandato(reg)))
        except Exception as e:
            print('%s non raggiungibile: %s' % (etichetta, e))

    per_nome, per_data, fuori, muti = [], [], [], []
    for p in vivi:
        # Un ministro tecnico non ha mai avuto un seggio: nessun registro
        # parlamentare puo' confermarlo, e non e' un buco nei dati.
        eletto = [m for m in p['mandati'] if not m.startswith('Governo')]
        if not eletto:
            fuori.append(p)
            continue
        esito = None
        for etichetta, modulo, reg, indice, per_mandato in registri:
            v, come = modulo.cerca_ampia(reg, indice, p['nome'], p['nascita'],
                                         eletto, per_mandato)
            if v:
                esito = (etichetta, come, v)
                break
        if not esito:
            muti.append(p)
        elif esito[1] != 'nome':
            per_data.append((p, esito))
        else:
            per_nome.append((p, esito))

    print('VIVENTI PASSATI IN RASSEGNA: %d' % len(vivi))
    print('  confermati vivi dal registro, per nome        %4d' % len(per_nome))
    print('  confermati vivi, ritrovati per altra via      %4d' % len(per_data))
    print('  mai eletti: nessun registro li contiene        %4d' % len(fuori))
    print('  NON AGGANCIATI: la vita non e verificata  %4d' % len(muti))
    print()
    if per_data:
        print('RITROVATI CON I CRITERI PIU LARGHI (nome diverso fra le fonti):')
        for p, e in per_data[:12]:
            print('  %-30s n.%-11s %s, per %s' % (p['nome'], p['nascita'], e[0], e[1]))
        print()
    print('NON AGGANCIATI, dal piu anziano:')
    for p in sorted(muti, key=lambda x: x['nascita'] or '9')[:30]:
        print('  %-28s n.%-11s %s' % (p['nome'], p['nascita'],
                                      ', '.join(p['mandati'])))


if __name__ == '__main__':
    main()
