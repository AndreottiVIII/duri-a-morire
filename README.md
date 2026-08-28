# Duri a morire — Prima Repubblica edition

Chi è ancora vivo, tra i parlamentari e i ministri della Prima Repubblica.
Si aggiorna da solo. Ha il sapore del Televideo.

## Decisioni prese

**Ambito.** Assemblea Costituente (1946) più le legislature I–XI (1948–1994).
In coda i ministri dei governi Ciampi e Dini anche se non eletti in Parlamento.
La XII legislatura resta fuori: è già Seconda Repubblica.

**I non eletti stanno "sulla porta".** Tecnici, banchieri, sindacalisti e
segretari di partito entrano ma restano marcati come tali.

**Tre stati, non due.** Vivente, deceduto, e *sorte ignota*: chi non ha una data
di morte da nessuna parte ma avrebbe più di 106 anni non è un vivente, è un buco
nei dati. Sono 52 persone. La soglia si cambia in configurazione.

**Hall of fame congelata.** I 66 nomi curati a mano restano quelli: nessuno viene
aggiunto in automatico. Ad aggiornarsi da solo è soltanto il loro stato vivo/morto.
Vivono in `data/hall_of_fame.json`, separati dall'elenco grande.

**Fonte.** Wikidata, che è la versione interrogabile di Wikipedia. Copre l'intero
perimetro: 4.414 parlamentari, 99,98% con data di nascita. Gli aggiornamenti
vengono pubblicati senza approvazione manuale.

**Estetica.** Televideo RAI. Le pagine numerate non sono decorazione: sono il
sistema di navigazione, e sono la risposta al problema di far scorrere 897 nomi.

**Distribuzione.** Prima un sito statico generato in locale, senza installazioni
né account. Poi, se piace, lo stesso repo su hosting gratuito con un job notturno.

## Com'è messa la truppa

| | |
|---|---|
| Censiti in tutto | 4.616 |
| Viventi | 913 |
| Deceduti | 3.650 |
| Sorte ignota | 53 |

La Costituente e la I legislatura sono estinte al completo: l'ultimo costituente
è stato Emilio Colombo, morto il 24 giugno 2013.

Il partito è noto per 714 viventi su 913: per gli altri Wikidata non lo registra,
e la colonna resta vuota invece di inventarselo.

## Script

- `scripts/wd.py` — utility per Wikidata (API di ricerca + SPARQL)
- `scripts/aggancia_hall_of_fame.py` — collega i 66 nomi curati ai record Wikidata
- `scripts/scarica_elenco.py` — scarica l'elenco grande in `data/elenco.json`
- `scripts/genera_sito.py` + `scripts/modello.html` — costruiscono `sito/index.html`

Le risposte di Wikidata restano in `data/cache/`: rigenerare il sito non ribussa
all'endpoint. Per riscaricare tutto da capo, svuota quella cartella.

## Come si usa

```
python scripts/scarica_elenco.py
python scripts/genera_sito.py
```

Poi si apre `sito/index.html` con un doppio clic. È un file unico e autoportante:
niente server, niente installazioni. Le foto arrivano da Wikimedia Commons.

## Le pagine

    100  indice                200  statistiche
    101  viventi               210  sopravvissuti per partito
    110  per legislatura       220  curva di estinzione
    111  ...124 una per leg.   230  l'ultimo dei...
    150  ricerca               300  in memoriam
    500  compleanni            400  sorte ignota

    600  ricontrollo dal vivo su Wikidata

    sezione hall of fame
    130  indice della sezione  133  per partito
    131  ancora in piedi       134  compleanni
    132  in memoriam           135  i cursus piu lunghi

## Il tasto AGGIORNA

La pagina 600 (e il tasto AGGIORNA in fondo) interroga Wikidata dal browser e
ricontrolla, una per una, le persone date per viventi o di sorte ignota. Chi nel
frattempo e' morto viene spostato subito, e il risultato resta nel browser di chi
guarda: il file su disco non viene toccato, e per renderlo definitivo si rilanciano
i due script.

Funziona solo se il sito e' servito da un indirizzo (il server locale, o l'hosting).
Aperto col doppio clic dal disco il browser blocca le chiamate verso l'esterno, e
la pagina 600 lo dice invece di fallire in silenzio.

## Il partito dei 66

Per la hall of fame comanda la colonna scritta a mano nel file originale, non
Wikidata: e' una scelta editoriale su quale partito definisca quella persona in
quegli anni. Wikidata elenca anche le militanze successive, e senza questa regola
Pizzinato risultava PCI invece che PDS, Raffaele Costa Forza Italia invece che PLI,
Leoluca Orlando DC invece che La Rete, mentre Rete, Verdi e Radicali sparivano.
