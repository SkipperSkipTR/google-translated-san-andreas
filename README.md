# GTA: San Andreas - Google Translated Mod (v2) ⟳

Development repository for **Google Translated San Andreas v2** — the second generation total script overhaul for *Grand Theft Auto: San Andreas*. 

All 16,588 lines of dialogue, mission texts, and UI strings are processed through multi-pass machine translation chains across random foreign languages and back into English, producing chaotic and hilarious dialogue.

This repository contains the v2 translation pipeline, candidates database, and custom desktop editor (`hypertranslator.py`).

---

## 🛠️ Project Specifications (v2)

| Component | Details |
| :--- | :--- |
| **Game Target** | *Grand Theft Auto: San Andreas* (`american.txt` / `american.gxt`) |
| **Script Scope** | 16,588 entries |
| **Translation Engine** | Google Translate multi-pass back-translation |
| **Hop Multipliers** | 3, 5, 20, 50, and 100 random language hops |
| **Text Encoding** | Standard **Windows-1252 (ANSI)** (enforced in editor) |
| **GXT Tag Handling** | Color and vehicle tag preservation (`~w~`, `~r~`, `~VEHICLE_TURRETLEFT~`) |
| **Cloud Pipeline** | Supabase database task queue & multi-worker sync |

---

## 🌟 Features in v2

### 1. **HyperTranslator GUI Editor (`hypertranslator.py`)**
- **Side-by-Side Review**: Compare original GTA text against machine-translated candidates simultaneously.
- **Candidate Hop Switcher**: Switch between 3, 5, 20, 50, or 100-hop back-translated candidates.
- **Smart GXT Tag Bar**: Quick-insert buttons for GTA color and vehicle tags (e.g. `~w~`, `~b~`, `~VEHICLE_TURRETLEFT~`) to maintain game rendering.
- **Windows-1252 Safeguard**: Blocks non-1252 characters (foreign alphabets or unsupported symbols) that cause in-game crashes.
- **Session Persistence**: Auto-detects local source files (`american.txt`) and syncs session state via `american.hypertrans_session`.

### 2. **Distributed Translation Worker (`translation_worker.py`)**
- **Supabase Cloud Backend**: Distributes translation jobs across parallel workers.
- **Multi-Hop Chains**: Sequentially translates text through random language pairs before returning to English.
- **Paginated Exporter**: High-volume database export tool for generating candidate bundles (`candidates/batch_*.json`).

---

## 📂 Repository Structure

```
SA v2/
├── american.txt                   # Base game source localization text (16,588 keys)
├── american.hypertrans_session    # Active translation session & selection state
├── hypertranslator.py             # Desktop GUI translation editor
├── translation_worker.py          # Supabase cloud worker & candidate export script
├── candidates/                    # Pre-generated candidate translation pools
│   ├── batch_1.json               # Batch 1 candidate dataset
│   ├── batch_3.json               # Batch 3 candidate dataset
│   ├── batch_5.json               # Batch 5 candidate dataset
│   ├── batch_7.json               # Batch 7 candidate dataset
│   └── batch_10.json              # Batch 10 candidate dataset
├── .env.example                   # Template for environment variables
├── .gitignore                     # Git ignore rules
└── README.md                      # Repository documentation
```

---

## 🚀 Setup & Development

### 1. Installation
Install Python 3.9+ and required dependencies:

```bash
git clone https://github.com/SkipperSkipTR/google-translated-san-andreas.git
cd google-translated-san-andreas
pip install supabase deep-translator tqdm
```

### 2. Running the HyperTranslator GUI Editor
Launch the editor to review, edit, and commit translations for `american.txt`:

```bash
python hypertranslator.py
```
- Select an entry from the tree view.
- Pick your preferred candidate card (3, 5, 20, 50, or 100 hops).
- Click GXT tag buttons to restore missing tags.
- Press **F2** to Commit or **F3** to Skip.
- Progress auto-saves to `american.hypertrans_session`.

### 3. Running Translation Workers (Optional)
To run worker nodes or export database candidate sets:

1. Copy `.env.example` to `.env` and configure Supabase credentials:
   ```bash
   cp .env.example .env
   ```
2. Start the worker loop:
   ```bash
   python translation_worker.py worker
   ```
3. Export candidate JSON datasets:
   ```bash
   python translation_worker.py export --out candidates/
   ```

---

## 📄 License
MIT License
