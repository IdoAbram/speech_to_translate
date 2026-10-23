# Third-party components

The application code is distributed under the Apache License 2.0 in `LICENSE`.
Dependencies and models retain their upstream licenses; this file does not
relicense them. Exact runtime versions are in `requirements.lock.txt`.

Models:

- Whisper small, OpenAI/SYSTRAN: https://github.com/openai/whisper and
  https://huggingface.co/Systran/faster-whisper-small
- M2M100 418M, Meta/Facebook AI: https://huggingface.co/facebook/m2m100_418M
  (model card declares MIT). This app converts its official weights to INT8.
  Source code and license: https://github.com/facebookresearch/fairseq

Runtime projects:

- Python: https://www.python.org/psf/license/
- Qt/PySide6/Shiboken: https://doc.qt.io/qtforpython-6/licenses.html
  and https://code.qt.io/cgit/pyside/pyside-setup.git/
- CTranslate2: https://github.com/OpenNMT/CTranslate2
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- PyAV and its FFmpeg libraries: https://github.com/PyAV-Org/PyAV
- NumPy: https://numpy.org/doc/stable/license.html
- SentencePiece: https://github.com/google/sentencepiece
- ONNX Runtime: https://github.com/microsoft/onnxruntime
- Tokenizers / Hugging Face Hub: https://github.com/huggingface
- PyInstaller bootloader: https://pyinstaller.org/en/stable/license.html

Installed distribution license files are collected into `licenses/` during
the build. Model documentation travels with each model. The portable build
keeps shared libraries accessible under `_internal`, separate from the app.
The single-file build extracts those same shared libraries at startup.
