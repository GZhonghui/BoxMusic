# pip install moviepy

from moviepy import VideoFileClip
import os

video_filter = ['mp4', 'mkv']

video_dir = r'C:\Users\Admin\Desktop' # PASTE HERE
output_dir = os.path.join(os.path.expanduser('~'), 'Desktop', 'Output') # also works on Windows

def extract_audio(video_file_path, audio_file_path):
    video = VideoFileClip(video_file_path)
    audio = video.audio
    os.makedirs(os.path.dirname(audio_file_path), exist_ok=True)
    audio.write_audiofile(audio_file_path)
    video.close()

def main():
    print(f'[{video_dir}] -> [{output_dir}]')

    pre_l = len(video_dir)
    for root, dirs, files in os.walk(video_dir):
        for file_name in files:
            if file_name.split('.')[-1] not in video_filter: continue
            source_path = os.path.join(root, file_name)
            target_path = output_dir + source_path[pre_l:-3] + 'mp3'
            print(f'[{source_path}] -> [{target_path}]')
            extract_audio(source_path, target_path)

if __name__ == '__main__':
    main()