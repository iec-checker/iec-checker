"""Tests for PLCOpen inspections."""
import json
import re
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
    assert sorted(w.linenr for w in filter_warns(checker_warnings, 'PLCOPEN-CP1')) == [5]
    with DumpManager(fdump):
        pass


def test_cp3():
    f = 'st/plcopen-cp3.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    assert sorted(w.linenr for w in filter_warns(checker_warnings, 'PLCOPEN-CP3')) == [4, 5, 7]
    with DumpManager(fdump):
        pass


def test_cp3_no_initializer_allowed():
    """`VAR_IN_OUT` and `VAR_EXTERNAL` declarations take no initial value
    (IEC 61131-3, B.1.4.3): the caller or the `VAR_GLOBAL` supplies it."""
    warns, rc = check_program(
        """
        CONFIGURATION plant
          VAR_GLOBAL limit : INT := 100; END_VAR
          RESOURCE r ON PLC
            TASK t(INTERVAL := T#10ms, PRIORITY := 1);
            PROGRAM main WITH t : p;
          END_RESOURCE
        END_CONFIGURATION
        FUNCTION_BLOCK clamp
        VAR_IN_OUT v : INT; END_VAR
        VAR_EXTERNAL limit : INT; END_VAR
        VAR scratch : INT; END_VAR
        scratch := v;
        IF scratch > limit THEN v := limit; END_IF;
        END_FUNCTION_BLOCK
        PROGRAM p
        VAR x : INT := 0; c : clamp; END_VAR
        c(v := x);
        END_PROGRAM
        """.replace('\n', ''))
    assert rc == 0, warns
    msgs = sorted(w.msg for w in filter_warns(warns, 'PLCOPEN-CP3'))
    assert msgs == ['Variable SCRATCH shall be initialized before being used'], msgs
    with DumpManager('stdin.dump.json'):
        pass


def test_cp3_skips_fb_and_class_instances(tmp_path):
    """An instance takes the initial values its FB or class declares."""
    f = tmp_path / 'instances.st'
    f.write_text(
        'PROGRAM line\n'
        'VAR\n'
        '  pulse : TON;\n'
        '  hold : tof;\n'
        '  parts : CTU_DINT;\n'
        '  edge : R_TRIG;\n'
        '  feeder : Feeder;\n'
        '  gate : Gate;\n'
        '  recipe : Recipe;\n'
        '  remote : Lib_Drive;\n'
        '  speed : INT;\n'
        'END_VAR\n'
        'pulse(IN := edge.Q, PT := T#1s);\n'
        'feeder(go := pulse.Q);\n'
        'END_PROGRAM\n'
        'FUNCTION_BLOCK Feeder\n'
        'VAR_INPUT go : BOOL := FALSE; END_VAR\n'
        'END_FUNCTION_BLOCK\n'
        'CLASS Gate\n'
        'VAR open : BOOL := FALSE; END_VAR\n'
        'END_CLASS\n'
        'TYPE Recipe : STRUCT temp : INT := 0; END_STRUCT; END_TYPE\n')
    warns, rc = run_checker([str(f)])
    assert rc == 0
    got = sorted(w.msg.split()[1] for w in filter_warns(warns, 'PLCOPEN-CP3'))
    assert got == ['RECIPE', 'REMOTE', 'SPEED'], got


def test_cp4_same_address_and_memory_areas():
    """Two variables at one address overlap; addresses in different memory
    areas (`%I`, `%Q`, `%M`) never do."""
    warns, rc = check_program(
        """PROGRAM p
        VAR
          a AT %MW10 : INT;
          b AT %MW10 : INT;
          sw AT %IW0 : INT;
          lamp AT %QW1 : INT;
          lo AT %MW20 : INT;
          hi AT %MW21 : INT;
          flag AT %IX4.2 : BOOL;
          same AT %IX4.2 : BOOL;
        END_VAR
        a := b + sw + lo + hi;
        lamp := a;
        same := flag;
        END_PROGRAM
        """)
    assert rc == 0, warns
    lines = sorted(w.linenr for w in filter_warns(warns, 'PLCOPEN-CP4'))
    assert lines == [3, 4, 7, 8, 9, 10], lines
    with DumpManager('stdin.dump.json'):
        pass


