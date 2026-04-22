"""Audio package for the 3D Hunting Simulator."""

try:
    from audio.audio_manager import AudioManager
    __all__ = ['AudioManager']
except ImportError:
    __all__ = []
