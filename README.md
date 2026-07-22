# San Andreas HyperTranslator ⟳

An advanced translation toolkit and GUI for GTA: San Andreas localization files (`american.txt` / `ENGLISH.txt`), featuring multi-hop back-translation candidates, GXT tag handling, character encoding safeguards, and cloud worker distribution.

## Features

- **HyperTranslator GUI (`hypertranslator.py`)**:
  - Interactive side-by-side translation review and editing.
  - Multi-hop candidate selection (3, 5, 20, 50, 100 hops back-translated).
  - Smart GXT tag quick-insert bar (supports GTA color and vehicle tags like `~w~`, `~r~`, `~VEHICLE_TURRETLEFT~`).
  - Strict **Windows-1252** encoding validation to prevent invalid characters from causing ingame crashes.
  - Automatic session restoration and export.

- **Distributed Worker (`translation_worker.py`)**:
  - Cloud task distribution powered by **Supabase**.
  - Multi-threaded back-translation using Google Translate across random language chains.
  - Efficient chunked task claiming, progress tracking, and full candidate export.

## Setup & Installation

1. **Clone repository**:
   ```bash
   git clone https://github.com/SkipperSkipTR/san-andreas-hypertranslator.git
   cd san-andreas-hypertranslator
   ```

2. **Install dependencies**:
   ```bash
   pip install supabase deep-translator tqdm
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your Supabase credentials:
   ```bash
   cp .env.example .env
   ```

## Usage

### Running the GUI
```bash
python hypertranslator.py
```

### Running the Distributed Worker
```bash
# Start translation worker loop
python translation_worker.py worker

# Export candidates from Supabase database
python translation_worker.py export --out candidates/
```

## License
MIT
