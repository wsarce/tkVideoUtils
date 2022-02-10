
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

tkVideoUtils is a Python module for playing and recording videos in GUIs created with tkinter.


### Built With

* [tkinter (Python built-in)](https://docs.python.org/3/library/tkinter.html)
* [imageio](https://imageio.github.io)
* [Pillow](https://pypi.org/project/Pillow/)


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
## Usage

* Import tkinter and tkvideo
* Create `Tk()` parent and the label you'd like to use
* Create `tkvideo` object with its parameters (video file path, label name, whether to loop the video or not and size of the video)
* Start the player thread with `<player_name>.play()`
* Start the Tk main loop

Example code:

```py
from tkinter import *
from tkvideoutils import tkvideoplayer
from tkinter import filedialog, messagebox

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
video_path = filedialog.askopenfilename()
slider_var = IntVar(root)
slider = Scale(root, orient=HORIZONTAL, variable=slider_var)
# place elements
video_label.pack()
button.pack()
slider.pack()

if video_path:
    # read video to display on label
    player = tkvideoplayer(video_path, video_label,
                           loop=False, size=(700, 500),
                           play_button=button, play_image=play_image, pause_image=pause_image,
                           slider=slider, slider_var=slider_var)
else:
    messagebox.showwarning("Select Video File", "Please retry and select a video file.")
    sys.exit(1)
root.mainloop()
```

## Issues / suggestions

Have a problem that needs to be solved or a suggestion to make? See the [issues](https://github.com/wsarce/tkVideoUtils/issues) page.


## License

Distributed under the MIT License. See `LICENSE` for more information.



## Contact

Walker Arce - wsarcera@gmail.com
Project Link: [https://github.com/wsarce/tkVideoUtils](https://github.com/wsarce/tkVideoUtils)
