import os
import math
import struct
import tempfile
import wave

try:
    from PyQt5.QtCore import QUrl
    from PyQt5.QtMultimedia import QSoundEffect
    _MULTIMEDIA_AVAILABLE = True
except Exception:
    _MULTIMEDIA_AVAILABLE = False


def _write_tone(path, notes, volume=0.22, sample_rate=44100):
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for freq, duration in notes:
            n = max(1, int(sample_rate * duration))
            fade = max(1, int(sample_rate * 0.015))
            for i in range(n):
                t = i / sample_rate
                env = 1.0
                if i < fade:
                    env = i / fade
                elif i > n - fade:
                    env = (n - i) / fade
                sample = volume * env * math.sin(2 * math.pi * freq * t)
                frames += struct.pack("<h", int(sample * 32767))
        wf.writeframes(bytes(frames))


class SoundManager:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self._effects = {}
        if not _MULTIMEDIA_AVAILABLE:
            return
        try:
            self._dir = tempfile.mkdtemp(prefix="ecobalance_sfx_")
            self._build("click", [(880, 0.045), (1180, 0.035)], volume=0.16)
            self._build("chime", [(660, 0.10), (880, 0.16)], volume=0.20)
            self._build("alert", [(520, 0.09), (390, 0.16)], volume=0.22)
            self._build("fire", [(160, 0.08), (125, 0.08), (185, 0.08), (110, 0.12)], volume=0.20)
            self._build("plague", [(280, 0.12), (235, 0.12), (190, 0.18)], volume=0.18)
            self._build("drought", [(220, 0.10), (170, 0.18)], volume=0.17)
            self._build("place", [(740, 0.05), (980, 0.07)], volume=0.15)
        except Exception:
            self._effects = {}

    def _build(self, name, notes, volume):
        path = os.path.join(self._dir, f"{name}.wav")
        _write_tone(path, notes, volume=volume)
        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(path))
        effect.setVolume(0.6)
        self._effects[name] = effect

    def _play(self, name):
        if not self.enabled or not _MULTIMEDIA_AVAILABLE:
            return
        effect = self._effects.get(name)
        if effect is not None:
            try:
                effect.play()
            except Exception:
                pass

    def play_click(self):
        self._play("click")

    def play_chime(self):
        self._play("chime")

    def play_alert(self):
        self._play("alert")

    def play_fire(self):
        self._play("fire")

    def play_plague(self):
        self._play("plague")

    def play_drought(self):
        self._play("drought")

    def play_place(self):
        self._play("place")