def test_direct_variable_names_in_messages():
    """A direct variable is `%` + location prefix + size prefix + address
    (IEC 61131-3, 2.4.1.1): `%QW3`, not `%WQ3`."""
    warns, rc = check_program(
        """PROGRAM p
        VAR
          a AT %MW10 : INT;
          b AT %MW10 : INT;
          r : INT := 0;
        END_VAR
        %QW3 := r;
        %MD4.1 := r;
        a := b + r;
        END_PROGRAM
        """)
    assert rc == 0, warns
    cp4 = {w.msg for w in filter_warns(warns, 'PLCOPEN-CP4')}
    assert cp4 == {'Address of direct variable %MW10 (size 2) should not '
                   'overlap with direct variable %MW10'}, cp4
    n1 = sorted(w.msg for w in filter_warns(warns, 'PLCOPEN-N1'))
    assert n1 == ['Avoid hardcoded physical address %MD4.1 in code',
                  'Avoid hardcoded physical address %QW3 in code'], n1
    with DumpManager('stdin.dump.json'):
        pass


def test_cp6():
    f = 'st/plcopen-cp6.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    assert sorted(w.linenr for w in filter_warns(checker_warnings, 'PLCOPEN-CP6')) == [3, 10, 24]
    with DumpManager(fdump):
        pass


def test_cp8():
    f = 'st/plcopen-cp8.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    assert sorted(w.linenr for w in filter_warns(checker_warnings, 'PLCOPEN-CP8')) == [6, 10, 14, 18]
    with DumpManager(fdump):
        pass


def test_cp28():
    f = 'st/plcopen-cp28.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    assert sorted(w.linenr for w in filter_warns(checker_warnings, 'PLCOPEN-CP28')) == [6, 10, 14, 18]
    with DumpManager(fdump):
        pass


def test_cp13():
    f = 'st/plcopen-cp13.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    assert sorted(w.linenr for w in filter_warns(checker_warnings, 'PLCOPEN-CP13')) == [8]
    with DumpManager(fdump):
        pass


def test_cp25():
    f = 'st/plcopen-cp25.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    assert sorted(w.linenr for w in filter_warns(checker_warnings, 'PLCOPEN-CP25')) == [7, 8]
    with DumpManager(fdump):
        pass


def test_l10():
    f = 'st/plcopen-l10.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    assert sorted(w.linenr for w in filter_warns(checker_warnings, 'PLCOPEN-L10')) == [12, 16, 18]
    with DumpManager(fdump):
        pass


def test_l17():
    f = 'st/plcopen-l17.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    l17_warns = filter_warns(checker_warnings, 'PLCOPEN-L17')
    assert any(w.linenr == 10 and w.column == 3 for w in l17_warns)
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
        (4, 5), (5, 5), (5, 5), (6, 5), (8, 5), (9, 5), (9, 5),
        (10, 5), (12, 5), (12, 5), (17, 5), (18, 5), (25, 5),
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
    assert any(w.linenr == 6 and w.column == 5 for w in n3_warns)
    with DumpManager(fdump):
        pass


def test_cp9():
    f = 'st/plcopen-cp9.st'
    fdump = f'{f}.dump.json'
    warns, rc = run_checker([f])
    assert rc == 0
    cp9 = [w.msg for w in filter_warns(warns, 'PLCOPEN-CP9')]
    assert cp9 == ['Code of function block CHARCURVE is too complex (27 statements)'], cp9
    with DumpManager(fdump):
        pass


def test_cp9_reports_at_the_pou():
    """CP9 names the POU and reports at its name, not at `0:0`."""
    chain = 'IF n > 0 THEN n := 1;' + ''.join(
        f' ELSIF n > {i} THEN n := {i + 1};' for i in range(1, 20)) + ' ELSE n := 0; END_IF;'
    warns, rc = check_program(
        f"""FUNCTION_BLOCK Ladder
        VAR n : INT := 0; END_VAR
        {chain}
        END_FUNCTION_BLOCK
        PROGRAM Main
        VAR n : INT := 0; END_VAR
        {chain}
        END_PROGRAM
        """)
    assert rc == 0, warns
    got = sorted((w.linenr, re.sub(r'\d+', 'N', w.msg))
                 for w in filter_warns(warns, 'PLCOPEN-CP9'))
    assert got == [
        (1, 'Code of function block LADDER is too complex (N McCabe complexity)'),
        (1, 'Code of function block LADDER is too complex (N statements)'),
        (5, 'Code of program MAIN is too complex (N McCabe complexity)'),
        (5, 'Code of program MAIN is too complex (N statements)'),
    ], got
    with DumpManager('stdin.dump.json'):
        pass


