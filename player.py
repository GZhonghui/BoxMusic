import vlc, os

class AudioPlayer:
    def __init__(self):
        self.player = vlc.MediaPlayer()
        self.current_file = None

    def play(self, file_path):
        if not os.path.exists(file_path):
            return

        if self.current_file != file_path:
            self.stop()
            self.current_file = file_path
            media = vlc.Media(file_path)
            self.player.set_media(media)

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

if __name__ == '__main__':
    pass