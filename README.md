---
title: MurderMind Multi-Agent Mystery Studio
emoji: 🕵️‍♀️
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 6.32.0
app_file: app.py
short_description: Studio Multi-Agente per Cene con Delitto giocabili
python_version: "3.12"
startup_duration_timeout: 30m
---

# 🕵️‍♀️ MurderMind — Studio Multi-Agente per Cene con Delitto

**MurderMind** è una piattaforma open source che progetta, valida ed esporta **Cene con Delitto (*Murder Mystery Dinner Games*) complete, coerenti e pronte da giocare**.

Invece di generare un semplice racconto con un unico prompt, MurderMind coordina **10 agenti AI specializzati** su un **Grafo d'Informazione condiviso (*Single Source of Truth*)**: definisce prima la soluzione canonica del crimine, costruisce alibi e segreti incrociati, verifica che gli indizi permettano davvero di dedurre l'assassino e separa rigorosamente il materiale dei giocatori da quello del Master.

---

## 🤖 Come lavorano i 10 Agenti

1. **Game Director** (`Fase 1`): crea titolo, premessa narrativa (*hook*), vittima e atmosfera.
2. **World Builder** (`Fase 2`): costruisce l'ambientazione, i luoghi della scena del crimine e gli antefatti.
3. **Plot Architect** (`Fase 3`): stabilisce **colpevole canonico**, arma, movente, orario, **falla nell'alibi** e cronologia (`timeline`).
4. **Character Designer** (`Fase 4`): genera i personaggi giocanti (PG) e non giocanti (PNG) con obiettivi, relazioni, alibi e segreti.
5. **Subplot Designer** (`Fase 5`): intreccia sottotrame secondarie (ricatti, debiti, amori segreti, rivalità) tra gli invitati.
6. **Clue Master** (`Fase 6`): progetta le prove fisiche/documentali che smascherano il colpevole più i depistaggi (*red herrings*).
7. **Game Mechanics Designer** (`Fase 7`): divide la serata in 3 fasi di gioco con tempi, regole di interrogatorio e punteggi di vittoria.
8. **Narrative Writer** (`Fase 8`): scrive il monologo di apertura, le battute suggerite, i messaggi riservati di metà serata e i documenti in-game.
9. **Continuity Editor** (`Fase 9`): revisore critico che controlla la coerenza del grafo e richiede correzioni mirate agli altri agenti.
10. **Final Game Producer** (`Fase 10`): impacchetta Manuale del Master, Regole per i Giocatori, Soluzione Segreta e Dossier stampabile.

---

## 📦 Guida Specifica all'Output Generato (`murder_mystery/`)

Quando clicchi su **Esporta Dossier**, MurderMind genera un pacchetto completo (scaricabile come **`.zip`**, **`.pdf` stampabile**, **`.json`** o **`.md`**) progettato per gestire materialmente la serata a tavola senza rischio di spoiler.

### 1. Cosa consegnare ai Giocatori (Zero Spoiler sul Colpevole)

| File / Cartella nel Dossier | Cosa contiene esattamente | Come si usa durante la cena |
| :--- | :--- | :--- |
| `gameplay/player_instructions.md` | Introduzione pubblica all'ambientazione, elenco dei sospettati presenti, regole del gioco e criteri di punteggio per l'accusa finale. | Da inviare agli invitati prima della serata o da leggere insieme all'aperitivo. |
| `characters/character_01.md` ... `character_NN.md` | **Scheda individuale riservata a un singolo giocatore**: storia personale, carattere, obiettivi della serata, **il proprio alibi**, **il proprio segreto da nascondere**, cosa sa sugli altri, battute consigliate e se è **Innocente** o **Colpevole**. *Non contiene mai i segreti altrui né la soluzione del Master.* | Ogni giocatore riceve **solo la propria scheda** (stampata o via smartphone). |
| `clues/printable_clues/clue_01.md` ... | **Cartellini dei singoli reperti investigativi** (es. analisi del veleno, oggetto smarrito, registro orario), privi delle note interne del Master. | Il Master li mette in 3 buste (`Fase 1`, `Fase 2`, `Fase 3`) e li distribuisce a centro tavola all'inizio di ogni portata. |
| `documents/letters/`, `messages/`, `evidence/` | **Prove sceniche pronte da stampare**: lettere incompiute della vittima, biglietti minacciosi strappati, verbali o estratti di registri. | Da consegnare fisicamente ai giocatori insieme agli indizi a cui sono collegati. |

---

### 2. Cosa resta esclusivamente in mano al Master (Organizzatore)