def test_cp9_mccabe_counts_decisions(tmp_path):
    """1 plus each IF, ELSIF, CASE selection and loop; calls, RETURN and AND/OR add nothing."""
    cfg = tmp_path / 'cfg.json'
    cfg.write_text('{"thresholds": {"mccabe_complexity": 0}}')
    f = tmp_path / 'mccabe.st'
    f.write_text(
        'FUNCTION Flat : INT\n'
        'VAR_INPUT i : INT := 0; END_VAR\n'
        'Flat := i + 1;\n'
        'END_FUNCTION\n'
        'PROGRAM Ifs\n'
        'VAR n : INT := 0; a : BOOL := FALSE; END_VAR\n'
        'IF n > 1 THEN n := 1; END_IF;\n'
        'Flat(i := n);\n'
        'IF a AND n > 2 OR NOT a THEN n := 2; END_IF;\n'
        'Flat(i := 2);\n'
        'IF n > 3 THEN n := 3; END_IF;\n'
        'END_PROGRAM\n'
        'FUNCTION_BLOCK Chain\n'
        'VAR n : INT := 0; END_VAR\n'
        'IF n = 1 THEN RETURN; ELSIF n = 2 THEN n := 0; ELSIF n = 3 THEN RETURN; ELSE n := 1; END_IF;\n'
        'END_FUNCTION_BLOCK\n'
        'FUNCTION_BLOCK Loops\n'
        'VAR n : INT := 0; k : INT := 0; END_VAR\n'
        'FOR k := 1 TO 3 DO IF k = n THEN EXIT; END_IF; END_FOR;\n'
        'WHILE n < 5 DO n := n + 1; END_WHILE;\n'
        'REPEAT n := n - 1; UNTIL n < 0 END_REPEAT;\n'
        'CASE n OF 1, 2: n := 0; 3..4: n := 1; 5: n := 2; ELSE n := 3; END_CASE;\n'
        'END_FUNCTION_BLOCK\n')
    warns, rc = run_checker([str(f)], args=['-c', str(cfg)])
    assert rc == 0
    got = sorted(re.match(r'Code of [a-z ]+ (\w+) is too complex \((-?\d+) McCabe', w.msg).groups()
                 for w in filter_warns(warns, 'PLCOPEN-CP9') if 'McCabe' in w.msg)
    assert got == [('CHAIN', '4'), ('FLAT', '1'), ('IFS', '4'), ('LOOPS', '8')], got


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


def test_n5_var_external_is_not_a_local():
    """`VAR_EXTERNAL` refers to the global: it shadows nothing (IEC 61131-3,
    2.4.3, table 16a)."""
    cfg = """
        CONFIGURATION plant
          VAR_GLOBAL limit : INT := 100; END_VAR
          RESOURCE r ON PLC
            TASK t(INTERVAL := T#10ms, PRIORITY := 1);
            PROGRAM main WITH t : p;
          END_RESOURCE
        END_CONFIGURATION
        """
    for section, expected in (('VAR_EXTERNAL limit : INT; END_VAR', 0),
                              ('VAR limit : INT := 0; END_VAR', 1)):
        warns, rc = check_program((cfg + f"""
            PROGRAM p
            {section}
            VAR x : INT := 0; END_VAR
            x := limit;
            END_PROGRAM
            """).replace('\n', ''))
        assert rc == 0, warns
        assert len(filter_warns(warns, 'PLCOPEN-N5')) == expected, (section, warns)
    with DumpManager('stdin.dump.json'):
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


def test_cp8_cp28_equality_and_inequality_once():
    """`=` and `<>` are both reported, each comparison exactly once."""
    for check in ('cp8', 'cp28'):
        f = f'st/plcopen-{check}.st'
        warns, rc = run_checker([f])
        lines = sorted(w.linenr for w in filter_warns(warns, f'PLCOPEN-{check.upper()}'))
        assert lines == [6, 10, 14, 18], (check, lines)
        with DumpManager(f'{f}.dump.json'):
            pass


