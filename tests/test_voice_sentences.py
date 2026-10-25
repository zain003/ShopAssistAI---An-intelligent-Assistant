"""Tests for streaming sentence splitter used by TTS."""

from backend.voice.sentences import SentenceBuffer, split_sentences
from backend.voice.vad import pcm16_rms, SilenceDetector


def test_sentence_buffer_incremental():
    buf = SentenceBuffer()
    assert buf.push("Hello") == []
    assert buf.push(" there.") == ["Hello there."]
    assert buf.push(" Next") == []
    assert buf.push(" one!") == ["Next one!"]
    assert buf.flush() == []


def test_sentence_buffer_flush_leftover():
    buf = SentenceBuffer()
    buf.push("Almost done")
    assert buf.flush() == ["Almost done"]


def test_split_sentences_utility():
    parts = split_sentences("One. Two? Three!")
    assert parts == ["One.", "Two?", "Three!"]


def test_vad_silence_detection():
    det = SilenceDetector(
        silence_rms_threshold=100.0,
        silence_chunks_required=3,
        min_speech_chunks=1,
    )
    # Loud frame (approx)
    loud = (b"\xff\x7f") * 256
    assert pcm16_rms(loud) > 100
    assert det.observe(loud) is False
    quiet = (b"\x00\x00") * 256
    assert det.observe(quiet) is False
    assert det.observe(quiet) is False
    assert det.observe(quiet) is True
