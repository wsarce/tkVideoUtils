
<p align="center">
  <p align="center">
    tkVideoUtils - Python module for playing videos and camera feeds in a Tkinter label, with recording functionality
    <br />
</p>

<p align = center>
	<a href="https://github.com/wsarce/tkVideoUtils/graphs/contributors">
		<img src="https://img.shields.io/github/contributors/wsarce/tkVideoUtils.svg?style=flat-square" alt="Contributors" />
	</a>
	<a href="https://github.com/wsarce/tkVideoUtils/network/members">
		<img src="https://img.shields.io/github/forks/wsarce/tkVideoUtils.svg?style=flat-square" alt="Forks" />
	</a>
	<a href="https://github.com/wsarce/tkVideoUtils/stargazers">
		<img src="https://img.shields.io/github/stars/wsarce/tkVideoUtils.svg?style=flat-squarem/huskeee/tkvideo/network/members" alt="Stargazers" />
	</a>
	<a href="https://github.com/wsarce/tkVideoUtils/issues">
		<img src="https://img.shields.io/github/issues/wsarce/tkVideoUtils.svg?style=flat-square" alt="Issues" />
	</a>
	<a href="https://github.com/wsarce/tkVideoUtils/blob/master/LICENSE">
		<img src="https://img.shields.io/github/license/wsarce/tkVideoUtils.svg?style=flat-square" alt="MIT License" />
	</a>
</p>





<!-- ABOUT THE PROJECT -->
## About The Project

tkVideoUtils is a Python module for playing and recording videos in GUIs created with tkinter.  Using imageio-ffmpeg, webcams can be indexed and streamed in a tkinter Label.  They can also be recorded (in their original resolution) by calling the `start_recording()` function!  This project was heavily inspired by [huskeee's tkvideo library](https://github.com/huskeee/tkvideo), check their project out!


### Built With

* [tkinter (Python built-in)](https://docs.python.org/3/library/tkinter.html)
* [imageio](https://imageio.github.io)
* [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)
* [Pillow](https://pypi.org/project/Pillow/)
* [opencv-python](https://pypi.org/project/opencv-python/)


## Installation

### End-users:

 * Clone the repo and run `setup.py`
```sh
git clone https://github.com/wsarce/tkVideoUtils.git
python ./tkvideo/setup.py
```
or
 * Install the package from PyPI
```sh
pip install tkVideoUtils
```

### Developers and contributors
 * Clone the repo and install the module in developer mode
```sh
git clone https://github.com/wsarce/tkVideoUtils.git
python ./tkvideo/setup.py develop
```
or
 * Install the package from PyPI in editable mode
```sh
pip install -e tkvideoplayer
```

This will create a shim between your code and the module binaries that gets updated every time you change your code.


<!-- USAGE EXAMPLES -->
# Playing a Video in a Label

```py
from tkinter import *
from tkvideoutils import VideoPlayer
from tkinter import filedialog, messagebox

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
    video_path = filedialog.askopenfilename()
    slider_var = IntVar(root)
    slider = Scale(root, orient=HORIZONTAL, variable=slider_var)
    # place elements
    video_label.pack()
    button.pack()
    forward_button.pack()
    backward_button.pack()
    slider.pack()

    if video_path:
        # read video to display on label
        player = VideoPlayer(video_path, video_label,
                             loop=False, size=(700, 500),
                             play_button=button, play_image=play_image, pause_image=pause_image,
                             slider=slider, slider_var=slider_var)
    else:
        messagebox.showwarning("Select Video File", "Please retry and select a video file.")
        sys.exit(1)
    forward_button.config(command=player.skip_video_forward)
    backward_button.config(command=player.skip_video_backward)
    root.mainloop()
```

# Playing and Recording a Webcam in a Label

```py
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

```

## Issues / suggestions

Have a problem that needs to be solved or a suggestion to make? See the [issues](https://github.com/wsarce/tkVideoUtils/issues) page.

## Notes on Freezing

If you want to freeze your Python scripts that reference tkVideoUtils, there are some general notes to keep in mind:
- Due to the use of ImageIO, the lazy import error causes frozen Python scripts to fail to start or fail to execute the imageio codepaths.  This can make it look like imageio-ffmpeg is failing with a backend issue.  To circumvent this, follow this [answer](https://stackoverflow.com/a/70214003).  This answer says to overwrite your imageio folder in your exe output directory with the imageio folder from your virtual environment (`venv\Lib\site-packages\imageio`).  I can verify that this works.
- I prefer copying the ffmpeg exe version that is packaged with imageio-ffmpeg into your exe directory in a known folder and updating `os.environ['IMAGEIO_FFMPEG_EXE']` with that directory.  This ensures a known path.

## License

Distributed under the MIT License. See `LICENSE` for more information.



## Contact

Walker Arce - wsarcera@gmail.com
Project Link: [https://github.com/wsarce/tkVideoUtils](https://github.com/wsarce/tkVideoUtils)
