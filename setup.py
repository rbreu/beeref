from setuptools import setup

setup(
    name='BeeRef',
    version='0.3.3',
    author='Rebecca Breu',
    author_email='rebecca@rbreu.de',
    url='https://github.com/rbreu/beeref',
    license='LICENSE',
    description='A simple reference image viewer',
    install_requires=[
        'pyQt6>=6.5.0,<=6.6.1',
        'pyQt6-Qt6>=6.5.0,<=6.6.1',
        'rectangle-packer>=2.0.1,<=2.0.2',
        'exif>=1.3.5,<=1.6.0',
        'lxml==5.1.0'
    ],
    packages=[
        'beeref',
        'beeref.actions',
        'beeref.assets',
        'beeref.config',
        'beeref.documentation',
        'beeref.fileio',
        'beeref.widgets',
        'beeref.widgets.controls',
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
