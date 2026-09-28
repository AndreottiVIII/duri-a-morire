# Fonti dei dati

## Trascrizioni del Voynich (in `trascrizioni/`)

Sono le trascrizioni pubblicate da René Zandbergen su
[voynich.nu](https://www.voynich.nu/transcr.html), nel formato IVTFF. Il sito
da questo ambiente non si raggiunge: le copie vengono dal repository pubblico
[Krymorn/The-Voynich-Transliteration-Tool](https://github.com/Krymorn/The-Voynich-Transliteration-Tool)
(commit `cb2d36894a901b9570dd05e96f309fedf9947c4e`), che le distribuisce con
le impronte SHA-256 degli originali. Le nostre copie coincidono con quelle
impronte. Gli autori le rendono liberamente disponibili per la ricerca.

| file | trascrizione | alfabeto | versione | SHA-256 |
|---|---|---|---|---|
| `ZL3b-n.txt` | Zandbergen-Landini, la più completa | EVA | 3b del 13/05/2025 | `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc` |
| `IT2a-n.txt` | Takahashi, dall'archivio interlineare di Stolfi | EVA di base | 2a, rivista 25/06/2025 | `7f27a8b0feed8f6de0a99900df6bf912dd1d295c38e5f830bac8b41c3f536fb5` |
| `GC2a-n.txt` | Glen Claston | v101 | 2a, rivista 25/06/2025 | `b09570cb6c993bc2d87134d115e60a978650a8a6495483ddbb1f6005a586096f` |

## Testi di confronto (non nel repository, si rigenerano con `prepara.py`)

- **La Bibbia in 100 lingue**: [christos-c/bible-corpus](https://github.com/christos-c/bible-corpus),
  commit `44e5fca1bfb369a5da2ee23ebc6f421c88489c5c`, pubblico dominio (CC0).
  Da qui viene anche il cinese trascritto in pinyin (con la libreria `pypinyin`).
- **Testi tecnici latini** (ricette, agricoltura, piante, trattati):
  [cltk/lat_text_latin_library](https://github.com/cltk/lat_text_latin_library),
  commit `76229acaf02efd1964ac32009408a90b6f279758`, i testi della Latin Library.
