from setuptools import setup

setup(
    name='BeeRef',
    version='0.3.0',
    author='Rebecca Breu',
    author_email='rebecca@rbreu.de',
    url='https://github.com/rbreu/beeref',
    license='LICENSE',
    description='A simple reference image viewer',
    install_requires=[
        'pyQt6>=6.2.0',
        'pyQt6-Qt6>=6.2.0',
        'rectangle-packer>=2.0.1',
        'exif',
    ],
    packages=[
        'beeref',
        'beeref.actions',
        'beeref.assets',
        'beeref.documentation',
        'beeref.fileio',
    ],
    entry_points={
        'gui_scripts': [
            'beeref = beeref.__main__:main'
        ]
    },
    include_package_data=True,
    package_data={
        'beeref.assets': ['*.png'],
        'beeref': ['documentation/*.html'],
    },
)
