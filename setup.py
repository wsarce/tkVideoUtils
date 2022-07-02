from setuptools import setup

with open('README.md') as f:
    readme = f.read()

setup(name='tkVideoUtils',
      version='1.0.3',
      description='Python module for playing and recording videos with sound inside tkinter Label widget '
                  'using Pillow, imageio, and PyAudio, including media playback control, slider, '
                  'and fps aware buffering.',
      long_description=readme,
      long_description_content_type="text/markdown",
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.8',
          'Topic :: Multimedia :: Video :: Display'
      ],
      keywords='tkVideoUtils tkinter video webcam display label pillow imageio wsarce',
      url='https://github.com/wsarce/tkVideoUtils',
      author='Walker Arce (wsarce)',
      author_email='wsarcera@gmail.com',
      license='MIT',
      packages=['tkvideoutils'],
      install_requires=[
          'imageio',
          'imageio-ffmpeg',
          'pillow',
          'opencv-python',
          'ttkwidgets',
          'pyaudio',
          'ffmpy',
          'moviepy'
      ],
      include_package_data=True,
      zip_safe=False
      )
