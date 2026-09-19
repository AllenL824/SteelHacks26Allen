from functools import lru_cache

import soundfile as sf
import torch
import torchaudio
from silero_vad import get_speech_timestamps, load_silero_vad

SAMPLE_RATE = 16000


@lru_cache(maxsize=1)
def _model():
    return load_silero_vad()


def _read_audio(path: str, sampling_rate: int = SAMPLE_RATE) -> torch.Tensor:
    """Load audio as a mono float32 tensor at `sampling_rate`.

    Deviation from the plan: silero_vad's own `read_audio` calls
    `torchaudio.load`, which on the installed torchaudio 2.9.1 hard-requires
    the `torchcodec` package for all I/O backends. The available torchcodec
    build (0.16.0) has an ABI mismatch with this torch build (dlopen fails
    with "Symbol not found: _torch_call_dispatcher"), so `read_audio` raises
    a RuntimeError even after installing torchcodec. We load the file with
    `soundfile` instead (no torchcodec dependency) and resample with
    `torchaudio.transforms.Resample`, which is pure tensor math and doesn't
    touch the broken I/O backend.
    """
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    wav = torch.from_numpy(data.T)  # (channels, samples)
    if wav.size(0) > 1:
        wav = wav.mean(dim=0, keepdim=True)
    if sr != sampling_rate:
        wav = torchaudio.transforms.Resample(sr, sampling_rate)(wav)
    return wav.squeeze(0)


def speech_regions(audio_path: str) -> list[tuple[float, float]]:
    wav = _read_audio(audio_path)  # resamples to 16k mono
    ts = get_speech_timestamps(wav, _model(), return_seconds=True)
    return [(t["start"], t["end"]) for t in ts]
