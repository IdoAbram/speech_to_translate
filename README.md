# SongWords — offline speech and translation

Drop an MP3, read its words, then translate between **English, Hebrew, and
Polish**. Speech language is detected automatically. All processing stays on
the computer; the desktop app never downloads models or needs an account.

## Run on a computer without Python

Use **`dist/SongWords.exe`**. It includes Python, native libraries, the speech
model, and the translation model. Copy that one file to another Windows x64
computer and double-click it. No separate Python or FFmpeg installation is
needed. Windows 10/11 x64 is the intended platform; ARM is not tested.

A self-contained model application is large: the two models alone occupy
about **980 MB** before executable compression. The single-file executable
unpacks its runtime and models into a temporary folder at each launch, so it
needs extra startup time and free disk space. Allow at least 3 GB free.

For faster startup, use **`dist/SongWordsPortable/SongWordsPortable.exe`**.
Copy the **entire `SongWordsPortable` folder**, including `_internal` and
`models`, to the other computer. It also works without Python and avoids
unpacking models at each launch. The portable folder also exposes the shared
libraries for replacement and inspection.

## Use the app

1. Drop one MP3 or click the large file area.
2. Wait while the app identifies the language and transcribes the audio.
3. Review or edit the transcript.
4. Choose the translation language and click **Translate**.

Both texts appear side by side, with Copy and Save actions and native Hebrew
right-to-left layout. The app starts fullscreen. **F11** or the visible
**Window / Fullscreen** button toggles fullscreen; **Esc** returns to a maximized
window. **Exit** closes the app.

Language settings contains an optional override for incorrect detections.
Selecting an override transcribes the current recording again. Changing the
transcript or translation language clears the previous translation.
Finished translations are remembered while the app is open: translating the
same transcript into a language used earlier shows the result instantly.
Editing the transcript translates it again.

The loading display reports elapsed time and **confirmed audio coverage**.
Model loading and language detection have an indeterminate indicator. During
recognition, progress follows audio timestamps and never moves backward.
Whisper delivers passages in batches, so the percentage may stay still while
the elapsed timer continues. It is not a prediction of time remaining.
Completion is reported only after inference and model cleanup finish.

Cancel takes effect between model steps. A running native decoder call cannot
be interrupted immediately. Cancelling translation keeps the transcript.

## Models and translation quality

- Speech: multilingual **Whisper small**, using faster-whisper / CTranslate2
  with INT8 CPU computation. Stored speech weights are about 486 MB.
- Translation: **M2M100 418M**, converted from the official Meta weights to
  CTranslate2 INT8, about 494 MB including vocabulary and tokenizer.
- All six translation directions use the same multilingual model directly.
  Hebrew ↔ Polish no longer goes through English.
- Each transcript line is translated on its own, so line N of the
  translation always belongs to line N of the transcript. This keeps
  subtitles aligned. Very long lines are split at sentence or word boundaries
  into at most 256 content tokens per passage.
- There is **no whole-document text-length limit**. A decoder that reaches its
  output budget is retried on smaller pieces. Input is never silently cut to
  fit the model. Repeated passages are reused within a request; every occurrence
  remains in the result.

If a translated passage omits a numeric identifier of three or more digits,
the app retries smaller pieces. This addresses an omission found by the long
document test; it is not a general test of translation completeness.

The transcript uses word timing for editable line and stanza spacing. Gaps of
0.8 seconds suggest line breaks; gaps of 2.5 seconds suggest stanza breaks.
Translated text keeps the exact line and blank-line layout of the transcript,
so edit line breaks in the transcript to match the song before translating.
A phrase split across two lines is translated as two pieces, which can read
less naturally. It is a meaning translation, not a rhyming adaptation.

Detection can use vocal regions to skip an instrumental introduction. The
actual transcription retains the full recording without speech-only VAD
trimming. One main language per recording is assumed.

These compact offline models still make mistakes. Real checks found a Hebrew
pronoun translated as “he” where “it” was intended, and awkward Polish grammar.
Songs, idioms, overlapping vocals, and music can cause recognition errors that
then propagate into translation. The included checks verify processing and some
key meanings; they do not establish a general accuracy score for songs.

Only one inference model is resident at a time, with up to four CPU threads.
An 8 GB RAM computer is the initial target, not a measured minimum. Performance
depends on the CPU, recording duration, and document length.

## Better translation with Groq (free, online)

The offline model translates word by word and misses slang. With a free Groq
key, the app sends the whole song to a large online model instead, which
understands context, slang, and idioms. Each source line still gets exactly
one translated line, and blank stanza lines are kept.

