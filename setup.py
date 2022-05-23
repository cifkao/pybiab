import setuptools
import sys

setuptools.setup(
    name='pybiab',
    author='Ondřej Cífka',
    author_email='cifkao@gmail.com',
    description='Band-in-a-Box/RealBand automation',
    url='https://github.com/cifkao/pybiab',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    python_requires='>=3.5',
    install_requires=[
        'pywinauto',
        'pywin32',
        'psutil',
        'mido',
    ],
)
