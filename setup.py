from setuptools import setup

with open('README.md') as f:
    readme = f.read()

setup(name='tkVideoUtils',
      version='0.4.22',
      description='Python module for playing and recording videos (without sound) inside tkinter Label widget '
                  'using Pillow and imageio, including media playback control, slider, and fps aware buffering.',
      long_description=readme,
      long_description_content_type="text/markdown",
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.8',
          'Topic :: Multimedia :: Video :: Display'
      ],
      keywords='tkVideoUtils tkinter video webcam display label pillow imageio wsarce',
      url='https://github.com/wsarce/tkvideo',
      author='Walker Arce (wsarce)',
      author_email='wsarcera@gmail.com',
      license='MIT',
      packages=['tkvideoutils'],
      install_requires=[
          'imageio',
          'imageio-ffmpeg',
          'pillow',
          'opencv-python'
      ],
      include_package_data=True,
      zip_safe=False
      )