def test_cp8_cp28_nested_comparisons(tmp_path):
    f = tmp_path / 'nested.st'
    f.write_text(
        'PROGRAM nested\n'
        'VAR r : REAL; t : TIME; b : BOOL; END_VAR\n'
        'IF (r = 1.5) AND b THEN\n'
        '  IF b THEN\n'
        '    IF r <> 2.5 THEN b := FALSE; END_IF;\n'
        '  END_IF;\n'
        'END_IF;\n'
        'b := MOVE(t = T#1s);\n'
        'WHILE t <> T#2s DO t := t + T#1s; END_WHILE;\n'
        'b := r < 1.5;\n'
        'END_PROGRAM\n')
    warns, rc = run_checker([str(f)])
    assert sorted(w.linenr for w in filter_warns(warns, 'PLCOPEN-CP8')) == [3, 5]
    assert sorted(w.linenr for w in filter_warns(warns, 'PLCOPEN-CP28')) == [8, 9]


def test_cp8_real_variables(tmp_path):
    """A variable declared REAL or LREAL in the POU is enough, without a REAL literal."""
    f = tmp_path / 'real_vars.st'
    f.write_text(
        'FUNCTION_BLOCK gauge\n'
        'VAR_INPUT lo : LREAL := 0.0; hi : LREAL := 1.0; END_VAR\n'
        'VAR_EXTERNAL g : REAL; END_VAR\n'
        'VAR k : INT := 0; m : INT := 0; END_VAR\n'
        'IF lo = hi THEN k := 1; END_IF;\n'
        'IF lo <> lo THEN k := 2; END_IF;\n'
        'IF k = 3 AND g <> hi THEN k := 3; END_IF;\n'
        'IF k = m THEN k := 4; END_IF;\n'
        'IF lo < hi THEN k := 5; END_IF;\n'
        'END_FUNCTION_BLOCK\n'
        'PROGRAM main\n'
        'VAR lo : INT := 0; hi : INT := 0; END_VAR\n'
        'IF lo = hi THEN lo := 1; END_IF;\n'
        'END_PROGRAM\n')
    warns, rc = run_checker([str(f)])
    assert rc == 0
    assert sorted(w.linenr for w in filter_warns(warns, 'PLCOPEN-CP8')) == [5, 6, 7]


def test_cp25_ignores_output_assignment_formals():
    """The formal output name of an FB is not a variable of the caller."""
    warns, rc = check_program(
        """
        PROGRAM p
        VAR ctr : CTU; up : BOOL; count : INT; CV : REAL; END_VAR
        ctr(CU := up, PV := 10, CV => count);
        CV := 1.5;
        END_PROGRAM
        """.replace('\n', ''))
    assert not filter_warns(warns, 'PLCOPEN-CP25'), warns
    with DumpManager('stdin.dump.json'):
        pass


def _positions(n):
    if isinstance(n, dict):
        if 'linenr' in n and 'col' in n:
            yield n['linenr'], n['col']
        for v in n.values():
            yield from _positions(v)
    elif isinstance(n, list):
        for v in n:
            yield from _positions(v)


