"""
Audio Player — VLC-based audio player for karaoke sync
"""
import sys
import threading
from typing import Callable, Optional


class AudioPlayer:
    """
    Wraps python-vlc for audio playback with precise time tracking.
    Falls back gracefully if VLC is not installed.
    """

    def __init__(self):
        self._instance = None
        self._player = None
        self._available = False
        self._position_callback: Optional[Callable] = None
        self._end_callback: Optional[Callable] = None
        self._poll_timer: Optional[threading.Timer] = None
        self._poll_interval = 0.1  # 100ms

        self._try_init_vlc()

    def _try_init_vlc(self):
        """Try to initialize VLC. Sets _available flag.

        On Linux, headless servers (no DISPLAY) still need libvlc to load
        even though there's no display — the AudioPlayer does not open a
        video window, only an audio stream. We don't pass --no-xlib on
        non-Windows because that flag is X11-only and confuses the macOS
        VLC bindings.
        """
        try:
            import vlc
            if sys.platform.startswith("win"):
                instance_args = ["--no-xlib", "--quiet"]
            else:
                instance_args = ["--quiet"]
            self._instance = vlc.Instance(*instance_args)
            self._player = self._instance.media_player_new()
            self._available = True
        except (ImportError, Exception):
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def load(self, filepath: str) -> bool:
        """Load an audio file. Returns True on success."""
        if not self._available:
            return False
        try:
            import vlc
            media = self._instance.media_new(filepath)
            self._player.set_media(media)
            return True
        except Exception:
            return False

    def play(self):
        if self._available and self._player:
            self._player.play()
            self._start_polling()

    def pause(self):
        if self._available and self._player:
            self._player.pause()

    def stop(self):
        if self._available and self._player:
            self._player.stop()
            self._stop_polling()

    def seek(self, ms: int):
        """Seek to position in milliseconds."""
        if self._available and self._player:
            self._player.set_time(ms)

    def get_time_ms(self) -> int:
        """Get current playback position in milliseconds."""
        if self._available and self._player:
            t = self._player.get_time()
            return max(0, t)
        return 0

    def get_duration_ms(self) -> int:
        """Get total duration in milliseconds."""
        if self._available and self._player:
            d = self._player.get_length()
            return max(0, d)
        return 0

    def is_playing(self) -> bool:
        if self._available and self._player:
            return self._player.is_playing() == 1
        return False

    def set_volume(self, volume: int):
        """Set volume 0-100."""
        if self._available and self._player:
            self._player.audio_set_volume(max(0, min(100, volume)))

    def set_position_callback(self, callback: Callable):
        """callback(time_ms: int) called every ~100ms during playback."""
        self._position_callback = callback

    def set_end_callback(self, callback: Callable):
        """callback() called when playback ends."""
        self._end_callback = callback

    def _start_polling(self):
        self._stop_polling()
        self._poll()

    def _stop_polling(self):
        if self._poll_timer:
            self._poll_timer.cancel()
            self._poll_timer = None

    def _poll(self):
        """Poll VLC for current time and dispatch callbacks."""
        if not self._available or not self._player:
            return

        if self.is_playing():
            t = self.get_time_ms()
            if self._position_callback:
                self._position_callback(t)
            self._poll_timer = threading.Timer(self._poll_interval, self._poll)
            self._poll_timer.daemon = True
            self._poll_timer.start()
        else:
            # Check if ended
            try:
                import vlc
                state = self._player.get_state()
                if state == vlc.State.Ended:
                    if self._end_callback:
                        self._end_callback()
            except Exception:
                pass

    def cleanup(self):
        """Release resources."""
        self._stop_polling()
        if self._player:
            try:
                self._player.stop()
                self._player.release()
            except Exception:
                pass
        if self._instance:
            try:
                self._instance.release()
            except Exception:
                pass


# Singleton instance
_player_instance: Optional[AudioPlayer] = None


def get_player() -> AudioPlayer:
    global _player_instance
    if _player_instance is None:
        _player_instance = AudioPlayer()
    return _player_instance
