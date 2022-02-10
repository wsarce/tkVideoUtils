""" tkVideoUtils: Python module for playing and recording videos (without sound) inside tkinter Label widget using
Pillow and imageio

Copyright © 2022 Walker Arce (wsarcera@gmail.com)
Released under the terms of the MIT license (https://opensource.org/licenses/MIT) as described in LICENSE.md
"""
import time
try:
    import Tkinter as tk  # for Python2 (although it has already reached EOL)
except ImportError:
    import tkinter as tk  # for Python3
import threading
import imageio
import cv2
from PIL import Image, ImageTk


class VideoRecorder:
    def __init__(self, source, path, fps, label, size=(640, 360), keep_ratio=True):
        self.fps = fps
        self.frame_duration = float(1 / self.fps)
        self.label = label
        self.output_path = path
        self.input_source = source[0]
        self.cam = imageio.get_reader(f'<video{source[0]}>', fps=fps)
        self.writer = imageio.get_writer(path, fps=fps)
        self.thread = None
        self.recording = False
        if keep_ratio:
            self.aspect_ratio = float(source[1][1]) / float(source[1][0])
            self.size = (size[0], int(size[0] / self.aspect_ratio))
        else:
            self.size = size

    @staticmethod
    def get_sources():
        sources = []
        for i in range(0, 10):
            try:
                cam = imageio.get_reader(f'<video{i}>', fps=8)
                sources.append((i, cam.get_next_data().shape[0:2]))
                cam.close()
            except IndexError:
                break
        return sources

    def recording_thread(self):
        while self.recording:
            im = self.cam.get_next_data()
            self.writer.append_data(im)
            if self.label.winfo_viewable():
                frame_image = ImageTk.PhotoImage(Image.fromarray(im).resize(self.size))
                self.label.config(image=frame_image)
                self.label.image = frame_image
            time.sleep(self.frame_duration - time.monotonic() % self.frame_duration)

    def stop_recording(self):
        self.recording = False

    def record(self):
        self.recording = True
        self.thread = threading.Thread(target=self.recording_thread)
        self.thread.daemon = 1
        self.thread.start()


class VideoPlayer:
    """
        Main class of tkVideo. Handles loading and playing
        the video inside the selected label.

        :keyword path:
            Path of video file
        :keyword label:
            Name of label that will house the player
        :param loop:
            If equal to 0, the video only plays once,
            if not it plays in an infinite loop (default 0)
        :param size:
            Changes the video's dimensions (2-tuple,
            default is 640x360)
    """

    def __init__(self, path, label, loop=False, size=(640, 360), play_button=None, play_image=None, pause_image=None,
                 slider=None, slider_var=None, keep_ratio=False, skip_size_s=1):
        self.path = path
        self.label = label
        self.loop = loop
        self.playing = False
        self.skip_forward, self.skip_backward = False, False
        self.skip_size = skip_size_s
        self.frame_data = imageio.get_reader(path)
        meta_data = cv2.VideoCapture(path)
        # self.meta_data = self.frame_data.get_meta_data()
        self.fps = meta_data.get(cv2.CAP_PROP_FPS)
        self.frame_duration = float(1 / self.fps)
        self.nframes = int(meta_data.get(cv2.CAP_PROP_FRAME_COUNT))
        # if self.nframes == float("inf"):
        #     self.nframes = int(float(self.fps) * float(self.meta_data['duration']))
        self.current_frame = 0
        if keep_ratio:
            temp = self.frame_data._get_data(0)[0].shape
            self.aspect_ratio = float(temp[1]) / float(temp[0])
            self.size = (size[0], int(size[0] / self.aspect_ratio))
        else:
            self.size = size
        self.slider = slider
        if self.slider:
            self.slider.config(from_=1, to=self.nframes)
            self.slider.config(length=size[0], command=self.slider_frame_load)
            self.slider_var = slider_var
            self.slider_var.set(1)
        self.play_button = play_button
        self.play_image = play_image
        self.pause_image = pause_image
        if self.play_button:
            self.play_button.config(image=self.play_image, command=self.toggle_video)
        self.load_frame(1)

    def toggle_video(self):
        if not self.playing:
            self.play()
            self.playing = True
            if self.play_button:
                self.play_button.config(image=self.pause_image)
        else:
            self.stop_playing()
            self.playing = False
            if self.play_button:
                self.play_button.config(image=self.play_image)

    def slider_frame_load(self, value):
        self.load_frame(value)

    def load_frame(self, frame):
        image, met = self.frame_data._get_data(int(frame) - 1)
        frame_image = ImageTk.PhotoImage(Image.fromarray(image).resize(self.size))
        self.label.config(image=frame_image)
        self.label.image = frame_image
        self.current_frame = int(frame)
        if self.slider:
            self.slider.set(self.current_frame)

    def stop_playing(self):
        if self.playing:
            self.playing = False

    def skip_video_forward(self):
        if self.playing:
            self.skip_forward = True
        else:
            self.current_frame = self.current_frame + int(self.skip_size * self.fps)
            self.load_frame(self.current_frame)

    def skip_video_backward(self):
        if self.playing:
            self.skip_backward = True
        else:
            self.current_frame = self.current_frame - int(self.skip_size * self.fps)
            self.load_frame(self.current_frame)

    def iter_data_index(self, path, label, frame, slider):
        """ iter_data()
        Iterate over all images in the series. (Note: you can also
        iterate over the reader object.)
        """
        frame_data = imageio.get_reader(path)
        frame_data._checkClosed()
        n = frame_data.get_length()
        i = int(frame)
        self.playing = True
        while i < n:
            # start = time.perf_counter_ns()
            if not self.playing:
                break
            try:
                im, meta = frame_data._get_data(i)
                self.current_frame = i
            except StopIteration as e:
                print(str(e))
                break
            except IndexError as e:
                print(str(e))
                self.playing = False
                if n == float("inf"):
                    break
                raise
            if self.label.winfo_viewable():
                frame_image = ImageTk.PhotoImage(Image.fromarray(im).resize(self.size))
                label.config(image=frame_image)
                label.image = frame_image
                if self.slider_var:
                    self.slider_var.set(i)
            if self.skip_forward:
                i += int(self.skip_size * self.fps)
                self.skip_forward = False
            elif self.skip_backward:
                i += int(self.skip_size * self.fps)
                self.skip_backward = False
            i += 1
            # end = time.perf_counter_ns()
            # processing_time = float(end - start) / float(1000000000)
            # print(processing_time)
            # time.sleep((self.frame_duration - processing_time) - time.monotonic() %
            #            (self.frame_duration - processing_time))
            time.sleep(self.frame_duration - time.monotonic() % self.frame_duration)
        self.playing = False
        if self.current_frame > self.nframes:
            self.current_frame = self.nframes
        if self.play_button:
            self.play_button.config(image=self.play_image)

    def play(self):
        """
            Creates and starts a thread as a daemon that plays the video by rapidly going through
            the video's frames.
        """
        if self.current_frame == self.nframes:
            self.current_frame = 0
        thread = threading.Thread(target=self.iter_data_index,
                                  args=(self.path, self.label, self.current_frame, self.slider))
        thread.daemon = 1
        thread.start()
