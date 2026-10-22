# Validation — 23 October 2026

The updated app was checked in the local Windows x64 environment with Python
3.13.17. These are local development checks, not a clean Windows VM or a
benchmark of the user's other computers.

## Automated tests

- **111 passed**: unit, Qt workflow, and actual-model integration tests, excluding
  the separately run long-document suite.
- **3 passed**: connected Hebrew/Polish sentences and a real **5,900-word**
  English-to-Hebrew document with **100 distinct numbered paragraphs**.
- **114 passing tests across those runs**, with **96.89%** combined statement
  and branch coverage of `speech_translate` in the main run.
- Ruff lint and formatting checks passed. The convention test verifies that
  every owned function, including build and test helpers, is at most 20 physical
  lines long. Dependency checks passed in both virtual environments.

The long document retained every paragraph number, with no text-length error.
That stress test took 523 seconds on this machine while other work was running,
including repeated inference to recover omitted numbers. It verifies processing
and preservation of paragraph identifiers, not perfect translation of every word.

Tests block Python socket connections. Real integration checks cover all six
language directions, actual MP3 decoding, automatic English detection, silence,
invalid audio, cancellation, and the complete desktop worker pipeline.

## Executable checks

Both builds were copied into a separate folder with a Hebrew name. Each ran
from a different working directory with a minimal environment and only Windows
directories on `PATH`. A Hebrew-named MP3 was generated from the existing local
speech fixture. The checks constructed the fullscreen UI, transcribed the MP3,
and translated every language direction.

| Build | Outcome | Assets used |
|---|---|---|
| `dist/SongWords.exe` | Passed | Embedded models extracted into `_MEI.../models`; no neighboring model folder |
| `dist/SongWordsPortable/SongWordsPortable.exe` | Passed | Models in the relocated portable folder, including Unicode path characters |

The single executable is **1,038,592,909 bytes** (about 1.04 GB). Its SHA-256 is
`770254a98e2682dbcb337ee310d7058dfc4852a9f6f13e2c4d91061f67cd278c`.
The complete portable folder is **1,325,267,879 bytes** (about 1.33 GB).
The small portable EXE requires the rest of that folder.

The complete single-file self-test took 71 seconds, including extraction,
startup, six translations, and transcription. The portable self-test took
60.43 seconds. These checks ran under varying system load; they are not isolated
startup benchmarks. The single-file build must unpack its models on each launch.

Run the release checks again with:

```powershell
.\.venv\Scripts\python.exe -m tests.verify_executable dist\SongWords.exe
.\.venv\Scripts\python.exe -m tests.verify_executable dist\SongWordsPortable\SongWordsPortable.exe --portable
```

These checks write reports in `.downloads/standalone-verified.json` and
`.downloads/portable-verified.json`. The executable itself also accepts
`--self-test report.json --audio recording.mp3` without Python installed.

## Translation and UI review

[Actual translation examples](translation-examples.json) contain original test
passages and the six resulting translations. A Hebrew pronoun became “he” where
“it” was intended; some Polish phrasing remains awkward. These compact models
still need review for lyrics, idioms, pronouns, and recognition errors.

[Interface preview](interface.png) shows the native Windows layout with a
synthetic English passage and its actual model translation. The real-model audio
fixture is generated English speech. Sung Hebrew and Polish recognition accuracy
has not been measured.
