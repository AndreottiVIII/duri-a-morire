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

**I gruppi che non sono partiti.** Il gruppo misto raccoglie chi un gruppo non
ce l'ha, l'autonomista metteva insieme sardisti, azionisti e socialisti, e i
gruppi congiunti come `PSDI - Lib.` sono due partiti sotto un tetto. Per chi
sedeva li' il gruppo non dice niente, e comanda il partito di Wikidata: senza
questa eccezione il misto si mangiava 148 persone con un partito noto, fra cui
23 sudtirolesi, 16 liberali e tutti i sardisti.

E vale il contrario del caso Sgarbi: certi partiti non possono essere attribuiti
fuori dalla loro epoca. Il Partito d'Azione si sciolse nel 1947, quindi darlo a
un deputato eletto nel 1987 sarebbe lo stesso errore rovesciato. Le sigle
distintive portano percio' l'elenco delle legislature in cui potevano esistere.

Nota storica emersa dai dati: la Costituente non aveva un gruppo azionista. Il
Partito d'Azione aveva sette deputati, troppo pochi per farsene uno, e si
divisero fra Repubblicano, Autonomista e Misto — ed e' per questo che Parri e
La Malfa risultano PRI, il partito che poi guidarono davvero.

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
e la Consulta. Sulla scheda dei 66 c'e' l'elenco completo e datato ricavato da
Wikidata.

Le due liste pero' dicevano in gran parte le stesse cose con parole diverse, e
la scheda le stampava entrambe. Ora si fondono: del cursus curato resta solo
quello che le cariche non dicono gia', ed e' parecchio, perche' Wikidata
registra le cariche di governo e ignora quasi tutto il resto — segretari di
partito, sindacati, Banca d'Italia, CONI, IRI. Quella e' la ragione per cui il
foglio scritto a mano esiste.

Una voce e' considerata gia' detta in tre modi (`scripts/cursus.py`): per le
parole, quando 'Rapporti con il Parlamento' sta dentro 'Ministro per i rapporti
con il Parlamento'; per gli anni esatti, che riconoscono 'Vice PdC (1983-1987)'
come la vicepresidenza del Consiglio; e per il ministero in forma breve, perche'
'Agricoltura' e 'Ministro delle politiche agricole alimentari e forestali' non
hanno una parola in comune e sono la stessa poltrona. Sui 66: 42 non hanno piu'
niente da aggiungere, 15 hanno una coda vera, 9 hanno solo il curato.

**La verifica.** `scripts/verifica_viventi.py` passa in rassegna chi risulta
vivo e chiede conto ai registri, perche' il silenzio di una fonte non e' una
prova di vita. Dei 796 viventi, **782 sono confermati da Camera o Senato e 14 non
sono mai stati eletti** — i tecnici di Ciampi e Dini, che nessun registro
parlamentare puo' contenere. Non ne resta fuori nessuno. **Nessuna
contraddizione**: non esiste un solo caso in cui noi diamo per vivo qualcuno che
un registro da' per morto. I venti viventi piu' anziani sono confermati tutti,
decano compreso.

**Chi non c'entra.** Comandano i registri: se Camera e Senato collocano qualcuno
fuori dal perimetro I-XI, esce, per quanto Wikidata insista. Sono tre, elencati
con la loro ragione in `data/esclusi.json`. Paolo Romani e Claudio Bonansea
appartengono alla XII legislatura — Wikidata sbaglia le legislature di tre
posizioni, attribuendo a Romani la IX con data d'inizio 1994. Agatone De Luca
Tronchet invece ha il mandato che comincia il **21 gennaio 1849**: e' un deputato
della Costituente della Repubblica Romana, e la sua nascita nel 1900 e' un
segnaposto.

Non basta pero' che un registro non trovi un nome per buttarlo fuori: Ignazio
Silone alla Camera e' registrato col nome vero, Secondino Tranquilli, e Gianna
Schelotto e' Giovanna Bochicchio. I nomi che le fonti scrivono in modo diverso
stanno in `data/alias_registri.json`.

**Il limbo.** I tre di sorte ignota restano dove sono. Nessuna delle tre fonti
ne registra la morte e nessuna puo' registrarla: la voce di Wikipedia di
Enrico Parri scrive *"10 gennaio 1902 -- ..."* e si ferma li'. Presumerli morti a
centoventiquattro anni sarebbe una deduzione nostra spacciata per un fatto. Uno di loro, Mario De Cristofaro, non ha data di nascita da nessuna parte: il suo
mandato comincia e finisce il 17 ottobre 1991, causale "Dimissioni".

**Estetica.** Televideo RAI. Le pagine numerate non sono decorazione: sono il
sistema di navigazione, e sono la risposta al problema di far scorrere 897 nomi.

**Distribuzione.** Prima un sito statico generato in locale, senza installazioni
né account. Poi, se piace, lo stesso repo su hosting gratuito con un job notturno.

## Com'è messa la truppa

| | |
|---|---|
| Censiti in tutto | 4.603 |
| Viventi | 796 |
| Deceduti | 3.804 |
| Sorte ignota | 3 |

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

## Gli indirizzi

Ogni schermata ha il suo indirizzo, quindi la freccia indietro del browser
funziona e le pagine si possono mandare a qualcuno:

    #p240              una pagina
    #Q3432264          la scheda di una persona
    #l/partito:DC      un elenco filtrato
    #cerca/rossi       una ricerca

Le sottopagine sostituiscono l'ultima voce invece di aggiungerne una: sfogliare
duecento sottopagine non deve seppellire il punto da cui si e' arrivati.

## Le pagine

    100  indice                200  statistiche
    101  viventi               210  sopravvissuti per partito
    110  per legislatura       220  curva di estinzione
    111  ...124 una per leg.   230  l'ultimo dei...
    150  ricerca               300  in memoriam
    500  compleanni            400  sorte ignota

    250  piu' legislature di tutti
    260  statistiche dei defunti   261  defunti per partito
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

**Puo' solo aggiungere morti, mai toglierne.** Una data viene scritta solo dove
non ce n'e' gia' una, e nessuno torna dai defunti ai viventi: se una fonte tace
su qualcuno, il silenzio non cancella cio' che un'altra ha gia' certificato. C'e'
anche una rete che non dovrebbe scattare mai, e che annulla l'aggiornamento se
per un difetto il conto dei defunti scendesse.

Funziona solo se il sito e' servito da un indirizzo (il server locale, o l'hosting).
Aperto col doppio clic dal disco il browser blocca le chiamate verso l'esterno, e
la pagina 600 lo dice invece di fallire in silenzio.

## Il partito dei 66

Per la hall of fame comanda la colonna scritta a mano nel file originale, non
Wikidata: e' una scelta editoriale su quale partito definisca quella persona in
quegli anni. Wikidata elenca anche le militanze successive, e senza questa regola
Pizzinato risultava PCI invece che PDS, Raffaele Costa Forza Italia invece che PLI,
Leoluca Orlando DC invece che La Rete, mentre Rete, Verdi e Radicali sparivano.
