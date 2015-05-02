from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='truce',
    version='0.2.1',
    description='An experimental text editor and/or shell',
    long_description=long_description,
    url='https://github.com/jangler/truce-py',
    author='Brandon Mulcahy',
    author_email='brandon@jangler.info',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Topic :: System :: Shells',
        'Topic :: Text Editors',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Operating System :: OS Independent',
    ],
    keywords=['truce', 'text', 'editor', 'shell', 'tkinter'],
    packages=find_packages(),
    entry_points={
        'gui_scripts': ['truce=truce.app:main']
    }
)
