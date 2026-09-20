from functools import lru_cache

import numpy as np
import torch
from pydub import AudioSegment
from silero_vad import get_speech_timestamps, load_silero_vad

SAMPLE_RATE = 16000


@lru_cache(maxsize=1)
def _model():
    return load_silero_vad()


def _read_audio(path: str, sampling_rate: int = SAMPLE_RATE) -> torch.Tensor:
    """Load audio as a mono float32 tensor at `sampling_rate`.

    Uses pydub (ffmpeg-backed) so every format Whisper can read — wav, m4a/AAC,
    mp3, … — decodes here too. Plain `soundfile` (libsndfile) can't open m4a,
    which is what phones/QuickTime/Gradio-mic produce, so a recording or upload
    would otherwise crash the VAD with "Format not recognised".
    """
    seg = (
        AudioSegment.from_file(path)
        .set_channels(1)
        .set_frame_rate(sampling_rate)
        .set_sample_width(2)  # 16-bit
    )
    samples = np.frombuffer(seg.raw_data, dtype=np.int16).astype(np.float32) / 32768.0
    return torch.from_numpy(samples)


@lru_cache(maxsize=None)
def speech_regions(audio_path: str) -> list[tuple[float, float]]:
    wav = _read_audio(audio_path)  # resamples to 16k mono
    ts = get_speech_timestamps(wav, _model(), return_seconds=True)
    return [(t["start"], t["end"]) for t in ts]