def test_columns_are_token_starts(tmp_path):
    f = tmp_path / 'columns.st'
    f.write_bytes(
        b'\xef\xbb\xbfPROGRAM plant\r\n'
        b'VAR\r\n'
        b'\tcounter : INT;\r\n'
        b"  speed : REAL := 0.0; tick : TIME := T#0s; label : STRING := 'ab'; mask : WORD := 16#FF;\n"
        b'  flag : BOOL := FALSE; bias : INT := -3; shift : Gear := LOW;\n'
        b'END_VAR\n'
        b'(* multi\n'
        b'   line *) IF speed > 1.5 THEN\n'
        b'  counter := MOD(counter, 2) + 1;\n'
        b'END_IF;\n'
        b'/* c */ flag := %IX0.1 AND mask > 16#0F;\n'
        b'WHILE flag DO EXIT; END_WHILE;\n'
        b'tick := tick + T#1h2m;\n'
        b'bias := -bias + INT#5;\n'
        b'flag := NOT flag;\n'
        b'speed := REAL#-2.5;\n'
        b'IF shift = Gear#HIGH THEN shift := Gear#LOW; ELSE shift := Gear#HIGH; END_IF;\n'
        b'END_PROGRAM\n'
        b'TYPE Gear : (LOW, HIGH); END_TYPE\n')
    warns, rc = run_checker([str(f)])
    assert rc == 0
    ls = f.read_bytes()[3:].decode().split('\n')

    def tok(l, c):
        m = re.match(r"%\w+(?:\.\d+)*|'[^']*'|=|NOT \w+|-?\w+#-?[\w.]+|-?\d+\.\d+|-?\w+", ls[l - 1][c - 1:])
        return (c == 1 or not re.match(r'\w\w', ls[l - 1][c - 2:])) and m and m.group(0)

    with open(f'{f}.dump.json') as fp:
        got = {tok(l, c) for l, c in _positions(json.load(fp)) if l > 0}
    assert got == {
        'plant', 'counter', 'speed', 'tick', 'label', 'mask', 'flag', 'bias',
        '0.0', 'T#0s', "'ab'", '16#FF', 'FALSE', '-3', 'IF', '1.5', 'MOD', '2', '1',
        '%IX0.1', '16#0F', 'WHILE', 'EXIT', 'T#1h2m', '-bias', 'INT#5',
        'NOT flag', 'REAL#-2.5', 'shift', 'LOW', 'Gear#HIGH', 'Gear#LOW', '='}, got
    assert {(w.id, tok(w.linenr, w.column)) for w in warns} == {
        ('PLCOPEN-CP3', 'counter'), ('UnusedVariable', 'label'),
        ('PLCOPEN-L17', 'IF'), ('PLCOPEN-N1', '%IX0.1'),
        ('PLCOPEN-L10', 'EXIT')}, warns
    assert [(w.linenr, w.column) for w in filter_warns(warns, 'PLCOPEN-CP3')] == [(3, 2)]
    assert [(w.linenr, w.column) for w in filter_warns(warns, 'PLCOPEN-L17')] == [(8, 12)]


def test_columns_of_warnings_in_one_statement(tmp_path):
    f = tmp_path / 'mixer.st'
    f.write_text(
        'PROGRAM mixer\n'
        'VAR\n'
        '  level : INT;\n'
        '  ratio : REAL := 0.0;\n'
        'END_VAR\n'
        'IF ratio = 2.5 THEN\n'
        '  level := 1;\n'
        'END_IF;\n'
        'END_PROGRAM\n')
    warns, rc = run_checker([str(f)])
    assert rc == 0
    assert {(w.id, w.linenr, w.column) for w in warns} == {
        ('PLCOPEN-CP3', 3, 3), ('PLCOPEN-CP8', 6, 10), ('PLCOPEN-L17', 6, 1)}, warns


def test_warning_and_syntax_error_columns_agree(tmp_path):
    p = 'PROGRAM p VAR x : INT := 0; END_VAR\n    %s x := 1; END_IF;\nEND_PROGRAM\n'
    a, b = tmp_path / 'a.st', tmp_path / 'b.st'
    a.write_text(p % 'IF x > 0 THEN')
    b.write_text(p % 'END_IF;')
    w, _ = run_checker([str(a)])
    e, _ = run_checker([str(b)])
    assert [(x.linenr, x.column) for x in filter_warns(w, 'PLCOPEN-L17')] == [(2, 5)]
    assert [(x.linenr, x.column) for x in filter_warns(e, 'ParserError')] == [(2, 5)]


def test_cp8_cp28_cp25_point_at_the_comparison_operator(tmp_path):
    f = tmp_path / 'operators.st'
    f.write_text(
        'PROGRAM operators\n'
        'VAR flow : REAL := 0.0; delay : TIME := T#0s; n : INT := 0; END_VAR\n'
        'IF flow = 1.5 THEN n := 1; ELSE n := 2; END_IF;\n'
        'IF (n > 0) AND (2.5 <> flow) THEN n := 3; ELSE n := 4; END_IF;\n'
        'IF T#1h2m\n'
        '     = delay THEN n := 5; ELSE n := 6; END_IF;\n'
        'WHILE delay <> T#2s DO delay := delay + T#1s; END_WHILE;\n'
        'IF n = flow THEN n := 7; ELSE n := 8; END_IF;\n'
        'IF flow < 3.5 THEN n := 9; ELSE n := 10; END_IF;\n'
        'END_PROGRAM\n')
    warns, rc = run_checker([str(f)])
    assert rc == 0
    at = {i: sorted({(w.linenr, w.column) for w in filter_warns(warns, f'PLCOPEN-{i}')})
          for i in ('CP8', 'CP28', 'CP25')}
    assert at == {'CP8': [(3, 9), (4, 21), (8, 6)], 'CP28': [(6, 6), (7, 13)], 'CP25': [(8, 6)]}, at
