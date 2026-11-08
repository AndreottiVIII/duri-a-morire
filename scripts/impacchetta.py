# -*- coding: utf-8 -*-
"""L'elenco delle persone, impacchettato per stare sotto i 2 MB.

Google legge solo i primi 2 MB di ogni file, programma compreso: oltre, il
Televideo arriva a meta' e la pagina resta vuota (e' cio' che e' successo a
Seconda Repubblica Tracker il 22/10/2026). I dati sono la quasi totalita'
del programma, quindi si scrivono piu' corti, senza togliere niente:

- le chiavi di ogni persona non si ripetono: c'e' un elenco di "schemi"
  (le chiavi nell'ordine giusto) e ogni persona e' una riga di valori, che
  comincia col numero del suo schema;
- i valori che si ripetono uguali in una colonna (date, partiti, mandati...)
  stanno una volta sola in un vocabolario, e nella riga c'e' il numero;
  oppure, per le colonne fatte solo di testi, sono i singoli testi ripetuti
  (incarichi, luoghi, governi) a stare nel vocabolario;
- foto e voce di Wikipedia perdono l'inizio e la fine sempre uguali.

Il programma (modello.html, spacchetta) ricompone l'elenco identico appena
parte. Qui, prima di consegnare, lo si ricompone anche in Python e si
controlla che sia uguale all'originale, chiave per chiave e nell'ordine: se
non lo e', ci si ferma.
"""
import collections
import json

FOTO_INIZIO = 'https://commons.wikimedia.org/wiki/Special:FilePath/'
FOTO_FINE = '?width=260'
VOCE_INIZIO = 'https://it.wikipedia.org/wiki/'

J = lambda x: json.dumps(x, ensure_ascii=False, separators=(',', ':'))


def _numero(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _foglie(v):
    if isinstance(v, list):
        for x in v:
            yield from _foglie(x)
    elif isinstance(v, dict):
        for x in v.values():
            yield from _foglie(x)
    else:
        yield v


def _accorcia(k, v):
    if k == 'f' and isinstance(v, str):
        if not v.startswith('http'):
            raise SystemExit('Foto senza indirizzo completo: %r' % v)
        if v.startswith(FOTO_INIZIO) and v.endswith(FOTO_FINE):
            return v[len(FOTO_INIZIO):-len(FOTO_FINE)]
    if k == 'w' and isinstance(v, str):
        if not v.startswith('http'):
            raise SystemExit('Voce di Wikipedia senza indirizzo completo: %r' % v)
        if v.startswith(VOCE_INIZIO):
            return v[len(VOCE_INIZIO):]
    return v


def _allunga(k, v):
    if k == 'f' and isinstance(v, str) and not v.startswith('http'):
        return FOTO_INIZIO + v + FOTO_FINE
    if k == 'w' and isinstance(v, str) and not v.startswith('http'):
        return VOCE_INIZIO + v
    return v


def _scegli_modi(persone):
    colonne = collections.defaultdict(list)
    for p in persone:
        for k, v in p.items():
            colonne[k].append(_accorcia(k, v))
    modi = {}
    for k, vs in colonne.items():
        meglio = (0, None, None)
        # valori interi ripetuti: solo se nella colonna non ci sono numeri,
        # perche' nella riga un numero vuol dire "voce del vocabolario"
        if not any(_numero(v) for v in vs):
            conta = collections.Counter(J(v) for v in vs)
            voci = sorted((s for s, n in conta.items() if n > 1 and len(s) > 2),
                          key=lambda s: (-conta[s], s))
            guadagno = sum(conta[s] * (len(s.encode()) - len(str(j))) - len(J(s).encode()) - 1
                           for j, s in enumerate(voci))
            if guadagno > meglio[0]:
                meglio = (guadagno, 'v', voci)
        # testi ripetuti dentro elenchi: solo se le foglie sono tutte testi
        if (any(isinstance(v, (list, dict)) for v in vs)
                and all(x is None or isinstance(x, str) for v in vs for x in _foglie(v))):
            conta = collections.Counter(x for v in vs for x in _foglie(v) if isinstance(x, str))
            voci = sorted((s for s, n in conta.items() if n > 1 and len(s) > 2),
                          key=lambda s: (-conta[s], s))
            guadagno = sum(conta[s] * (len(J(s).encode()) - len(str(j))) - len(J(s).encode()) - 1
                           for j, s in enumerate(voci))
            if guadagno > meglio[0]:
                meglio = (guadagno, 'f', voci)
        if meglio[0] > 2000:
            modi[k] = [meglio[1], meglio[2]]
    return modi


def _dentro(x, posto):
    if isinstance(x, list):
        return [_dentro(y, posto) for y in x]
    if isinstance(x, dict):
        return {a: _dentro(b, posto) for a, b in x.items()}
    if isinstance(x, str):
        return posto.get(x, x)
    return x


def _fuori(x, voci):
    if _numero(x):
        return voci[x]
    if isinstance(x, list):
        return [_fuori(y, voci) for y in x]
    if isinstance(x, dict):
        return {a: _fuori(b, voci) for a, b in x.items()}
    return x


def spacchetta(pacco):
    """Lo stesso lavoro di spacchetta() in modello.html: serve al controllo."""
    modi, persone = pacco['modi'], []
    for riga in pacco['righe']:
        p = {}
        for k, v in zip(pacco['schemi'][riga[0]], riga[1:]):
            m = modi.get(k)
            if m and m[0] == 'v' and _numero(v):
                v = json.loads(m[1][v])
            elif m and m[0] == 'f':
                v = _fuori(v, m[1])
            p[k] = _allunga(k, v)
        persone.append(p)
    return persone


def impacchetta(persone):
    modi = _scegli_modi(persone)
    posti = {k: {s: j for j, s in enumerate(m[1])} for k, m in modi.items()}
    schemi, numero_schema, righe = [], {}, []
    for p in persone:
        chiavi = tuple(p.keys())
        if chiavi not in numero_schema:
            numero_schema[chiavi] = len(schemi)
            schemi.append(list(chiavi))
        riga = [numero_schema[chiavi]]
        for k, v in p.items():
            v = _accorcia(k, v)
            m = modi.get(k)
            if m and m[0] == 'v':
                v = posti[k].get(J(v), v)
            elif m and m[0] == 'f':
                v = _dentro(v, posti[k])
            riga.append(v)
        righe.append(riga)
    pacco = {'schemi': schemi, 'modi': modi, 'righe': righe}
    # il controllo: ricomposto deve essere identico, anche nell'ordine delle chiavi
    rifatto = spacchetta(json.loads(J(pacco)))
    if len(rifatto) != len(persone) or any(
            list(a.items()) != list(b.items()) for a, b in zip(rifatto, persone)):
        raise SystemExit('Impacchettando le persone qualcosa cambia: mi fermo.')
    return pacco


def dati_impacchettati(dati):
    """I dati per il programma, con le persone impacchettate, come testo JSON."""
    return J(dict(dati, persone=impacchetta(dati['persone'])))
