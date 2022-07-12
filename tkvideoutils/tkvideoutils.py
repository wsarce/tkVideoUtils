""" tkVideoUtils: Python module for playing and recording videos with sound inside tkinter Label widget using
Pillow, imageio, and PyAudio

Copyright © 2022 Walker Arce (wsarcera@gmail.com)
Released under the terms of the MIT license (https://opensource.org/licenses/MIT) as described in LICENSE.md
"""
import _tkinter
import os
import pathlib
import shutil
import time
import traceback
import wave
from tkinter import ttk
import ffmpy
from moviepy.editor import AudioFileClip
from ttkwidgets import TickScale

try:
    import Tkinter as tk  # for Python2 (although it has already reached EOL)
except ImportError:
    import tkinter as tk  # for Python3
import threading
import imageio
import cv2
import pyaudio
from itertools import count
from tkinter import *
from PIL import Image, ImageTk


class ImageLabel:
    """a label that displays images, and plays them if they are gifs
    https://stackoverflow.com/a/43770948
    """
    def __init__(self, im, label, size):
        self.load(im, label, size)

    def load(self, im, label, size=(300, 300)):
        if isinstance(im, str):
            im = Image.open(im)
        self.size = (size[0]-50, size[1]-50)
        self.loc = 0
        self.frames = []
        self.label = label
        try:
            for i in count(1):
                self.frames.append(ImageTk.PhotoImage(im.copy().resize(self.size, Image.ANTIALIAS)))
                im.seek(i)
        except EOFError:
            pass

        try:
            self.delay = im.info['duration']
        except:
            self.delay = 100

        if len(self.frames) == 1:
            self.label.config(image=self.frames[0])
        else:
            self.next_frame()

    def unload(self):
        try:
            self.label.config(image="")
            self.frames = None
        except _tkinter.TclError:
            pass

    def next_frame(self):
        try:
            if self.frames:
                self.loc += 1
                self.loc %= len(self.frames)
                if not self.loc:
                    self.loc = 1
                self.label.config(image=self.frames[self.loc])
                self.label.after(self.delay, self.next_frame)
        except _tkinter.TclError:
            pass


