from setuptools import setup

with open('README.md') as f:
    readme = f.read()

setup(name='tkVideoPlayer',
      version='0.2.8',
      description='Python module for playing videos (without sound) inside tkinter Label widget using Pillow and '
                  'imageio, including media playback control, slider, and fps aware buffering.  Derivative of tkVideo'
                  'by huskeee',
      long_description=readme,
      long_description_content_type="text/markdown",
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.8',
          'Topic :: Multimedia :: Video :: Display'
      ],
      keywords='tkvideplayer tkinter video display labeli pillow imageio huskeee wsarce',
      url='https://github.com/wsarce/tkvideo',
      author='Walker Arce (wsarce)',
      author_email='wsarcera@gmail.com',
      license='MIT',
      packages=['tkvideoplayer'],
      install_requires=[
          'imageio',
          'imageio-ffmpeg',
          'pillow'
      ],
      include_package_data=True,
      zip_safe=False
      )
