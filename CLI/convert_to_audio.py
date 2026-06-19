# pip install moviepy

# from moviepy import VideoFileClip # Windows py39+
from moviepy.editor import VideoFileClip # Mac py38

import os

video_filter = ['mp4', 'mkv']

video_dir = r'C:\Users\Admin\Dropbox\Apps\ZhonghuiPlayer\视频\Video' # PASTE HERE
compare_dir = r'C:\Users\Admin\Dropbox\Apps\ZhonghuiPlayer\视频\Audio' # PASTE HERE
output_dir = os.path.join(os.path.expanduser('~'), 'Desktop', 'Output') # also works on Windows

def extract_audio(video_file_path, audio_file_path):
    video = VideoFileClip(video_file_path)
    audio = video.audio
    os.makedirs(os.path.dirname(audio_file_path), exist_ok=True)
    audio.write_audiofile(audio_file_path)
    video.close()

def convert_full_dir(dir_path: str):
    files = [file for file in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, file)) and file.split('.')[-1] in video_filter]
    for file in files:
        target_file_name = file[:-3] + 'mp3'
        source_path = os.path.join(dir_path, file)
        target_path = os.path.join(dir_path, target_file_name)
        print(f'[{source_path}] -> [{target_path}]')
        extract_audio(source_path, target_path)

def convert_video_dir():
    print(f'[{video_dir}] -> [{output_dir}]')

    pre_l = len(video_dir)
    for root, dirs, files in os.walk(video_dir):
        for file_name in files:
            if file_name.split('.')[-1] not in video_filter: continue
            source_path = os.path.join(root, file_name)
            target_path = output_dir + source_path[pre_l:-3] + 'mp3'
            compare_path = compare_dir + source_path[pre_l:-3] + 'mp3'
            if os.path.exists(compare_path) and os.path.isfile(compare_path):
                print(f'[{compare_path}] exists, skip...')
            else:
                print(f'Convert: [{source_path}] -> [{target_path}]')
                extract_audio(source_path, target_path)

def main():
    # convert_video_dir() # run on windows
    # convert_full_dir('/Users/anny/Dropbox/Apps/ZhonghuiPlayer/原声/漫长的季节/配乐专辑')
    pass

if __name__ == '__main__':
    main()