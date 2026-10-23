`sample.wav` is synthetic English speech generated locally with Windows SAPI.
It contains this original test sentence:

> Hello. This is a test of the offline speech translation application. The
> meeting starts tomorrow at nine in the morning.

The fixture is distributed under the repository's Apache-2.0 license. Tests
encode it to MP3 using PyAV and verify decoding, automatic language detection,
recognition, and the complete GUI and packaged-EXE workflows. It is not a song
and does not measure recognition quality for sung vocals.
