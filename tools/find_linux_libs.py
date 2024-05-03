#!/usr/bin/env python3

# Create JSON with Linux libs needed for BeeRef appimage

import argparse
import json
import logging
import os
import pathlib
import re
import subprocess
import sys
from urllib import request


parser = argparse.ArgumentParser(
    description=('Create JSON with Linux libs needed for BeeRef appimage'))
parser.add_argument(
    'pid',
    nargs=1,
    default=None,
    help='PID of running BeeRef process')
parser.add_argument(
    '-l', '--loglevel',
    default='INFO',
    choices=list(logging._nameToLevel.keys()),
    help='log level for console output')
parser.add_argument(
    '--jsonfile',
    default='linux_libs.json',
    help='JSON input/output file')
parser.add_argument(
    '--check-appimage',
    default=False,
    action='store_true',
    help='Check a running appimage process for missing libraries')


args = parser.parse_args()


def strip_minor_versions(path):
    # foo2.so.2.1.1 -> foo2.so.2
    return re.sub('(.so.[0-9]*)[.0-9]*$', r'\1', path)


def what_links_to(path):
    links = set()
    dirname = os.path.dirname(path)
    for filename in os.listdir(dirname):
        filename = os.path.join(dirname, filename)
        if (os.path.islink(filename)
                and str(pathlib.Path(filename).resolve()) == path):
            links.add(filename)
    return sorted(links, key=len)


def is_lib(path):
    return ('.so' in path
            and os.path.expanduser('~') not in path
            and 'python3' not in path
            and 'mesa-diverted' not in path)


def iter_lsofoutput(output):
    for line in output.splitlines():
        line = line.split()
        if line[3] == 'mem':
            path = line[-1]
            if is_lib(path):
                yield path


PID = args.pid[0]
logger = logging.getLogger(__name__)
logging.basicConfig(level=getattr(logging, args.loglevel))


result = subprocess.run(('lsof', '-p', PID), capture_output=True)
assert result.returncode == 0, result.stderr
output = result.stdout.decode('utf-8')


if args.check_appimage:
    logger.info('Checking appimage...')
    errors = False
    for lib in iter_lsofoutput(output):
        if 'mount_BeeRef' not in lib:
            print(f'Not in appimage: {lib}')
            errors = True
    if not errors:
        print('No missing libs found.')
    sys.exit()


libs = []

if os.path.exists(args.jsonfile):
    logger.info(f'Reading from: {args.jsonfile}')
    with open(args.jsonfile, 'r') as f:
        data = json.loads(f.read())
    known_libs = data['libs']
    packages = set(data['packages'])
else:
    logger.info(f'No file {args.jsonfile}; starting from scratch')
    known_libs = []
    packages = set()


for lib in iter_lsofoutput(output):
    links = what_links_to(lib)
    if len(links) == 1:
        lib = links[0]
    else:
        logger.warning(f'Double check: {lib} {links}')
        lib = links[0]
    if lib in known_libs:
        logger.debug(f'Found known lib: {lib}')
    else:
        logger.debug(f'Found unknown lib: {lib}')
        libs.append(lib)


for lib in libs:
    result = subprocess.run(('apt-file', 'search', lib), capture_output=True)
    if result.returncode != 0:
        logger.warning(f'Fix manually: {lib}')
        continue
    output = result.stdout.decode('utf-8')
    pkgs = set()
    for line in output.splitlines():
        pkg = line.split(': ')[0]
        if not (pkg.endswith('-dev') or pkg.endswith('-dbg')):
            pkgs.add(pkg)
    if len(pkgs) == 1:
        pkg = pkgs.pop()
        logger.debug(f'Found package: {pkg}')
        packages.add(pkg)
    else:
        logger.warning(f'Fix manually: {lib}')


# Find the libs we shouldn't include in the appimage
with request.urlopen(
        'https://raw.githubusercontent.com/AppImageCommunity/pkg2appimage/'
        'master/excludelist') as f:
    response = f.read().decode()


exclude_masterlist = set()
for line in response.splitlines():
    if not line or line.startswith('#'):
        continue
    line = line.split()[0]
    line = strip_minor_versions(line)
    exclude_masterlist.add(line)

excludes = []
for ex in exclude_masterlist:
    for lib in (libs + known_libs):
        if lib.endswith(ex):
            excludes.append(ex)
            continue


logger.info(f'Writing to: {args.jsonfile}')
with open(args.jsonfile, 'w') as f:
    data = {'libs': sorted(libs + known_libs),
            'packages': sorted(packages),
            'excludes': sorted(excludes)}
    f.write(json.dumps(data, indent=4))
