"""Tests for internal errors."""
import sys
import os
import threading

sys.path.append(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../src"))
from python.core import run_checker, run_checker_full_out, check_program  # noqa
from python.dump import DumpManager  # noqa


def test_missing_file():
    f = 'st/foo.bar'
    checker_warnings, rc = run_checker([f])
    assert rc == 1
    assert len(checker_warnings) == 1
    cv = checker_warnings[0]
    assert cv.id == 'FileNotFoundError'


def test_large_file():
    """Make sure that there are no stack overflows on large programs."""
    fname = 'st/_TEMP_large.st'
    with open(fname, 'w') as f:
        f.write(f"""
        PROGRAM test_for
        VAR a : INT; i : INT; END_VAR
        FOR i := 0 TO 10 BY 2 DO
        """)
        for _ in range(1000):
            f.write('a := a + i;\n')
        f.write(f"""
        END_FOR;
        i := 0;
        END_PROGRAM
        """)
    checker_warnings, rc = run_checker([fname])
    os.remove(fname)


def test_large_output(tmp_path):
    """The checker's output may exceed the OS pipe buffer."""
    f = tmp_path / 'big.st'
    f.write_text('PROGRAM p @ (*' + 'x' * 2 ** 17 + '*)\nEND_PROGRAM\n')
    for run in (lambda: run_checker([str(f)]),
                lambda: run_checker_full_out([str(f)])):
        res = []
        t = threading.Thread(target=lambda: res.append(run()), daemon=True)
        t.start()
        t.join(timeout=30)
        assert not t.is_alive(), 'deadlocked on a full stdout pipe'
        assert len(str(res[0])) > 2 ** 16


def test_stdin_reads_whole_input():
    """`-` reads the program until the end of the input."""
    warns, rc = check_program('PROGRAM p\nVAR x : INT; END_VAR\nx := 1;\nEND_PROGRAM')
    assert not [w for w in warns if w.id in ('ParserError', 'LexingError')], warns
    assert rc == 0
    warns, rc = check_program('PROGRAM p VAR x : INT; END_VAR x := 1;\nEND_PROGRAM\n@@@')
    e = [w for w in warns if w.id in ('ParserError', 'LexingError')]
    assert rc == 1 and len(e) == 1 and (e[0].id, e[0].linenr) == ('LexingError', 3), warns
    with DumpManager('stdin.dump.json'):
        pass