1. Sign up at [console.groq.com](https://console.groq.com) (no card needed)
   and create an API key under **API Keys**.
2. Create a file named **`groq_key.txt`** next to `app.py`, or next to
   `SongWords.exe`, and paste the key into it. Git ignores this file.
3. Restart the app. Translation now uses Groq; delete the file to go back to
   the offline model.

The default model is `openai/gpt-oss-120b`. Set the `GROQ_MODEL` environment
variable to try another Groq model. Lyrics are sent to Groq, so this needs
internet, and the free plan has request limits. Without a key nothing is sent
anywhere.

## Run and develop from source

Use Python 3.13 x64. From this project folder:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe setup_models.py
.\.venv\Scripts\python.exe app.py
```

Use the full Python executable path if the `py` launcher cannot find it.
For an already prepared checkout, double-click `run.bat`.

Setup requires internet and downloads official model assets. It pins each
repository revision across retries and records provenance in
`models/manifest.json`. Translation conversion uses a separate project-local
**`.model-venv`**, with PyTorch and Transformers from `requirements-models.txt`.
Those large conversion dependencies are not part of the desktop runtime.
Setup may need several GB of temporary space in `.downloads/`.

After setup, the app runs offline. Legacy Argos model folders from an earlier
version are left on disk but are no longer used or shipped by the build.
Missing models produce an actionable error instead of a network request.

The stages also have independent CLI commands:

```powershell
.\.venv\Scripts\python.exe -m speech_translate transcribe song.mp3 --output transcript.txt
.\.venv\Scripts\python.exe -m speech_translate translate transcript.txt --source he --target pl --output translated.txt
```

Language codes are `en`, `he`, and `pl`. Optional `transcribe --language he`
overrides automatic detection. Output filenames must not already exist.
The CLI supports other audio formats through PyAV; the desktop accepts MP3.
`setup_models.py --speech-model base` or `medium` installs alternative speech
models, selectable with CLI `transcribe --model`. The desktop uses `small`.

## Build the executable

Build on Windows with the models already installed:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe build_windows.py
.\.venv\Scripts\python.exe build_windows.py --portable
```

`build.bat` performs the first two commands. Pass `--portable` to it for the
portable folder. Builds include only the selected small speech model and the
new multilingual translation model.

The executable has an unattended verification command that writes a JSON report:

```powershell
.\dist\SongWords.exe --self-test report.json --audio sample.mp3
```

This constructs the fullscreen UI, loads local weights, tests all six language
directions, and optionally transcribes audio with automatic detection. The
report records whether it ran as a frozen executable and which model path it
used. A successful local check is not a substitute for testing on the oldest
target Windows machine.

## Modules and tests

| Folder | Responsibility |
|---|---|
| `speech_translate/speech/` | Audio decoding, detection, progress, recognition, lyric formatting |
| `speech_translate/translation/` | Tokenization, contextual passages, bounded decoding and retries |
| `speech_translate/gui/` | Theme, fullscreen window, text panels, activity display, worker lifecycle |
| `speech_translate/installation/` | Connected setup, downloads, isolated conversion |
| `tests/` | Pytest unit, Qt workflow, and opt-in actual-model tests |

Python uses Google-style naming, imports, docstrings, and 80-column formatting.
A test enforces **at most 20 physical lines per function**, including tests and
build helpers. Qt event methods retain Qt's required names.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest --cov=speech_translate
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
$env:RUN_MODEL_TESTS = '1'
.\.venv\Scripts\python.exe -m pytest --durations=10
```

Tests block Python socket connections. They cover detection, backward timestamp
corrections, a 40,000-plus-character input, decoder overflow recovery, repeated
stanzas, cancellation, Unicode, exports, actual Qt workers, and packaging.
Actual-model tests include all six translation routes, connected Hebrew/Polish
sentences, and **100 distinct paragraphs totaling over 5,000 English words**.
They check that every numbered paragraph survives in the Hebrew result.

Integration tests encode `tests/fixtures/sample.wav` as MP3, check automatic
English detection, and exercise the complete desktop pipeline. The fixture is
generated speech, not a real song. Recognition accuracy for sung Hebrew and
Polish has not been measured.

## Windows builds on GitHub

The **Windows standalone EXE** workflow runs on Windows Server 2022 x64 for
pull requests to `main`/`dev`, pushes to `main`/`dev`/`speed_to_translate`, and
manual runs from the Actions tab. Its stages run in this order:

1. **Prebuild:** create a Python 3.13 virtual environment, check dependencies,
   Google-style Python conventions, formatting, and workflow syntax.
2. **Build:** install/cache the Whisper small and INT8 M2M100 runtime models,
   embed them with Python in `SongWords.exe`, and record its SHA-256 checksum,
   commit, model revisions, and licenses.
3. **Test:** check the candidate checksum, run pytest with at least 95% coverage,
   including real models and a 5,000-plus-word translation, then run the EXE
   from a separate Unicode directory with no Python on `PATH`. This checks
   actual MP3 recognition and all six translation directions.
4. **Deploy artifact:** verify and upload the exact tested EXE without rebuilding.

Open a successful workflow run and download **SongWords.exe** from its summary
or Artifacts section. This is a direct EXE download, with both models embedded;
the other computer needs neither Python nor a model download. Expect about
1 GB and some extraction time at launch. `SongWords-release-info-*` contains
checksums, build provenance, and notices; `windows-test-reports-*` contains
pytest, coverage, and executable-check reports. Final artifacts last 14 days;
intermediate build/model artifacts last one day. GitHub requires sign-in to
download workflow artifacts. This workflow does not create a GitHub Release.

GitHub's build runner needs internet access to install dependencies and fetch
models on a cache miss. The finished app performs inference offline. A first
build is slower because it also converts the translation weights; subsequent
builds reuse completed model files. Models and generated EXEs stay out of Git.

## Upstream references

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [Whisper small weights](https://huggingface.co/Systran/faster-whisper-small)
- [Meta M2M100 model card and supported languages](https://huggingface.co/facebook/m2m100_418M)
- [CTranslate2 M2M100 inference format](https://opennmt.net/CTranslate2/guides/transformers.html#m2m-100)
- [Qt for Python](https://doc.qt.io/qtforpython-6/)
- [PyInstaller](https://pyinstaller.org/)

Application code uses the repository's Apache-2.0 license. Libraries and models
retain their own licenses and notices; see `THIRD_PARTY_NOTICES.md`.
