import sys
import os

sys.path.append(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../src"))
from python.core import run_checker, filter_warns  # noqa
from python.dump import DumpManager  # noqa


def test_uncalled_instance():
    f = 'st/uncalled-instance.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f])
    assert rc == 0
    got = sorted((w.linenr, w.column, w.msg.split()[3]) for w in filter_warns(warns, 'UncalledInstance'))
    assert got == [(21, 3, 'LATCH'), (22, 3, 'MINE')], got
    with DumpManager(fdump):
        pass
