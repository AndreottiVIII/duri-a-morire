# Duri a morire — Prima Repubblica edition

Chi è ancora vivo, tra i parlamentari e i ministri della Prima Repubblica.
Si aggiorna da solo. Ha il sapore del Televideo.

**https://andreottiviii.github.io/duri-a-morire/**

Ogni notte un lavoro automatico riscarica i dati da Wikidata, ricostruisce il
sito e lo ripubblica. Committa solo quando è cambiato qualcosa di vero, così la
cronologia del repository è il registro di chi se n'è andato e quando.

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

**Due fonti.** Wikidata, che è la versione interrogabile di Wikipedia, copre
l'intero perimetro ed è rapida sui personaggi noti. Ma sui deputati di seconda
fila è cieca: di parecchi non registra la morte, e quelli restavano per sempre
fra i viventi — Giuseppe Sasso risultava vivo a 106 anni ed era morto nel 2015.
Il secondo controllo sono gli open data della **Camera dei deputati**, che tiene
il registro dei propri ex e sa quello che Wikidata ignora: 148 decessi recuperati
al primo incrocio. I due nomi vengono accoppiati solo se coincide anche l'anno di
nascita, altrimenti si finisce per seppellire un vivo al posto del suo omonimo
deputato del Regno. Gli aggiornamenti vengono pubblicati senza approvazione
manuale.

Terzo controllo, dall'altra parte del Parlamento: gli open data del **Senato**,
che la Camera per forza di cose ignora. Ne aggiunge altri 9 — pochi perché molti
senatori di quegli anni erano stati prima deputati, e la Camera li aveva già
coperti.

**Come si agganciano i nomi.** Per nome piu' legislatura in comune, mai per data
di nascita: e' proprio quella che a volte sbaglia Wikidata, e usarla come prova
d'identita' lascerebbe in vita chi ce l'ha storta — Giovanni Battista Melis su
Wikidata risulta del 1922, alla Camera del 1904, e ha ragione la Camera. Dentro
la Camera invece l'aggancio e' esatto: l'URI del deputato per una legislatura
(`d19930_4`) contiene l'identificativo della persona (`p19930`), che porta le
date. Chi non torna per nome viene ricercato per legislatura piu' data di nascita
esatta, e in ultimo per nome contenuto nell'altro — i registri accorciano i
cognomi da sposata, e `LODI ADRIANA` sta dentro `Adriana Lodi Faustini Fustini`.

**Doppioni.** Stesso nome e stessa legislatura vuol dire stessa persona: su
Wikidata capita che qualcuno compaia due volte, una col record buono e una con
una scheda spoglia e la nascita sbagliata, e quel secondo esemplare non muore
mai. Omonimi veri ne esistono (due Giuseppe Leoni, due Arturo Marzano), ma
stanno in legislature diverse. Dieci doppioni fusi.

In tutto: 160 persone che risultavano vive e non lo erano. I viventi scendono da
913 a 798, e i dispersi da 53 a 4. Sulla scheda di ognuno c'è scritto da quale
registro arriva la data.

**Chi comanda sul decesso.** Il registro ufficiale, non Wikidata: e'
l'istituzione che certifica i propri ex, mentre Wikidata la scrive chi passa.
La data di Wikidata si tiene solo quando e' piu' precisa e non contraddice il
registro. Cosi' sono state affinate 134 date di morte e corrette 42 di nascita.

**Le cariche.** Il cursus scritto a mano e' una sintesi, e le sintesi perdono
pezzi: a Sergio Mattarella mancavano la vicepresidenza del Consiglio, la Difesa
e la Consulta. Sulla scheda dei 66 c'e' ora l'elenco completo e datato ricavato
da Wikidata, accanto al cursus curato che resta come lo aveva scritto l'autore.

**La verifica.** `scripts/verifica_viventi.py` passa in rassegna chi risulta
vivo e chiede conto ai registri, perche' il silenzio di una fonte non e' una
prova di vita. Degli 798 viventi, 781 sono confermati da Camera o Senato, 14 non
sono mai stati eletti (i tecnici di Ciampi e Dini, che nessun registro
parlamentare puo' contenere) e **3 restano non agganciati**: la loro vita non e'
verificata da nessuna seconda fonte.

**Estetica.** Televideo RAI. Le pagine numerate non sono decorazione: sono il
sistema di navigazione, e sono la risposta al problema di far scorrere 897 nomi.

**Distribuzione.** Prima un sito statico generato in locale, senza installazioni
né account. Poi, se piace, lo stesso repo su hosting gratuito con un job notturno.

## Com'è messa la truppa

| | |
|---|---|
| Censiti in tutto | 4.606 |
| Viventi | 798 |
| Deceduti | 3.804 |
| Sorte ignota | 4 |

La Costituente e la I legislatura sono estinte al completo: l'ultimo costituente
è stato Emilio Colombo, morto il 24 giugno 2013.

Il partito è noto per 714 viventi su 913: per gli altri Wikidata non lo registra,
e la colonna resta vuota invece di inventarselo.

## Script

- `scripts/wd.py` — utility per Wikidata (API di ricerca + SPARQL)
- `scripts/camera.py`, `scripts/senato.py` — i registri ufficiali di Camera e Senato
- `scripts/verifica_viventi.py` — chiede conto ai registri di chi risulta vivo
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
