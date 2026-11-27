import sys
import os

sys.path.append(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../src"))
from python.core import run_checker, check_program, filter_warns  # noqa
from python.dump import DumpManager  # noqa


def test_initialization_literal():
    f = 'st/declaration-analysis.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    assert len(checker_warnings) == 3
    cv = checker_warnings[0]
    assert cv.id == 'OutOfBounds'
    # assert cv.linenr == 8
    # assert cv.column == 31
    with DumpManager(fdump):
        pass


def test_array_initialized_list():
    fdump = f'stdin.dump.json'
    warns, rc = check_program(
        """
        TYPE BITS: ARRAY [1..2, 1..3] OF BOOL := [0,0,0,0,0,0,1,1,1]; END_TYPE
        PROGRAM test_p
          VAR
            ARR1: ARRAY [1..2, 1..3] OF BOOL := [0,0,0,0,0,0,1,1,1];
          END_VAR
          ARR1[1] := 19;
        END_PROGRAM
        """.replace('\n', ''))
    assert rc == 0
    assert len(warns) >= 2
    oob_warns = filter_warns(warns, 'OutOfBounds')
    assert len(oob_warns) == 2
    for w in oob_warns:
        assert w.id == 'OutOfBounds'
        assert '3 values will be lost' in w.msg
    with DumpManager(fdump) as dm:
        scheme = dm.scheme
        assert scheme
        assert len(scheme.types) == 1


def test_subrange_var_initial_value():
    warns, rc = check_program(
        """
        PROGRAM p
          VAR
            ok : INT (0..10) := 10;
            lo : INT (0..10) := -1;
            hi : INT (0..10) := 11;
          END_VAR
          ok := lo + hi;
        END_PROGRAM
        """.replace('\n', ''))
    msgs = sorted(w.msg for w in filter_warns(warns, 'OutOfBounds'))
    assert msgs == [
        'Initial subrange value -1 does not fit the specified range (0 .. 10)',
        'Initial subrange value 11 does not fit the specified range (0 .. 10)',
    ], msgs
    assert not filter_warns(warns, 'ParserError')
    with DumpManager('stdin.dump.json'):
        pass


def test_string_initializer_length_counts_escapes_as_one(tmp_path):
    """`$$`, `$N`, `$'`, `$hh` and `$hhhh` are one character each (B.1.2.2), and so is a UTF-8 sequence."""
    f = tmp_path / 'escapes.st'
    f.write_bytes(
        'PROGRAM p\n'
        'VAR\n'
        "  a : STRING[2] := ',$20';\n"
        "  b : STRING[1] := '$$';\n"
        "  c : STRING[2] := '$N$t';\n"
        "  d : STRING[1] := '$'';\n"
        '  e : WSTRING[1] := "$0041";\n'
        '  g : WSTRING[2] := "äö";\n'
        "  h : STRING[2] := '$$$$x';\n"
        "  i : STRING[2] := '$41$42$43';\n"
        '  j : WSTRING[1] := "$0041$0042";\n'
        "  k : STRING[3] := '$4142';\n"
        'END_VAR\n'
        'a := b;\n'
        'END_PROGRAM\n'.encode())
    warns, rc = run_checker([str(f)])
    assert rc == 0
    got = sorted((w.linenr, w.msg.split('(')[1]) for w in filter_warns(warns, 'OutOfBounds'))
    assert got == [(9, '3 > 2)'), (10, '3 > 2)'), (11, '2 > 1)')], got
