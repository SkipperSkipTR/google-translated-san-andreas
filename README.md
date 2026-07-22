# GTA: San Andreas - Google Translated Mod (v2) ⟳

Created by **SkipperSkip** ([ModDB Profile](https://www.moddb.com/mods/google-translated-san-andreas))

**Google Translated San Andreas v2** is the second generation of the total script overhaul mod for *Grand Theft Auto: San Andreas*. The entire in-game text (16,500+ dialogue entries, mission objectives, and UI strings) is passed through multi-layer machine translation chains across random foreign languages and back into English, yielding chaotic, hilarious, and unpredictable dialogue.

Version 2 introduces a completely new custom toolkit: a dedicated desktop editor (`hypertranslator.py`), multi-hop candidate generation (3, 5, 20, 50, and 100 hops), cloud-assisted worker pipelines (`translation_worker.py`), and strict encoding verification.

---

## 🎮 Mod Specifications (v2)

| Specification | Details |
| :--- | :--- |
| **Game Target** | *Grand Theft Auto: San Andreas* (v1.0 & Modloader compatible) |
| **Mod Author** | SkipperSkip |
| **Script Scope** | 16,588 entries (`american.txt` / `american.gxt`) |
| **Translation Engine** | Google Translate multi-pass back-translation |
| **Hop Multipliers** | 3, 5, 20, 50, and 100 random language hops |
| **Text Encoding** | Standard **Windows-1252 (ANSI)** (enforced via GUI) |
| **GXT Tag Handling** | Full preservation of game formatting & color tags (`~w~`, `~r~`, `~VEHICLE_TURRETLEFT~`) |
| **Cloud Pipeline** | Supabase database task queue & distributed worker sync |

---

## 🌟 Key Features in v2

### 1. **HyperTranslator GUI Editor (`hypertranslator.py`)**
- **Side-by-Side Review**: Compare original GTA text against multiple machine-translated candidates simultaneously.
- **Candidate Hop Switcher**: Instantly switch between 3, 5, 20, 50, or 100-hop back-translated candidates.
- **Smart GXT Tag Bar**: One-click quick-insert buttons for special GTA color and vehicle tags (e.g. `~w~`, `~b~`, `~VEHICLE_TURRETLEFT~`) to prevent broken text rendering in-game.
- **Windows-1252 Safeguard**: Automatically inspects edited text and blocks non-1252 characters (e.g., unicode symbols or foreign alphabets) that cause in-game crashes or garbled fonts.
- **Dynamic File & Session Persistence**: Auto-detects local source files (`american.txt`) and saves progress to `.hypertrans_session` files for seamless resume.

### 2. **Distributed Cloud Translation Worker (`translation_worker.py`)**
- **Supabase Cloud Backend**: Synchronizes translation tasks across multiple worker instances.
- **Multi-Hop Random Chains**: Routes text sequentially through random Google Translate language pairs before returning to English.
- **Paginated Export**: High-volume chunked database export tool to generate candidate bundles (`candidates/batch_*.json`).

---

## 📂 Repository Contents

```
SA v2/
├── american.txt                   # Base game source localization text (16,588 keys)
├── hypertranslator.py             # Desktop GUI editor & translation manager
├── translation_worker.py          # Supabase cloud worker & candidate export script
├── candidates/                    # Pre-generated candidate translation pools
│   ├── batch_1.json               # Batch 1 candidate dataset
│   ├── batch_3.json               # Batch 3 candidate dataset
│   ├── batch_5.json               # Batch 5 candidate dataset
│   ├── batch_7.json               # Batch 7 candidate dataset
│   └── batch_10.json              # Batch 10 candidate dataset
├── .env.example                   # Template for environment configuration
├── .gitignore                     # Git ignore rules for secrets and sessions
└── README.md                      # Project documentation & mod specs
```

---

## 🛠️ Usage Guide

### 1. Requirements & Setup
Install Python 3.9+ and required dependencies:

```bash
git clone https://github.com/SkipperSkipTR/google-translated-san-andreas.git
cd google-translated-san-andreas
pip install supabase deep-translator tqdm
```

### 2. Running the HyperTranslator GUI
Launch the editor to review, edit, and commit translations for `american.txt`:

```bash
python hypertranslator.py
```
- Select an entry from the tree.
- Choose your preferred candidate card (3, 5, 20, 50, or 100 hops).
- Click GXT tag buttons to restore required tags.
- Press **F2** to Commit or **F3** to Skip.
- Click **Save** to export your final `american_translated.txt`.

### 3. Running Translation Workers (Optional)
To contribute new translation candidates to the Supabase database:

1. Copy `.env.example` to `.env` and fill in your Supabase credentials:
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

## 🎮 Installing the Mod into GTA: San Andreas

Once `american_translated.txt` is exported:
1. Convert `american_translated.txt` to `american.gxt` using a standard GXT compiler (e.g. GXT Editor or GTA GXT Builder).
2. **ModLoader (Recommended)**: Place `american.gxt` into `modloader/Google Translated/text/american.gxt`.
3. **Manual Install**: Replace `text/american.gxt` inside your main GTA San Andreas directory.

---

## 📜 Credits

- **Mod Author & Developer**: SkipperSkip ([ModDB Page](https://www.moddb.com/mods/google-translated-san-andreas))
- **Original Game**: Rockstar Games (*Grand Theft Auto: San Andreas*)
- **Translation Services**: Google Translate via `deep-translator`

---

## 📄 License
MIT License