| File / Cartella nel Dossier | Cosa contiene esattamente | Come lo usa il Master |
| :--- | :--- | :--- |
| `gameplay/master_manual.md` | **Manuale di Regia passo-passo**: checklist di preparazione prima della cena, tempi di ciascuna delle 3 fasi, quali indizi svelare in ogni fase, eventi programmati e consigli per sbloccare le indagini. | È il copione operativo che il Master tiene sott'occhio per tutta la serata. |
| `plot/secret_solution.md` & `final/resolution.md` | **La Soluzione Segreta Canonica**: identità dell'assassino (`culprit_id`), arma, luogo, fascia oraria, movente, **la contraddizione esatta che smonta il suo alibi**, la catena deduttiva che lega gli indizi e il **Discorso Teatrale di Rivelazione Finale**. | Da tenere segreto fino a fine serata; il discorso finale va letto ad alta voce dopo aver ritirato le schede di accusa dei giocatori. |
| `plot/timeline.json` & `plot/main_plot.md` | **Cronologia canonica oraria** (`20:00`, `20:45`, `21:15`...) con posizione reale di ogni personaggio e lista dei depistaggi. | Permette al Master di verificare all'istante chi mente o dice la verità durante gli interrogatori. |
| `subplots/subplot_01.md` ... | Dettaglio delle sottotrame secondarie tra gli innocenti (chi ricatta chi, come si innesca il conflitto e come si risolve). | Aiuta il Master a stimolare il roleplay tra i giocatori durante la Fase 2. |
| `clues/clues.json` | Database strutturato degli indizi con i campi riservati `points_to_character_id`, `contradicts_alibi_of_id`, `is_red_herring` (vero/falso) e `logical_inference`. | Mostra al Master cosa dimostra logicamente ogni singola prova e quali sono le false piste. |
| `final/master_report.md` | **Matrice riassuntiva rapida** con tutti i personaggi (Colpevole vs Innocente, Movente, Alibi, Segreto) e il punteggio di coerenza assegnato dal `ContinuityEditor`. | Colpo d'occhio rapido per avere tutti i segreti su un'unica pagina. |
| `final/printable_dossier.pdf` | **Unico PDF impaginato pronto per la stampa**, diviso in: 1) Regole Giocatori, 2) Schede Personaggio (una per pagina, così da distribuirle facilmente), 3) Cartellini Indizi, 4) Manuale e Soluzione del Master in fondo. | Stampa immediata dell'intero kit di gioco con un solo click. |
| `project.json` | L'intero **Grafo d'Informazione canonico** in formato JSON (configurazione, mondo, trama, personaggi, sottotrame, indizi, log degli agenti). | Per backup, modifica programmatica o re-importazione del progetto. |

> 💡 Nel repository trovi due dossier completi già generati e navigabili:
> - [`examples/demo_villa_morosini/murder_mystery/`](./examples/demo_villa_morosini/murder_mystery/) (*"L'Ultimo Brindisi a Villa Morosini"*)
> - [`examples/qwen_generated_mystery/murder_mystery/`](./examples/qwen_generated_mystery/murder_mystery/) (*"Delitto al Grand Hotel Excelsior"*, generato dal vivo con `unsloth/Qwen3.5-2B`).

---

## 🚀 Avvio Rapido (Locale & Hugging Face Spaces)

### In Locale (con `unsloth/Qwen3.5-2B` su `:8888`)
```bash
cp .env.example .env          # Inserisci la tua LLM_API_KEY in .env
pip install -e ".[dev]"       # Installa dipendenze
pytest -v                     # Esegui i test automatici
python app.py                 # Avvia la Web App su http://localhost:7860
```

### Su Hugging Face Spaces & CI/CD Automatico
- **ZeroGPU (`zero-a10g`)**: Lo Space pubblico gira gratuitamente su **ZeroGPU** caricando `Qwen/Qwen2.5-3B-Instruct` direttamente su GPU, senza costi API.
- **Auto-Deploy DevOps (`.github/workflows/ci-cd-huggingface.yml`)**: Ad ogni `git push` su `main`, GitHub Actions esegue la suite `pytest` e, se tutti i test passano, pubblica automaticamente la nuova versione sullo Space [`nonsonpratico/murdermind`](https://huggingface.co/spaces/nonsonpratico/murdermind).

---

## 📄 Licenza

Rilasciato sotto licenza [MIT](./LICENSE). Vedi anche [CONTRIBUTING.md](./CONTRIBUTING.md) e [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).
