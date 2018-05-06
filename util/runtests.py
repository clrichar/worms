#!/usr/bin/env python

import sys
import os


def dispatch(file, pytest_args='--duration=5'):
    dispatch = {
        'segments.py': ['tests/test_segments.py', 'tests/test_search.py'],
        'database.py': ['tests/test_database.py'],
        'pose_contortions.py': [
            'tests/test_pose_contortions.py', 'tests/test_segments.py',
            'tests/test_search.py'
        ],
    }
    path, bname = os.path.split(file)
    if (not file.endswith('.py')
            or not os.path.relpath(file).startswith('worms/')):
        return 'pytest {pytest_args}'.format(**vars())
    if not os.path.basename(file).startswith("test_"):
        if bname in dispatch:
            return ('pytest {pytest_args} '.format(**vars()) + ' '.join(
                (os.path.join(path, n) for n in dispatch[bname])))
        else:
            file = path + "/tests/test_" + bname
            if os.path.exists(file):
                return 'pytest {pytest_args} {file}'.format(**vars())
            else:
                return 'python ' + file
    return 'pytest {pytest_args} {file}'.format(**vars())


if len(sys.argv) != 2:
    cmd = 'pytest ' + pytest_args
elif sys.argv[1].endswith(__file__):
    cmd = 'pytest DUMMY_DEBUGGING_runtests.py'
else:
    cmd = dispatch(sys.argv[1])

print('cwd:', os.getcwd())
print('cmd:', cmd)
print('=' * 20, 'util/runtests.py running cmd in cwd', '=' * 23)
sys.stdout.flush()
os.system(cmd)
print('=' * 20, 'util/runtests.py done', '=' * 37)
