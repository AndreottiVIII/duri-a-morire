# -*- coding: utf-8 -*-
"""Prepara i testi di confronto: clona il corpus biblico e ne estrae i campioni.

Le trascrizioni del Voynich stanno gia' nel repository (dati/trascrizioni/);
le cento Bibbie no, pesano troppo. Questo script le scarica una volta sola,
al commit fissato in analisi/lingue.py, e scrive i testi normalizzati in
dati/cache/lingue/, che git ignora.

    python3 voynich/prepara.py
"""
import os, subprocess, sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(QUI, 'analisi'))
import lingue

URL = 'https://github.com/christos-c/bible-corpus'
COMMIT_PIENO = '44e5fca1bfb369a5da2ee23ebc6f421c88489c5c'


def git(*argomenti, cwd=None):
    subprocess.check_call(['git'] + list(argomenti), cwd=cwd)


def fissa(url, cartella, commit):
    """Clona (se serve) e porta la copia locale esattamente al commit indicato."""
    if not os.path.isdir(os.path.join(cartella, '.git')):
        git('clone', '--depth', '1', url, cartella)
    attuale = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=cartella).decode().strip()
    if attuale != commit:
        git('fetch', '--depth', '1', 'origin', commit, cwd=cartella)
        git('checkout', '--quiet', commit, cwd=cartella)


def main():
    fissa(URL, lingue.SORGENTE, COMMIT_PIENO)
    fissa('https://github.com/cltk/lat_text_latin_library', lingue.LATIN_LIBRARY, lingue.COMMIT_LL)
    indice = lingue.prepara()
    lingue.prepara_pinyin()
    indice = lingue.indice()
    corte = [k for k, v in indice.items() if v['caratteri'] < 250_000]
    print('%d lingue pronte in %s' % (len(indice), os.path.normpath(lingue.CACHE)))
    if corte:
        print('troppo corte per il confronto alla pari: %s' % ', '.join(corte))


if __name__ == '__main__':
    main()
