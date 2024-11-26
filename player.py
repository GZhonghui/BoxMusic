import vlc, os
import message as m

class AudioPlayer:
    def __init__(self):
        self.player = vlc.MediaPlayer()
        self.current_file = None
        self.on_play_end_func = None
        self.event_manager = self.player.event_manager()
        self.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)

    def play(self, file_path):
        if not os.path.exists(file_path):
            return

        if self.current_file != file_path:
            if self.current_file: self.stop()
            self.current_file = file_path
            media = vlc.Media(file_path)
            self.player.set_media(media)

        m.out(f'Player: start playing {file_path}')
        self.player.play()

    def pause(self):
        if self.player.is_playing():
            self.player.pause()

    def resume(self):
        if not self.player.is_playing():
            self.player.play()

    def stop(self):
        self.player.stop()

    def is_playing(self):
        return self.player.is_playing()

    def change_file(self, file_path):
        self.play(file_path)

    def get_progress(self):
        current_time = self.player.get_time()  # ms
        total_length = self.player.get_length()  # ms

        return [current_time, total_length]
    
    def seek_to_last_second(self):
        if not self.is_playing(): return
        total_length = self.player.get_length()  # ms
        if total_length > 1000:
            self.player.set_time(total_length - 1000)
    
    def _on_end_reached(self, event):
        last_path = self.current_file
        self.current_file = None
        if self.on_play_end_func: self.on_play_end_func(last_path)

if __name__ == '__main__':
    pass