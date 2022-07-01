from tkinter import *

from ttkwidgets import TickScale

from tkvideoutils import VideoPlayer
from tkinter import filedialog, messagebox


def on_closing():
    player.loading = False
    root.quit()
    root.destroy()


if __name__ == '__main__':
    # create instance of window
    root = Tk()
    # set window title
    root.title('Video Player')
    # load images
    pause_image = PhotoImage(file='pause.png')
    play_image = PhotoImage(file='play.png')
    skip_backward = PhotoImage(file='skip_backward.png')
    skip_forward = PhotoImage(file='skip_forward.png')
    # create user interface
    button = Button(root, image=play_image)
    forward_button = Button(root, image=skip_forward)
    backward_button = Button(root, image=skip_backward)
    video_label = Label(root)
    video_path = 'recorded_video.mp4'
    audio_path = 'recorded_video.wav'
    slider_var = IntVar(root)
    slider = TickScale(root, orient="horizontal", variable=slider_var)
    # place elements
    video_label.pack()
    button.pack()
    forward_button.pack()
    backward_button.pack()
    slider.pack()

    if video_path:
        # read video to display on label
        player = VideoPlayer(root, video_path, audio_path, video_label, size=(700, 500),
                             play_button=button, play_image=play_image, pause_image=pause_image,
                             slider=slider, slider_var=slider_var, keep_ratio=True, cleanup_audio=True)
    else:
        messagebox.showwarning("Select Video File", "Please retry and select a video file.")
        sys.exit(1)
    player.set_clip(50, 70)
    forward_button.config(command=player.skip_video_forward)
    backward_button.config(command=player.skip_video_backward)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
