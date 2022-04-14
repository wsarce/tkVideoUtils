""" tkVideoUtils: Python module for playing and recording videos (without sound) inside tkinter Label widget using
Pillow and imageio

Copyright © 2022 Walker Arce (wsarcera@gmail.com)
Released under the terms of the MIT license (https://opensource.org/licenses/MIT) as described in LICENSE.md
"""
import os
import pathlib
import shutil
import time
from tkinter import ttk

from ttkwidgets import TickScale

try:
    import Tkinter as tk  # for Python2 (although it has already reached EOL)
except ImportError:
    import tkinter as tk  # for Python3
import threading
import imageio
import cv2
from PIL import Image, ImageTk


class VideoRecorder:
    """
    Class that handles the recording and streaming of video
    """

    def __init__(self, source, path, fps, label, size=(640, 360), keep_ratio=True):
        """
        Streams, records, and handles webcam feeds
        :param source: tuple: Use VideoRecorder.get_sources() to get compatible sources
        :param path: path-like: Output save path of the recorded video
        :param fps: float or int: The recording frames per second
        :param label: Tk Label: The Label that will be used to display the video
        :param size: tuple: The height and width of the video on the Label
        :param keep_ratio: bool: If true, the aspect ratio is kept for the video
        """
        self.fps = fps
        self.frame_duration = float(1 / self.fps)
        self.label = label
        self.output_path = path
        self.source = source
        self.thread = None
        self.recording = False
        self.playing = False
        self.cam = None
        self.writer = None
        self.current_frame = 0
        if keep_ratio:
            self.aspect_ratio = float(source[1][1]) / float(source[1][0])
            self.size = (size[0], int(size[0] / self.aspect_ratio))
        else:
            self.size = size

    @staticmethod
    def get_sources():
        """
        Polls webcam sources and find their video resolution, i.e., (0, (780, 420)).  Passing one of these sources to
        the VideoRecorder object will allow it to use that camera.
        :return: List of tuples containing found sources and their resolution.
        """
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
        """
        Thread that plays and records video in the background.  Will only update the image on the Label is the Label
        is currently being viewed.
        :return: None
        """
        while self.playing:
            try:
                im = self.cam.get_next_data()
                if self.recording:
                    self.writer.append_data(im)
                    self.current_frame += 1
                if self.label.winfo_viewable():
                    frame_image = ImageTk.PhotoImage(Image.fromarray(im).resize(self.size))
                    self.label.config(image=frame_image)
                    self.label.image = frame_image
                time.sleep(self.frame_duration - time.monotonic() % self.frame_duration)
            except Exception:
                continue
        if self.writer:
            self.writer.close()
        self.cam.close()

    def start_recording(self, output_path=None):
        """
        Start webcam recording, if an output path is provided then the original output path is overwritten.
        :param output_path: path-like: Desired absolute filepath for the recorded video
        :return: None
        """
        if output_path:
            self.output_path = output_path
            self.writer = imageio.get_writer(output_path, fps=self.fps)
        else:
            self.writer = imageio.get_writer(self.output_path, fps=self.fps)
        self.recording = True

    def stop_recording(self):
        """
        Sets the recording variable to False, which will stap the saving of frames to the output file.
        :return: None
        """
        self.recording = False

    def stop_playback(self):
        """
        Stops the playback for the VideoRecorder.  Thread is terminated.
        :return: None
        """
        self.playing = False

    def start_playback(self):
        """
        Setup webcam source and start the background thread.  The video will start streaming to the Label.
        :return: None
        """
        self.playing = True
        self.current_frame = 0
        self.cam = imageio.get_reader(f'<video{self.source[0]}>', fps=self.fps)
        self.thread = threading.Thread(target=self.recording_thread)
        self.thread.daemon = 1
        self.thread.start()


