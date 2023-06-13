from tkinter import *
from tkvideoutils import VideoRecorder
import threading


class Master_UI:
    def __init__(self, master):
        self.video_count = 0
        self.master = master
        self.master.title("project")
        self.master.geometry("640x600")
        self.io_frame = Frame(self.master)
        self.io_frame.pack(fill=BOTH, expand=True, side=BOTTOM)
        # Bind key press event to the window
        root.bind("<KeyPress>", self.on_key_press)
        # first number is start_recording enabled or not, second is end_recording enabled or not, and last is submit enabled or not
        self.button_state = "100"
        # initiate the dialogue model instance

        video_sources = VideoRecorder.get_video_sources()
        audio_sources = VideoRecorder.get_audio_sources()
        print(video_sources, audio_sources)

        self.ffmpeg_exe = r"D:\GitHub Repos\KeystrokeAnnotator\external_bin\ffmpeg\ffmpeg-win64-v4.2.2.exe"
        self.video_path = 'video.mp4'
        self.audio_path = 'recorded_audio.wav'
        self.merged_path = 'video.mp4'
        self.recording_label = Label(self.io_frame, text="")
        self.recording_label.pack()
        if video_sources:
            if self.video_path:
                # read video to display on label
                self.recording = VideoRecorder(video_source=video_sources[0], audio_source=audio_sources[1],
                                               video_path=self.video_path, audio_path=self.audio_path, fps=30,
                                               label=self.recording_label, keep_playing=True,
                                               size=(300, 300))
                self.recording.start_playback()

        self.is_recording = False

    def merge_sources(self):
        self.recording.close_video_recording()
        merge_thread = threading.Thread(target=self.merge_sources_thread)
        merge_thread.daemon = False
        merge_thread.start()

    def merge_sources_thread(self):
        self.video_count += 1
        self.merged_path = f"video_{self.video_count}.mp4"
        if self.recording.merge_sources(self.merged_path, self.ffmpeg_exe, delete_file=False):
            print("Sources merged!")
        else:
            print("Something went wrong")

    # Function to start recording audio
    def start_recording(self):
        self.button_state = "010"
        self.recording.start_recording()
        self.is_recording = True

        print("Recording started...")

    # Function to stop recording audio
    def stop_recording(self):
        # Stop the audio stream
        self.is_recording = False
        self.recording.recording = False
        self.merge_sources()
        self.button_state = "101"
        # self.submit()
        print("Recording stopped.")

    # Function to handle key press events
    def on_key_press(self, event):
        if event.char == ' ':
            if self.button_state[0] == '1':
                self.start_recording()
            elif self.button_state[1] == '1':
                self.stop_recording()


def on_closing():
    root.quit()
    root.destroy()


if __name__ == "__main__":
    root = Tk()
    app = Master_UI(root)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()