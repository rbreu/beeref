"""Build release files."""


from distutils.sysconfig import get_python_lib
import os.path
import shutil
import sys


import PyInstaller.__main__

from beeref import constants


def datapath(src, dest):
    return os.path.join(*src) + os.pathsep + os.path.join(*dest)


import os; print(sorted(os.listdir(get_python_lib())))
pyqt_dir = os.path.join(get_python_lib(), 'PyQt6', 'Qt6')
appname = f'{constants.APPNAME}-{constants.VERSION}'

PyInstaller.__main__.run([
    '--noconfirm',
    '--onedir',
    '--windowed',
    '--name', appname,
    '--hidden-import', 'PyQt6.sip',
    '--hidden-import', 'PyQt6.QtPrintSupport',
    '--icon', os.path.join('beeref', 'assets', 'logo.png'),
    '--paths', os.path.join(pyqt_dir, 'bin'),
    '--add-data', datapath(
        [pyqt_dir, 'plugins', 'platforms'], ['platforms']),
    '--add-data', datapath([pyqt_dir, 'lib'], ['.']),
    '--add-data', datapath(
        ['beeref', 'documentation'], ['beeref', 'documentation']),
    '--add-data', datapath(
        ['beeref', 'assets', '*.png'], ['beeref', 'assets']),
    'beeref/__main__.py'
])

outfilename = os.path.join('dist', f'{appname}-{sys.platform}')
print(f'Zipping output to {outfilename}.zip')
shutil.make_archive(
    outfilename,
    'zip',
    root_dir='dist',
    base_dir=appname)

print('Done')
