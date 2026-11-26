"""Tests for PLCOpen inspections."""
import sys
import os
from collections import Counter

sys.path.append(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../src"))
from python.core import run_checker, check_program, filter_warns  # noqa
from python.dump import DumpManager  # noqa


def test_cp1():
    f = 'st/plcopen-cp1.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    checker_warnings.count('PLCOPEN-CP1') == 1
    with DumpManager(fdump):
        pass


def test_cp3():
    f = 'st/plcopen-cp3.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    checker_warnings.count('PLCOPEN-CP3') == 8
    with DumpManager(fdump):
        pass


def test_cp6():
    f = 'st/plcopen-cp6.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    checker_warnings.count('PLCOPEN-CP6') == 2
    with DumpManager(fdump):
        pass


def test_cp8():
    f = 'st/plcopen-cp8.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    checker_warnings.count('PLCOPEN-CP8') == 4
    with DumpManager(fdump):
        pass


def test_cp28():
    f = 'st/plcopen-cp28.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    checker_warnings.count('PLCOPEN-CP28') == 4
    with DumpManager(fdump):
        pass


def test_cp13():
    f = 'st/plcopen-cp13.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    checker_warnings.count('PLCOPEN-CP13') == 3
    with DumpManager(fdump):
        pass


def test_cp25():
    f = 'st/plcopen-cp25.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    checker_warnings.count('PLCOPEN-CP25') == 2
    with DumpManager(fdump):
        pass


def test_l10():
    f = 'st/plcopen-l10.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    checker_warnings.count('PLCOPEN-L10') == 3
    with DumpManager(fdump):
        pass


def test_l17():
    f = 'st/plcopen-l17.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    l17_warns = filter_warns(checker_warnings, 'PLCOPEN-L17')
    assert any(w.linenr == 10 and w.column == 4 for w in l17_warns)
    with DumpManager(fdump):
        pass


def test_cp16():
    f = 'st/plcopen-cp16.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f])
    assert rc == 0
    cp16_warns = filter_warns(warns, 'PLCOPEN-CP16')
    assert len(cp16_warns) == 1
    with DumpManager(fdump):
        pass


def test_cp17():
    f = 'st/plcopen-cp17.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f])
    assert rc == 0
    cp17_warns = filter_warns(warns, 'PLCOPEN-CP17')
    expected = Counter([
        (4, 21), (5, 25), (5, 25), (6, 25), (8, 17), (9, 26), (9, 26),
        (10, 23), (12, 22), (12, 22), (17, 22), (18, 25), (25, 21),
    ])
    actual = Counter((w.linenr, w.column) for w in cp17_warns)
    assert actual == expected
    with DumpManager(fdump):
        pass


def test_cp26():
    f = 'st/plcopen-cp26.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f])
    assert rc == 0
    cp26_warns = filter_warns(warns, 'PLCOPEN-CP26')
    assert len(cp26_warns) == 2
    with DumpManager(fdump):
        pass


def test_l13():
    f = 'st/plcopen-l13.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f])
    assert rc == 0
    l13_warns = filter_warns(warns, 'PLCOPEN-L13')
    assert len(l13_warns) == 3
    with DumpManager(fdump):
        pass


def test_l22():
    f = 'st/plcopen-l22.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f])
    assert rc == 0
    l22_warns = filter_warns(warns, 'PLCOPEN-L22')
    assert len(l22_warns) == 3
    with DumpManager(fdump):
        pass


def test_n3():
    f = 'st/plcopen-n3.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    n3_warns = filter_warns(checker_warnings, 'PLCOPEN-N3')
    assert any(w.linenr == 6 and w.column == 7 for w in n3_warns)
    with DumpManager(fdump):
        pass


def test_cp9():
    f = 'st/plcopen-cp9.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f])
    assert rc == 0
    assert len(filter_warns(warns, 'PLCOPEN-CP9')) == 2
    with DumpManager(fdump):
        pass


def test_n1():
    f = 'st/plcopen-n1.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f])
    assert rc == 0
    assert len(filter_warns(warns, 'PLCOPEN-N1')) == 1
    with DumpManager(fdump):
        pass


def test_n2():
    f = 'st/plcopen-n2.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f], args=['-c', 'st/plcopen-n2.config.json'])
    assert rc == 0
    assert len(filter_warns(warns, 'PLCOPEN-N2')) == 2
    with DumpManager(fdump):
        pass


def test_n4():
    f = 'st/plcopen-n4.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f], args=['-c', 'st/plcopen-n4.config.json'])
    assert rc == 0
    assert len(filter_warns(warns, 'PLCOPEN-N4')) == 2
    with DumpManager(fdump):
        pass


def test_n5():
    f = 'st/plcopen-n5.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f])
    assert rc == 0
    assert len(filter_warns(warns, 'PLCOPEN-N5')) == 1
    with DumpManager(fdump):
        pass


def test_n6():
    f = 'st/plcopen-n6.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f], args=['-c', 'st/plcopen-n6.config.json'])
    assert rc == 0
    assert len(filter_warns(warns, 'PLCOPEN-N6')) == 2
    with DumpManager(fdump):
        pass


def test_n8():
    f = 'st/plcopen-n8.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f])
    assert rc == 0
    assert len(filter_warns(warns, 'PLCOPEN-N8')) == 0
    with DumpManager(fdump):
        pass


def test_n9():
    f = 'st/plcopen-n9.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f])
    assert rc == 0
    assert len(filter_warns(warns, 'PLCOPEN-N9')) == 2
    with DumpManager(fdump):
        pass


def test_n10():
    f = 'st/plcopen-n10.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f], args=['-c', 'st/plcopen-n10.config.json'])
    assert rc == 0
    assert len(filter_warns(warns, 'PLCOPEN-N10')) == 2
    with DumpManager(fdump):
        pass


def test_cp17_field_and_element_access():
    """Reading or writing a field or an element uses the parameter itself."""
    warns, rc = check_program(
        """
        TYPE Rec : STRUCT lo : INT; hi : INT; END_STRUCT; END_TYPE
        FUNCTION_BLOCK fb
        VAR_INPUT ir : Rec; iw : Rec; ia : ARRAY[1..2] OF Rec; END_VAR
        VAR_OUTPUT ow : Rec; oa : ARRAY[1..2] OF Rec; ou : Rec; END_VAR
        VAR_IN_OUT io : Rec; END_VAR
        VAR n : INT; END_VAR
        n := ir.lo + ia[1].hi + io.lo;
        ow.lo := n;
        oa[2].hi := n;
        iw.hi := 1;
        END_FUNCTION_BLOCK
        """.replace('\n', ''))
    assert rc == 0
    msgs = sorted(w.msg for w in filter_warns(warns, 'PLCOPEN-CP17'))
    assert msgs == [
        "Input parameter 'IW' of function block FB is never read",
        "Input parameter 'IW' of function block FB should not be written",
        "Output parameter 'OU' of function block FB is never written",
    ], msgs
    with DumpManager('stdin.dump.json'):
        pass


def test_cp26_field_and_element_writes():
    """A write to a field or an element of a global writes the global."""
    warns, rc = check_program(
        """
        TYPE Rec : STRUCT lo : INT; END_STRUCT; END_TYPE
        PROGRAM pa
        VAR_EXTERNAL g : Rec; h : ARRAY[1..2] OF Rec; k : Rec; END_VAR
        VAR n : INT; END_VAR
        g.lo := 1; h[1].lo := 2; n := k.lo;
        END_PROGRAM
        PROGRAM pb
        VAR_EXTERNAL g : Rec; h : ARRAY[1..2] OF Rec; k : Rec; END_VAR
        VAR n : INT; END_VAR
        g.lo := 3; h[2].lo := 4; n := k.lo;
        END_PROGRAM
        """.replace('\n', ''))
    assert rc == 0
    msgs = sorted(w.msg for w in filter_warns(warns, 'PLCOPEN-CP26'))
    assert len(msgs) == 2, msgs
    assert "'G'" in msgs[0] and "'H'" in msgs[1], msgs
    with DumpManager('stdin.dump.json'):
        pass


def test_cp25_path_is_not_typed_as_its_root():
    warns, rc = check_program(
        """
        PROGRAM p
        VAR n : INT; r : REAL; w : WORD; END_VAR
        n := r;
        w.3 := r;
        n.lo := r;
        r := w.%X1;
        END_PROGRAM
        """.replace('\n', ''))
    assert rc == 0
    assert len(filter_warns(warns, 'PLCOPEN-CP25')) == 1
    with DumpManager('stdin.dump.json'):
        pass


def test_l22_l13_qualified_loop_variable():
    """A loop variable `g.i` is that path, not every access rooted at `g`."""
    warns, rc = check_program(
        """
        PROGRAM p
        VAR n : INT; END_VAR
        FOR g.i := 1 TO 3 DO g.other := 1; n := g.limit; g.i := 2; END_FOR;
        n := g.other;
        n := g.i;
        END_PROGRAM
        """.replace('\n', ''))
    assert rc == 0
    l22 = filter_warns(warns, 'PLCOPEN-L22')
    l13 = filter_warns(warns, 'PLCOPEN-L13')
    assert [w.msg for w in l22] == ["Loop variable 'G.I' should not be modified inside a FOR loop"]
    assert [w.msg for w in l13] == ["FOR loop variable 'G.I' should not be used outside the FOR loop"]
    with DumpManager('stdin.dump.json'):
        pass