class VideoRecorder:
    """
    Class that handles the recording and streaming of video
    """

    def __init__(self, video_source, audio_source, video_path, audio_path, fps, label, size=(640, 360),
                 keep_ratio=True):
        """
        Streams, records, and handles webcam feeds
        :param video_source: tuple: Use VideoRecorder.get_video_sources() to get compatible sources
        :param audio_source: tuple: Use VideoRecorder.get_audio_sources() to get compatible sources
        :param video_path: path-like: Output save path of the recorded video
        :param audio_path: path-like: Output save path of the recorded audio
        :param fps: float or int: The recording frames per second
        :param label: Tk Label: The Label that will be used to display the video
        :param size: tuple: The height and width of the video on the Label
        :param keep_ratio: bool: If true, the aspect ratio is kept for the video
        """
        self.fps = fps
        self.frame_duration = float(1 / self.fps)
        self.label = label
        if video_path:
            self.video_output = os.path.join(pathlib.Path(video_path).parent,
                                             pathlib.Path(video_path).stem + "_raw" +
                                             pathlib.Path(video_path).suffix)
        else:
            self.video_output = None
        self.audio_output = audio_path
        self.video_source = video_source
        self.audio_source = audio_source
        self.thread = None
        self.recording = False
        self.playing = False
        self.cam = None
        self.cam_frame = None
        self.cam_thread_live = False
        self.mic = None
        self.mic_data = []
        self.mic_thread_live = False
        self.writer = None
        self.current_frame = 0
        self.p = None
        if keep_ratio:
            self.aspect_ratio = float(self.video_source[1][1]) / float(self.video_source[1][0])
            self.size = (size[0], int(size[0] / self.aspect_ratio))
        else:
            self.size = size

    @staticmethod
    def get_audio_sources():
        """
        Polls the audio sources and gets their description
        :return: tuple: First value is the output index, second value is the description
        """
        sources = []
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')

        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                sources.append((i, p.get_device_info_by_host_api_device_index(0, i).get('name')))
        return sources

    @staticmethod
    def get_video_sources():
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

    def __save_audio_file(self, filename):
        """
        Saves the recorded audio to the specified filename
        :param filename: path-like: Full filepath including filename for output file
        :return: None
        """
        wf = wave.open(filename, "wb")
        # set the channels
        wf.setnchannels(self.mic_channels)
        # set the sample format
        wf.setsampwidth(self.p.get_sample_size(self.audio_format))
        # set the sample rate
        wf.setframerate(self.mic_sample_rate)
        # write the frames as bytes
        wf.writeframes(b"".join(self.mic_data))
        # close the file
        wf.close()

    def __get_mic_recorder(self, source, chunk=1024, audio_format=pyaudio.paInt16, channels=1, sample_rate=44100):
        """
        Gets a microphone recording instance from a specified source
        :param source: tuple: Selected source from get_audio_sources
        :param chunk: int: The chunk size to get audio in
        :param audio_format: int: pyaudio format to save audio data in, default pyaudio.paInt16
        :param channels: int: Number of channels to record, default is one
        :param sample_rate: int: The sampling speed of the microphone, default is 44100 Hz
        :return: Microphone instance
        """
        self.mic_chunk = chunk
        self.audio_format = audio_format
        self.mic_channels = channels
        self.mic_sample_rate = sample_rate
        if not self.p:
            self.p = pyaudio.PyAudio()
        return self.p.open(format=audio_format,
                           channels=channels,
                           rate=sample_rate,
                           input_device_index=source,
                           input=True,
                           frames_per_buffer=chunk)

    def __close_mic_recorder(self):
        """
        Closes the microphone recording instance
        :return: None
        """
        if self.mic:
            self.mic.stop_stream()
            self.mic.close()
            self.p.terminate()

    def __audio_recording_thread(self):
        """
        Saves the input from an audio source to specified file
        :return: None
        """
        try:
            self.mic_thread_live = True
            self.mic_data = []
            while self.playing:
                try:
                    if self.recording:
                        self.mic_data.append(self.mic.read(self.mic_chunk))
                    else:
                        time.sleep(0.01)
                except Exception as e:
                    if self.recording:
                        print(
                            f"ERROR: Exception encountered in tkVideoUtils.VideoRecorder audio recording thread: {str(e)}")
            if self.mic_data:
                self.__save_audio_file(self.audio_output)
            self.__close_mic_recorder()
            self.mic_thread_live = False
        except Exception as e:
            print(f"ERROR: __audio_recording_thread exiting due to {str(e)}")
            return

    def __video_recording_thread(self):
        """
        Thread that plays and records video in the background.  Will only update the image on the Label is the Label
        is currently being viewed.
        :return: None
        """
        try:
            self.cam_thread_live = True
            while self.playing:
                try:
                    start_time = time.time()
                    self.cam_frame = self.cam.get_next_data()
                    if self.recording:
                        self.writer.append_data(self.cam_frame)
                    if self.recording:
                        process_time = time.time() - start_time
                    else:
                        process_time = 0
                    time.sleep((self.frame_duration - process_time) - time.monotonic() % self.frame_duration)
                except Exception as e:
                    if self.recording:
                        print(
                            f"ERROR: Exception encountered in tkVideoUtils.VideoRecorder video recording thread: {str(e)}")
            if self.writer:
                self.writer.close()
            self.cam.close()
            self.cam_thread_live = False
        except Exception as e:
            print(f"ERROR: __video_recording_thread exiting due to {str(e)}")
            return

    def __video_display_thread(self):
        """
        Thread that updates the video display label with the current frame
        :return: None
        """
        try:
            last_image = None
            while self.playing:
                try:
                    if self.cam_frame is not None:
                        if last_image is not None:
                            if (last_image == self.cam_frame).all():
                                continue
                        if self.label.winfo_viewable():
                            frame_image = ImageTk.PhotoImage(Image.fromarray(self.cam_frame).resize(self.size))
                            self.label.config(image=frame_image)
                            self.label.image = frame_image
                        last_image = self.cam_frame
                except Exception as e:
                    if self.recording:
                        print(
                            f"ERROR: Exception encountered in tkVideoUtils.VideoRecorder video recording thread: {str(e)}")
        except Exception as e:
            print(f"ERROR: __video_display_thread exiting due to {str(e)}")
            return

    def merge_sources(self, output, ffmpeg_path, overwrite='-y', delete_file=True):
        """
        Uses FFMPEG to add an audio source to an MP4 file
        :param delete_file: bool: If true, the raw audio and video files are deleted
        :param output: path-like: Full filepath to output file including filename
        :param ffmpeg_path: path-like: Full filepath to FFMPEG instance to use
        :param overwrite: string: -y to overwrite (default) or -n to not overwrite
        :return: bool: True if successful, False if unsuccessful
        """
        while self.mic_thread_live or self.cam_thread_live:
            time.sleep(0.01)
        try:
            ff = ffmpy.FFmpeg(
                executable=ffmpeg_path,
                inputs={self.video_output: None, self.audio_output: None},
                outputs={output: f'-vcodec copy {overwrite} -shortest'}
            )
            ff.run()
            if delete_file:
                os.remove(self.video_output)
                os.remove(self.audio_output)
            return True
        except ffmpy.FFRuntimeError as ffre:
            print(f"ERROR: Exception encountered merging audio and video sources {str(ffre)}")
            return False
        except ffmpy.FFExecutableNotFoundError as ffenfe:
            print(f"ERROR: FFmpeg executable not found!")
            return False
        except Exception as e:
            print(f"ERROR: Exception encountered with merging sources {str(e)}")
            return False

    def start_recording(self, video_output=None, audio_output=None):
        """
        Start webcam recording, if an output path is provided then the original output path is overwritten.
        :param video_output: path-like: Desired absolute filepath for the recorded video
        :param audio_output: path-like: Desired absolute filepath for the recorded audio
        :return: None
        """
        if video_output:
            self.video_output = os.path.join(pathlib.Path(video_output).parent,
                                             pathlib.Path(video_output).stem + "_raw" +
                                             pathlib.Path(video_output).suffix)
            self.writer = imageio.get_writer(self.video_output, fps=self.fps)
        else:
            self.writer = imageio.get_writer(self.video_output, fps=self.fps)
        if audio_output:
            self.audio_output = audio_output
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
        self.cam = imageio.get_reader(f'<video{self.video_source[0]}>', fps=self.fps)
        self.mic = self.__get_mic_recorder(self.audio_source[0])
        self.video_thread = threading.Thread(target=self.__video_recording_thread)
        self.video_thread.daemon = 1
        self.video_thread.start()
        self.audio_thread = threading.Thread(target=self.__audio_recording_thread)
        self.audio_thread.daemon = 1
        self.audio_thread.start()
        self.view_thread = threading.Thread(target=self.__video_display_thread)
        self.view_thread.daemon = 1
        self.view_thread.start()


