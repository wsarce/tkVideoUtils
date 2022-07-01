from tkinter import *
from tkvideoutils import VideoRecorder
from tkinter import messagebox


def merge_sources():
    if player.merge_sources(merged_path, ffmpeg_exe):
        print("Sources merged!")
    else:
        print("Something went wrong")


def stop_recording():
    player.stop_recording()
    player.stop_playback()
    button['command'] = merge_sources


def start_recording():
    player.start_recording()
    button['command'] = stop_recording


if __name__ == '__main__':
    # create instance of window
    root = Tk()
    # set window title
    root.title('Video Player')
    # load images
    pause_image = PhotoImage(file='pause.png')
    play_image = PhotoImage(file='play.png')
    # create user interface
    button = Button(root, image=play_image)
    video_label = Label(root)
    video_path = 'raw_video.mp4'
    audio_path = 'recorded_video.wav'
    merged_path = 'recorded_video.mp4'
    # place elements
    video_label.pack()
    button.pack()
    # Get existing video sources
    video_sources = VideoRecorder.get_video_sources()
    audio_sources = VideoRecorder.get_audio_sources()
    print(video_sources, audio_sources)
    # TODO: Fill out FFMPEG path
    ffmpeg_exe = r''

    if video_sources:
        if video_path:
            # read video to display on label
            player = VideoRecorder(video_source=video_sources[0], audio_source=audio_sources[1],
                                   video_path=video_path, audio_path=audio_path, fps=8, label=video_label,
                                   size=(700, 500))
            player.start_playback()
        else:
            messagebox.showwarning("Select Video File", "Please retry and select a video file.")
            sys.exit(1)
        button.config(command=start_recording)
        root.mainloop()
    else:
        print("No video sources found!")
