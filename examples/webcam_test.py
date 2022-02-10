from tkinter import *
from tkvideoutils import VideoRecorder
from tkinter import messagebox


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
    video_path = 'test.mp4'
    # place elements
    video_label.pack()
    button.pack()
    # Get existing video sources
    video_sources = VideoRecorder.get_sources()

    if video_sources:
        if video_path:
            # read video to display on label
            player = VideoRecorder(source=video_sources[0], path=video_path, fps=30, label=video_label, size=(700, 500))
            player.start_playback()
        else:
            messagebox.showwarning("Select Video File", "Please retry and select a video file.")
            sys.exit(1)
        button.config(command=player.start_recording)
        root.mainloop()
    else:
        print("No video sources found!")
