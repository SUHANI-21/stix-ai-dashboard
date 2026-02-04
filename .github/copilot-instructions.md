# Copilot / AI Agent Instructions for stix-ai-dashboard

Purpose: give coding agents the minimal, actionable context to be immediately productive in this repository.

- **Big picture:** This is a Streamlit-based STIX analysis dashboard. The UI entry is `dashboard.py` and the STIX-specific analyzer page lives at `pages/stix_analyzer.py`. Core analysis logic is implemented in the `modules/` package (detection, validation, formatting, utils).

- **Primary run command:**

  pipenv / venv: install dependencies then run the app like:

  ```bash
  pip install -r requirements_analyzer.txt
  streamlit run dashboard.py
  ```

- **Major components & data flow:**
  - `pages/stix_analyzer.py` — Streamlit page that wires the UI to analysis functions.
  - `modules/enhanced_detector.py` — high-level detection wrapper; prefer calling `EnhancedVersionChecker.detect_stix_full(filepath)` for full metadata (version, format, object count).
  - `modules/enhanced_validator.py` — validation wrapper; key entry points: `validate_stix_detailed()` and `extract_statistics()` returning dicts consumed by the UI.
  - `modules/formatter.py` — transforms validator/detector dicts into UI-friendly structures (e.g., `ResultFormatter.format_detection_card`).
  - `modules/utils.py` — session-based temp file management (FileManager), JSON helpers, and error formatting. Agents should use these helpers for file IO and cleanup.

- **Conventions and patterns to follow (project-specific):**
  - Modules expose class-based helpers whose methods return plain dicts (not custom objects). Mutations are local to temp files — prefer pure functions that return dicts for UI consumption.
  - Naming: higher-level wrappers are `Enhanced*` (e.g., `EnhancedVersionChecker`, `EnhancedValidator`). Use those, not lower-level legacy functions.
  - UI wiring: Streamlit pages expect functions that return serializable dicts and simple lists; avoid returning complex iterators or file handles.
  - Session storage: uploaded files go to a per-session temp dir managed by `FileManager` in `modules/utils.py`. Do not introduce persistent storage without explicit changes to the UI and README.

- **Files to reference when editing or adding features:**
  - `dashboard.py` — app entry; useful for global imports and Streamlit config.
  - `pages/stix_analyzer.py` — example of how analysis functions are called and results displayed.
  - `modules/enhanced_detector.py`, `modules/enhanced_validator.py`, `modules/formatter.py`, `modules/utils.py` — core logic and helpers.
  - `requirements_analyzer.txt` — dependencies; update when adding new packages.
  - `ANALYZER_README.md` and `SETUP_GUIDE.md` — higher-level documentation and run notes; mirror any run-command changes here.

- **Debugging & quick checks:**
  - Reproduce UI locally with `streamlit run dashboard.py` and watch stdout/stderr — most runtime errors surface in the terminal.
  - If you need to inspect intermediate data, add temporary prints or `logging` in `modules/*` and re-run Streamlit (it reloads on save).
  - To inspect file handling behavior, check `modules/utils.py` (FileManager) for temp path patterns used by the UI.

- **What to avoid / constraints:**
  - Do not introduce persistent storage without updating README and UI session behavior; the app intentionally uses ephemeral session temp dirs.
  - Avoid large blocking long-running jobs in the request/UI thread—Streamlit auto-reloads and may block the page. If needed, extract to a background worker and show progress in the UI.

- **Examples of changes & how to implement them:**
  - Adding a new analysis statistic: implement extractor in `modules/enhanced_validator.py` returning the new metric in the existing dict shape, then update `modules/formatter.py` to render it; finally update `pages/stix_analyzer.py` to display the new field.
  - Adding a new Streamlit page: create `pages/<your_page>.py` following `stix_analyzer.py` patterns (imports, session usage, and callables returning dicts).

- **Testing expectations:**
  - There are no unit tests in the repo. When adding logic, include small self-contained functions so the maintainer can later add tests. Prefer deterministic outputs (serializable dicts) to simplify future test creation.

If anything here is unclear or you want more examples (for example, a small PR that adds a new statistic end-to-end), tell me which part to expand and I will iterate.
