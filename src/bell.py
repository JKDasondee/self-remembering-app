import os
import sys

def _base_path():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_mixer_ok = False
_sound = None

def init():
    global _mixer_ok, _sound
    try:
        import pygame
        pygame.mixer.init()
        p = os.path.join(_base_path(), "sounds", "tibetanbowl.mp3")
        if os.path.exists(p):
            _sound = pygame.mixer.Sound(p)
        _mixer_ok = True
    except Exception:
        _mixer_ok = False

def play():
    if _mixer_ok and _sound:
        try:
            _sound.play()
        except Exception:
            pass