class VideoPlayer:
    """
    Class that handles the streaming of a video file from the filesystem to a Label.
    """

    def __init__(self, root, video_path, audio_path, label, loading_gif, size=(640, 360), play_button=None,
                 play_image=None, pause_image=None, slider=None, slider_var=None, keep_ratio=False, skip_size_s=1,
                 override_slider=False, cleanup_audio=False):
        """
        Streams a video on the filesystem to a tkinter Label.
        :param video_path: path-like: Absolute path to the video file to be streamed
        :param audio_path: path-like: Absolute path to the audio file to be streamed
        :param label: Tk Label: The Label that will stream the video
        :param loading_gif: path-like: The gif to be used for the loading animation
        :param size: tuple: The size of the video on the Tk Label.
        :param play_button: Tk Button: Pass in a Button that will be wired up to control the play/pause of the video
        :param play_image: PhotoImage: The image that will be on the play_button if the video is paused
        :param pause_image: PhotoImage: The image that will be on the play_button if the video is playing
        :param slider: Tk Slider: Pass in a Slider that will be wired up to control the loaded frame
        :param slider_var: Tk IntVar: Control variable that can be used to monitor the frame index
        :param keep_ratio: bool: If True, the source aspect ratio will be kept
        :param skip_size_s: int: The number of seconds the video should skip when skipped forward or backward
        :param override_slider: bool: Set to true if you want to configure an external callback for the Slider
        :param cleanup_audio: bool: Set to have separated audio track deleted after it's been loaded
        """
        self.root = root
        self.setup_streams(video_path, audio_path, label, loading_gif, size, play_button, play_image,
                           pause_image, slider, slider_var, keep_ratio, skip_size_s,
                           override_slider, cleanup_audio)

    def setup_streams(self, video_path, audio_path, label, loading_gif, size=(640, 360), play_button=None, play_image=None,
                      pause_image=None, slider=None, slider_var=None, keep_ratio=False, skip_size_s=1,
                      override_slider=False, cleanup_audio=False):
        """
        Streams a video on the filesystem to a tkinter Label.
        :param video_path: path-like: Absolute path to the video file to be streamed
        :param audio_path: path-like: Absolute path to the audio file to be streamed
        :param label: Tk Label: The Label that will stream the video
        :param loading_gif: path-like: The gif to be used for the loading animation
        :param size: tuple: The size of the video on the Tk Label.
        :param play_button: Tk Button: Pass in a Button that will be wired up to control the play/pause of the video
        :param play_image: PhotoImage: The image that will be on the play_button if the video is paused
        :param pause_image: PhotoImage: The image that will be on the play_button if the video is playing
        :param slider: Tk Slider: Pass in a Slider that will be wired up to control the loaded frame
        :param slider_var: Tk IntVar: Control variable that can be used to monitor the frame index
        :param keep_ratio: bool: If True, the source aspect ratio will be kept
        :param skip_size_s: int: The number of seconds the video should skip when skipped forward or backward
        :param override_slider: bool: Set to true if you want to configure an external callback for the Slider
        :param cleanup_audio: bool: Set to have separated audio track deleted after it's been loaded
        """
        self.video_path = video_path
        self.audio_path = audio_path
        self.audio_index = 0
        self.play_audio = False
        self.audio_chunk = 1024
        self.cleanup_audio = False
        self.loading_gif = loading_gif
        if not os.path.exists(self.audio_path):
            temp_audioclip = AudioFileClip(self.video_path)
            if len(temp_audioclip.reader.buffer):
                self.audio_loaded = True
            else:
                self.audio_loaded = False
            temp_audioclip.close()
            self.cleanup_audio = cleanup_audio
        else:
            self.audio_loaded = True
        self.label = label
        self.playing = False
        self.skip_forward, self.skip_backward = False, False
        self.skip_size = skip_size_s
        temp = imageio.get_reader(self.video_path)
        self.raw_size = temp._get_data(0)[0].shape
        temp.close()
        meta_data = cv2.VideoCapture(self.video_path)
        self.fps = meta_data.get(cv2.CAP_PROP_FPS)
        self.frame_duration = float(1 / self.fps)
        self.nframes = int(meta_data.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        self.start_frame = None
        self.clip_frame = None
        if keep_ratio:
            self.aspect_ratio = float(self.raw_size[1]) / float(self.raw_size[0])
            self.size = (int(size[1] * self.aspect_ratio), size[1])
        else:
            self.size = size

        new_slider = False
        if slider:
            self.slider = slider
            new_slider = True
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
                if new_slider:
                    self.trough_img = tk.PhotoImage(width=size[0], height=10, master=self.root)
                    style_name = self.__create_slider_style()
                    self.slider.configure(style=style_name)
                self.set_img_color(self.trough_img, ['white', 'red'], [size[0], 0])
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
        meta_data.release()

        self.load_video_thread_live = False
        self.video_thread_live = False
        self.audio_thread_live = False
        self.frames = []
        self.loading = False
        self.load_frame_index = 0
        self.load_thread = threading.Thread(target=self.__load_video)
        self.load_thread.daemon = True
        self.load_thread.start()
        if self.audio_loaded:
            self.audio_load_thread = threading.Thread(target=self.__load_audio_thread)
            self.audio_load_thread.daemon = True
            self.audio_load_thread.start()

    def start_stream(self):
        """
        Creates a new pyaudio instance and opens a new output stream
        :return: None
        """
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.p.get_format_from_width(self.audio_file.getsampwidth()),
            channels=self.audio_file.getnchannels(),
            rate=self.audio_file.getframerate(),
            frames_per_buffer=256,
            output=True
        )

    def stop_stream(self):
        """
        Terminates the pyaudio instance and closes the output stream, starts up a new stream
        :return: None
        """
        self.stream.close()
        self.p.terminate()
        self.start_stream()

    @staticmethod
    def get_wav_attr(audio_file):
        """
        Retrieves a dict of values for a wav file
        :param audio_file: file-like: Open wav file
        :return: dict: Dictionary of values
        """
        return {"nchannels": audio_file.getnchannels(),
                "sampwidth": audio_file.getsampwidth(),
                "framerate": audio_file.getframerate(),
                "nframes": audio_file.getnframes(),
                "params": audio_file.getparams()}

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
        """
        Creates the style for the slider
        :return: string: Name of style
        """
        try:
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
        except _tkinter.TclError:
            print("INFO: Style already exists!")
            try:
                self.style.element_create('Horizontal.Scale.trough', 'image', self.trough_img)
            except _tkinter.TclError:
                return 'custom.Horizontal.TScale'
            return 'custom.Horizontal.TScale'
        return 'custom.Horizontal.TScale'

    def __load_video(self):
        """
        Background thread to load in frames to prevent issues when playing
        :return: None
        """
        try:
            self.loading = True
            self.load_video_thread_live = True
            self.load_frame_index = 0
            last_image = None
            size = self.size
            frame_data = imageio.get_reader(self.video_path)
            for image in frame_data.iter_data():
                if not self.loading:
                    self.load_video_thread_live = False
                    return
                if image is not None:
                    try:
                        if last_image is not None:
                            if (last_image == image).all():
                                continue
                        resized_image = ImageTk.PhotoImage(Image.fromarray(image).resize(size))
                        self.frames.append(resized_image)
                        self.load_frame_index += 1
                        last_image = image
                        if not self.audio_loaded:
                            if self.load_frame_index == 1:
                                self.load_frame(1)
                        if self.load_frame_index % 10:
                            if self.slider:
                                if type(self.slider) == TickScale and self.loading:
                                    self.__update_loading_slider()
                                else:
                                    self.load_video_thread_live = False
                                    return
                    except IndexError as e:
                        self.load_video_thread_live = False
                        return
                    except Exception as e:
                        self.load_video_thread_live = False
                        return
            self.load_video_thread_live = False
            self.__clear_loading_slider()
        except Exception as e:
            print(f"ERROR: __load_video exiting due to {str(e)}")
            return

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
            try:
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
            except IndexError:
                frame_image = self.frames[self.load_frame_index - 1]
                if frame_image:
                    self.label.config(image=frame_image)
                    self.label.image = frame_image
                    self.current_frame = self.load_frame_index - 1
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
        if self.play_audio:
            self.play_audio = False
        while self.audio_thread_live or self.video_thread_live:
            time.sleep(0.001)

    def skip_video_forward(self):
        """
        Skips the video feed forward by either telling the Thread to do it, or by changing the current frame and loading
        the frame.
        :return: None
        """
        if self.playing:
            return
            # self.skip_forward = True
        else:
            new_frame = self.current_frame + int(self.skip_size * self.fps)
            if new_frame > (self.load_frame_index - 1):
                new_frame = self.load_frame_index - 1
            self.load_frame(new_frame)

    def skip_video_backward(self):
        """
        Skips the video feed backward by either telling the Thread to do it, or by changing the current frame and loading
        the frame.
        :return: None
        """
        if self.playing:
            return
            # self.skip_backward = True
        else:
            new_frame = (self.current_frame - int(self.skip_size * self.fps))
            if new_frame < 1:
                new_frame = 1
            self.load_frame(new_frame)

    def set_clip(self, start_frame, end_frame):
        """
        Sets the start and end frame for a clip, when video is played it will start and stop at these frames.
        :param start_frame: int: Starting frame for clip
        :param end_frame: int: Ending frame for clip
        :return: None
        """
        self.start_frame = start_frame
        self.clip_frame = end_frame

    def clear_clip(self):
        """
        Clears the clip setting
        :return: None
        """
        self.start_frame = None
        self.clip_frame = None

    def __load_audio_thread(self):
        """
        Loads in wav file for usage in audio playback thread, closes audio file once completed
        :return: None
        """
        try:
            loading_gif = ImageLabel(self.loading_gif, self.label, (self.size[1], self.size[1]))
            temp_audioclip = AudioFileClip(self.video_path)
            temp_audioclip.write_audiofile(self.audio_path, codec='pcm_s16le', verbose=False, logger=None)
            loading_gif.unload()
            self.load_frame(1)
            self.audio_file = wave.open(self.audio_path, 'rb')
            self.start_stream()
            self.stream_attr = self.get_wav_attr(self.audio_file)
            self.audio_data = [None] * int(self.stream_attr["nframes"] / self.audio_chunk)
            self.audio_loading = True
            self.audio_data = []
            while True:
                if self.audio_loading:
                    data = self.audio_file.readframes(self.audio_chunk)
                    if data != b'':
                        self.audio_data.append(data)
                    else:
                        break
                else:
                    break
            self.audio_file.close()
            self.audio_loading = False
            if self.cleanup_audio:
                os.remove(self.audio_path)
        except Exception as e:
            print(f"ERROR: __load_audio_thread exiting due to {str(e)}")
            return

    def __audio_thread(self):
        """
        Writes the current audio_index to the output stream
        :return: None
        """
        try:
            self.audio_thread_live = True
            try:
                while (self.audio_index < len(self.audio_data) - 1) and self.playing:
                    if self.play_audio:
                        if self.playing:
                            self.stream.write(self.audio_data[self.audio_index])
                            self.audio_index += 1
                        else:
                            break
                    else:
                        time.sleep(0.001)
                self.play_audio = False
                self.stop_stream()
                self.audio_thread_live = False
            except Exception as e:
                print(str(e), traceback.print_exc())
        except Exception as e:
            print(f"ERROR: __audio_thread exiting due to {str(e)}")
            return

    def __update_audio_index(self):
        """
        Updates the index to play from the audio stream based off of the current frame
        :return: None
        """
        if self.audio_loaded:
            self.audio_index = int((len(self.audio_data) * self.current_frame) / self.nframes)

    def __playing_thread(self):
        """
        Thread that will stream the video file to a Label at the source frame rate.
        :return: None
        """
        try:
            self.video_thread_live = True
            n = self.nframes
            i = int(self.current_frame)
            self.playing = True
            self.__update_audio_index()
            self.play_audio = True
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
                        if self.start_frame is not None and self.clip_frame is not None:
                            if not (self.start_frame <= i < self.clip_frame):
                                break
                        if self.skip_forward:
                            i += int(self.skip_size * self.fps)
                            self.skip_forward = False
                        elif self.skip_backward:
                            i -= int(self.skip_size * self.fps)
                            self.skip_backward = False
                        else:
                            i += 1
                        time.sleep(self.frame_duration - time.monotonic() % self.frame_duration)
                    else:
                        i = self.load_frame_index - 1
                except StopIteration as e:
                    print(str(e))
                    break
                except IndexError as e:
                    print(str(e))
                    self.playing = False
                    if n == float("inf"):
                        break
                    raise
            self.video_thread_live = False
            time.sleep(0.01)
            self.playing = False
            self.play_audio = False
            if self.current_frame > self.nframes:
                self.current_frame = self.nframes
            if self.play_button:
                self.play_button.config(image=self.play_image)
        except Exception as e:
            print(f"ERROR: __playing_thread exiting due to {str(e)}")
            return

    def play(self):
        """
        Creates a thread that plays the video frames onto the Label at the source FPS.
        :return: None
        """
        self.playing = True
        if self.current_frame == self.nframes - 1:
            self.current_frame = 0
        if self.start_frame is not None:
            self.current_frame = self.start_frame
        video_thread = threading.Thread(target=self.__playing_thread)
        video_thread.daemon = True
        video_thread.start()
        if self.audio_loaded:
            audio_thread = threading.Thread(target=self.__audio_thread)
            audio_thread.daemon = True
            audio_thread.start()

    def close(self):
        """
        Cleans up resources and sets flags to end running threads.
        :return: None
        """
        self.loading = False
        self.playing = False
        self.audio_loading = False


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