class VideoPlayer:
    """
    Class that handles the streaming of a video file from the filesystem to a Label.
    """

    def __init__(self, root, path, label, size=(640, 360), play_button=None, play_image=None, pause_image=None,
                 slider=None, slider_var=None, keep_ratio=False, skip_size_s=1, override_slider=False):
        """
        Streams a video on the filesystem to a tkinter Label.
        :param path: path-like: Absolute path to the video file to be streamed
        :param label: Tk Label: The Label that will stream the video
        :param size: tuple: The size of the video on the Tk Label.
        :param play_button: Tk Button: Pass in a Button that will be wired up to control the play/pause of the video
        :param play_image: PhotoImage: The image that will be on the play_button if the video is paused
        :param pause_image: PhotoImage: The image that will be on the play_button if the video is playing
        :param slider: Tk Slider: Pass in a Slider that will be wired up to control the loaded frame
        :param slider_var: Tk IntVar: Control variable that can be used to monitor the frame index
        :param keep_ratio: bool: If True, the source aspect ratio will be kept
        :param skip_size_s: int: The number of seconds the video should skip when skipped forward or backward
        :param override_slider: bool: Set to true if you want to configure an external callback for the Slider
        """
        self.root = root
        self.path = path
        self.label = label
        self.playing = False
        self.skip_forward, self.skip_backward = False, False
        self.skip_size = skip_size_s
        self.frame_data = imageio.get_reader(path)
        meta_data = cv2.VideoCapture(path)
        self.fps = meta_data.get(cv2.CAP_PROP_FPS)
        self.frame_duration = float(1 / self.fps)
        self.nframes = int(meta_data.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        if keep_ratio:
            temp = self.frame_data._get_data(0)[0].shape
            self.aspect_ratio = float(temp[1]) / float(temp[0])
            self.size = (size[0], int(size[0] / self.aspect_ratio))
        else:
            self.size = size
        self.slider = slider
        self.slider_var = slider_var
        self.override_slider = override_slider
        if self.slider:
            if type(self.slider) == tk.Scale:
                self.slider.config(from_=1, to=self.nframes)
                self.slider.config(length=size[0])
                if not override_slider:
                    self.slider.config(command=self.__slider_frame_load)
                self.slider_var = slider_var
                self.slider_var.set(1)
            elif type(self.slider) == TickScale:
                self.trough_img = tk.PhotoImage('img_trough', width=size[0], height=10, master=self.root)
                self.set_img_color(self.trough_img, ['white', 'red'], [size[0], 0])
                style_name = self.__create_slider_style()
                self.slider.configure(style=style_name)
                self.slider.configure(from_=1, to=int(self.nframes))
                self.slider.configure(length=size[0])
                self.slider.configure(resolution=1)
                if not override_slider:
                    self.slider.configure(command=self.__slider_frame_load)
        self.play_button = play_button
        self.play_image = play_image
        self.pause_image = pause_image
        if self.play_button:
            self.play_button.config(image=self.play_image, command=self.toggle_video)
        self.load_frame_index = 0
        self.loading = True
        self.frames = [None] * self.nframes
        self.load_thread = threading.Thread(target=self.__load_video)
        self.load_thread.start()

    @staticmethod
    def set_img_color(img, colors, widths):
        """
        Sets the colors of a PhotoImage column by column in place
        Example: set_img_color(img, ['white', 'red'], [100, 100])
        Sets a column of width 100px to white and a column of width 100px to red from left to right
        :param img: PhotoImage
        :param colors: list, colors to set columns to
        :param widths: list, widths to set columns to
        :return: None
        """
        pixel_line = "{"
        for color, width in zip(colors, widths):
            for i in range(0, width):
                pixel_line = pixel_line + f" {color}"
        pixel_line = pixel_line + "}"
        pixels = " ".join(pixel_line for i in range(img.height()))
        img.put(pixels)

    def __clear_loading_slider(self):
        """
        Clears the loading slider to a solid color
        :return: None
        """
        self.set_img_color(self.trough_img, ['white', 'red'],
                           [int(self.size[0] * (self.load_frame_index / self.nframes)), 0])
        self.slider.configure(style='custom.Horizontal.TScale')

    def __update_loading_slider(self):
        """
        Updates the loading slider to the current number of loaded frames
        :return: None
        """
        self.set_img_color(self.trough_img, ['white', 'red'],
                           [int(self.size[0] * (self.load_frame_index / self.nframes)),
                            self.size[0] - int(self.size[0] * (self.load_frame_index / self.nframes))])
        self.slider.configure(style='custom.Horizontal.TScale')

    def __create_slider_style(self):
        fig_color = '#%02x%02x%02x' % (240, 240, 237)
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        self.style.element_create('Horizontal.Scale.trough', 'image', self.trough_img)
        # create custom layout
        self.style.layout('custom.Horizontal.TScale',
                          [('Horizontal.Scale.trough',
                            {'sticky': 'nswe',
                             'children': [('custom.Horizontal.Scale.slider',
                                           {'side': 'left', 'sticky': ''})]})])
        self.style.configure('custom.Horizontal.TScale', background=fig_color)
        return 'custom.Horizontal.TScale'

    def __load_video(self):
        """
        Background thread to load in frames to prevent issues when playing
        :return: None
        """
        self.load_frame_index = 0
        frame_data = imageio.get_reader(self.path)
        for image in frame_data.iter_data():
            try:
                self.frames[self.load_frame_index] = (ImageTk.PhotoImage(Image.fromarray(image).resize(self.size)))
                if self.load_frame_index == 1:
                    self.load_frame(1)
                if self.load_frame_index % 10:
                    if self.slider:
                        if type(self.slider) == TickScale:
                            self.__update_loading_slider()
                self.load_frame_index += 1
                if not self.loading:
                    break
            except IndexError as e:
                break
        self.__clear_loading_slider()

    def play_video(self):
        """
        If the video is paused, play it.  If the play button exists, change the image on it.
        :return:
        """
        if not self.playing:
            self.play()
            if self.play_button:
                self.play_button.config(image=self.pause_image)

    def pause_video(self):
        """
        If the video is playing, pause it.  If the play button exists, change the image on it.
        :return: None
        """
        if self.playing:
            self.stop_playing()
            if self.play_button:
                self.play_button.config(image=self.play_image)

    def toggle_video(self):
        """
        If the video is playing, pause it, if the video is paused, play it.
        :return: None
        """
        if not self.playing:
            self.play_video()
        else:
            self.pause_video()

    def __slider_frame_load(self, value):
        """
        Callback for the slider to load a frame
        :param value: str: The slider value
        :return: None
        """
        self.load_frame(value)

    def load_frame(self, frame):
        """
        Loads the selected frame index into the Tk Label and sets the necessary control variables.
        :param frame: int: The frame to load.
        :return: None
        """
        if int(float(frame)) != self.current_frame:
            frame_image = self.frames[int(float(frame)) - 1]
            if frame_image:
                self.label.config(image=frame_image)
                self.label.image = frame_image
                self.current_frame = int(float(frame))
                if self.slider:
                    self.slider.set(self.current_frame)
            else:
                if self.slider:
                    self.slider.set(self.current_frame)

    def stop_playing(self):
        """
        Stop the playback of the video, thread will terminate.
        :return: None
        """
        if self.playing:
            self.playing = False

    def skip_video_forward(self):
        """
        Skips the video feed forward by either telling the Thread to do it, or by changing the current frame and loading
        the frame.
        :return: None
        """
        if self.playing:
            self.skip_forward = True
        else:
            self.load_frame(self.current_frame + int(self.skip_size * self.fps))

    def skip_video_backward(self):
        """
        Skips the video feed backward by either telling the Thread to do it, or by changing the current frame and loading
        the frame.
        :return: None
        """
        if self.playing:
            self.skip_backward = True
        else:
            self.load_frame(self.current_frame - int(self.skip_size * self.fps))

    def __playing_thread(self):
        """
        Thread that will stream the video file to a Label at the source frame rate.
        :return: None
        """
        n = self.nframes
        i = int(self.current_frame)
        self.playing = True
        while i < n:
            if not self.playing:
                break
            try:
                if i < self.load_frame_index:
                    im = self.frames[i]
                    self.current_frame = i
                    if self.label.winfo_viewable():
                        frame_image = im
                        self.label.config(image=frame_image)
                        self.label.image = frame_image
                        if self.override_slider:
                            if self.slider:
                                # Trigger callback each time a frame is loaded
                                self.slider.set(i)
                        else:
                            if self.slider_var:
                                self.slider_var.set(i)
                    if self.skip_forward:
                        i += int(self.skip_size * self.fps)
                        self.skip_forward = False
                    elif self.skip_backward:
                        i -= int(self.skip_size * self.fps)
                        self.skip_backward = False
                    else:
                        i += 1
                    time.sleep(self.frame_duration - time.monotonic() % self.frame_duration)
            except StopIteration as e:
                print(str(e))
                break
            except IndexError as e:
                print(str(e))
                self.playing = False
                if n == float("inf"):
                    break
                raise
        self.playing = False
        if self.current_frame > self.nframes:
            self.current_frame = self.nframes
        if self.play_button:
            self.play_button.config(image=self.play_image)

    def play(self):
        """
        Creates a thread that plays the video frames onto the Label at the source FPS.
        :return: None
        """
        self.playing = True
        if self.current_frame == self.nframes:
            self.current_frame = 0
        thread = threading.Thread(target=self.__playing_thread)
        thread.start()


def cp_rename(src, dst, name):
    """
    Small utility for handling recorded videos.  Copy and rename a file on the filesystem.
    :param src: path-like: Absolute filepath to the source video
    :param dst: path-like: Absolute filepath to the folder to move the src to
    :param name: str: New name for file being moved
    :return:
    """
    shutil.copy2(src, dst)
    dst_file = os.path.join(dst, pathlib.Path(src).name)
    new_dst_file = os.path.join(dst, name + pathlib.Path(src).suffix)
    os.rename(dst_file, new_dst_file)
