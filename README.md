**Test-STT (Speech-to-Text) Runner**

Lightweight toolkit to generate noisy audio samples and evaluate an external STT service against a gold standard. The repository contains sample generators, a test harness that calls an HTTP STT endpoint, and reporting (Excel) of results and statistics.

**Requirements**
- **Python**: 3.12+ recommended (project `pyproject.toml` specifies `requires-python = ">=3.12"`)
- **System**: `ffmpeg` (required by `pydub` for reading/writing audio)
- **Python packages**: `pydub`, `numpy`, `pandas`, `openpyxl`, `python-dotenv`, `requests`

**Quick Install**

If you already have a virtual environment (for example `.venv`), activate it:

```bash
source .venv/bin/activate
```

Install dependencies using the included `pyproject.toml` (recommended):

```bash
uv sync
```

3. Install system dependency (Debian/Ubuntu):

```bash
sudo apt update && sudo apt install ffmpeg -y
```

**Environment / Configuration**
This project reads configuration from environment variables (or a `.env` file) via `settings.py`. 

```
BASE_FOLDER=base_samples          # folder with original sample_X.wav files
TEST_FOLDER=test_samples          # output folder for noisy samples
STT_SERVICE_URL=http://localhost:8000/transcribe  # HTTP endpoint that accepts file upload
GOLD_STANDARD_FILE=gold_standard.json            # mapping sample -> reference text
RUNS=3                            # number of runs per sample (integer)
TEST_RESULT_FILE=test_results.xlsx # output Excel file path
```

- The STT service should accept a multipart file field named `file` and return JSON with a `transcription` key on success. Example response:

```json
{ "transcription": "hello world" }
```

**Usage**
- Generate noisy samples (reads WAVs named like `sample_1.wav` in `base_samples/` and writes to `test_samples/`):

```bash
python generate_samples.py
```

- Run only the test harness (transcribes files in `TEST_FOLDER` and writes `TEST_RESULT_FILE`):

```bash
python test.py
```

- Run the full workflow (generate + test):

```bash
python main.py
```

**What the scripts do**
- `generate_samples.py`: Adds configurable white noise (multiple SNR levels) to each `sample_X.wav`, exporting `sample_X_noise_<dB>.wav` into `TEST_FOLDER`.
- `test.py`: Iterates `.wav` files in `TEST_FOLDER`, calls the STT endpoint for each (multiple `RUNS` times), compares to entries in `GOLD_STANDARD_FILE`, and saves a detailed Excel report.
- `main.py`: Convenience runner that calls `generate_samples.generate()` and then `test.stt_test()`.
- `settings.py`: Loads configuration from environment variables (supports `.env` via `python-dotenv`).

**File Map**
- `generate_samples.py`: sample noise generator (uses `pydub` + `numpy`).
- `test.py`: test harness that calls the STT HTTP service and aggregates results in Excel (`openpyxl` engine used by `pandas`).
- `settings.py`: environment-backed configuration.
- `main.py`: runs generator + tests.
- `base_samples/`: place your original `sample_X.wav` files here.
- `test_samples/`: generated noisy samples (ignored by git via `.gitignore`).
- `gold_standard.json`: JSON mapping of sample numbers to reference transcriptions (e.g., `{ "1": "hello world", "2": "foo bar" }`).

**Output & Reports**
- The test harness writes a detailed Excel file specified by `TEST_RESULT_FILE` (default from `.env`) with per-run transcriptions and an aggregated statistics sheet. It also prints aggregated statistics to console.

**Troubleshooting**
- If `pydub` raises import/codec errors, ensure `ffmpeg` is installed and available in `PATH`.
- If requests to the STT service fail, verify `STT_SERVICE_URL` and that the service accepts a multipart `file` field and returns `transcription` in JSON.
- If you see empty results, confirm `GOLD_STANDARD_FILE` exists and maps sample numbers (integers) to strings.