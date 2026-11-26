"""Tests for parser and lexer."""
import sys
import os
import json
import re
import subprocess

sys.path.append(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../src"))
from python.core import run_checker, check_program, filter_warns, binary_default  # noqa
from python.dump import DumpManager  # noqa


def _find_bool_constants(node):
    if isinstance(node, list):
        if (len(node) == 3 and node[0] == 'Bool'
                and isinstance(node[2], bool)):
            yield node[2]
        for child in node:
            yield from _find_bool_constants(child)
    elif isinstance(node, dict):
        for child in node.values():
            yield from _find_bool_constants(child)


def test_bool_literals_preserve_value():
    """`TRUE` must be lexed as the boolean value `true`, not `false`."""
    dump = 'stdin.dump.json'
    _, rc = check_program(
        """
        PROGRAM p
        VAR t : BOOL := TRUE; f : BOOL := FALSE; END_VAR
        t := TRUE;
        f := FALSE;
        END_PROGRAM
        """.replace('\n', ''))
    assert rc == 0
    try:
        with open(dump, 'r') as fp:
            scheme = json.load(fp)
        bools = list(_find_bool_constants(scheme))
        assert len(bools) > 0, 'no Bool constants found in dump'
        assert bools.count(True) > 0, (
            f'every Bool literal serialized as `false` — '
            f'`bool_true` lexer rule is flipped again. All bools: {bools}')
        assert bools.count(True) == bools.count(False), (
            f'asymmetric counts — TRUEs={bools.count(True)}, '
            f'FALSEs={bools.count(False)}, all={bools}')
    finally:
        if os.path.exists(dump):
            os.remove(dump)


def test_lexing_error():
    f = 'st/bad/lexing-error.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 1
    assert len(checker_warnings) == 1
    cv = checker_warnings[0]
    assert cv.id == 'LexingError'
    assert cv.linenr == 10
    assert cv.column == 6
    with DumpManager(fdump):
        pass


def test_lexing_error_context_snippet():
    """LexingError must carry the offending source line and a caret."""
    f = 'st/bad/lexing-error.st'
    fdump = f'{f}.dump.json'
    checker_warnings, _ = run_checker([f])
    cv = checker_warnings[0]
    assert cv.id == 'LexingError'
    assert 'wtf?' in cv.context
    assert '10 |' in cv.context
    # Caret must land under column 6 (the '?' char)
    caret_line = [l for l in cv.context.splitlines() if '^' in l][0]
    assert caret_line == '     |      ^'
    with DumpManager(fdump):
        pass


def test_parser_error_context_snippet():
    """ParserError must name the offending token and show a source snippet."""
    f = 'st/bad/semantic-error.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 1
    parser_warns = [w for w in checker_warnings if w.id == 'ParserError']
    assert len(parser_warns) == 1
    cv = parser_warns[0]
    assert cv.msg == 'unexpected token `"`'
    assert 'ANALOG_DATA_BAD' in cv.context
    assert '3 |' in cv.context
    assert '^' in cv.context
    with DumpManager(fdump):
        pass


def test_no_parser_error_no_context():
    """Valid programs must not emit any parser/lexer warnings with context."""
    _, rc = check_program(
        """
        PROGRAM p
        VAR a : INT; END_VAR
        a := 1;
        END_PROGRAM
        """.replace('\n', ''))
    assert rc == 0
    with DumpManager('stdin.dump.json'):
        pass


def test_parser_errors():
    for fname in os.listdir('st/bad/'):
        if not fname.endswith('.st'):
            continue
        f = os.path.join('st/bad/', fname)
        fdump = f'{f}.dump.json'
        checker_warnings, rc = run_checker([f])
        assert rc == 1, f"Incorrect exit code for {f}"
        assert len(checker_warnings) > 0
        with DumpManager(fdump):
            pass


def test_no_parser_errors():
    for fname in os.listdir('st/good/'):
        if not fname.endswith('.st'):
            continue
        f = os.path.join('st/good/', fname)
        fdump = f'{f}.dump.json'
        checker_warnings, rc = run_checker([f])
        assert rc == 0, f"Incorrect exit code for {f}"
        with DumpManager(fdump):
            pass


def test_direct_variables():
    f = 'st/good/direct-variables.st'
    fdump = f'{f}.dump.json'
    checker_warnings, rc = run_checker([f])
    assert rc == 0
    with DumpManager(fdump) as dm:
        _ = dm.scheme  # TODO


def test_statements_order():
    """Test that POU statements are arranged in the correct order."""
    fdump = f'stdin.dump.json'
    checker_warnings, rc = check_program(
        """
        PROGRAM p
        VAR a : INT; i : INT; END_VAR
        a := 1;
        i := 22;
        a := 16#42;
        END_PROGRAM
        """.replace('\n', ''))
    assert rc == 0
    with DumpManager(fdump) as dm:
        scheme = dm.scheme
        assert scheme
        assert len(scheme.programs) == 1
        # TODO: need recursive traverse in om
        # p = scheme.programs[0]
        # assert len(p.statements) == 3


def test_enum_types():
    fdump = f'stdin.dump.json'
    checker_warnings, rc = check_program(
        """
        TYPE
          Traffic_Light: (Red, Amber, Green);
        END_TYPE
        """.replace('\n', ''))
    assert rc == 0
    with DumpManager(fdump) as dm:
        scheme = dm.scheme
        assert scheme
        assert len(scheme.types) == 1
        ty = scheme.types[0]
        assert ty.name == 'TRAFFIC_LIGHT'
        assert ty.type == 'Enum'


def test_struct_types():
    fdump = f'stdin.dump.json'
    checker_warnings, rc = check_program(
        """
        TYPE
          Cooler: STRUCT
            Temp: INT;
            Cooling: TOF;
          END_STRUCT;
        END_TYPE
        """.replace('\n', ''))
    assert rc == 0
    with DumpManager(fdump) as dm:
        scheme = dm.scheme
        assert scheme
        assert len(scheme.types) == 1
        ty = scheme.types[0]
        assert ty.name == 'COOLER'
        assert ty.type == 'Struct'


def test_ref_types():
    fdump = f'stdin.dump.json'
    checker_warnings, rc = check_program(
        """
        TYPE myRef: REF_TO INT; END_TYPE
        """.replace('\n', ''))
    assert rc == 0
    with DumpManager(fdump) as dm:
        scheme = dm.scheme
        assert scheme
        assert len(scheme.types) == 1
        ty = scheme.types[0]
        assert ty.name == 'MYREF'
        assert ty.type == 'Ref'


def test_array_types():
    fdump = f'stdin.dump.json'
    checker_warnings, rc = check_program(
        """
        TYPE BITS: ARRAY [0..7] OF BOOL; END_TYPE
        """.replace('\n', ''))
    assert rc == 0
    with DumpManager(fdump) as dm:
        scheme = dm.scheme
        assert scheme
        assert len(scheme.types) == 1
        ty = scheme.types[0]
        assert ty.name == 'BITS'
        assert ty.type == 'Array'

def test_literal_elementary_ty_inference():
    """Test that CInteger, CReal, CBitString literals carry the correct
    elementary_ty when a type prefix is used, and carry None otherwise."""
    fdump = 'stdin.dump.json'
    _, rc = check_program("""
        PROGRAM p
        VAR
            (* Variable declaration and initialization - type-prefixed literals should infer concrete types *)
            a : INT := 123;           (* unprefixed integer → CInteger(ty=None) *)
            b : REAL := 1.23;         (* unprefixed real → CReal(ty=None) *)
            c : INT := INT#456;       (* INT# prefix → CInteger(ty=Some INT) *)
            d : REAL := REAL#7.89;    (* REAL# prefix → CReal(ty=Some REAL) *)
            e : UINT := UINT#789;     (* UINT# prefix → CInteger(ty=Some UINT) *)
            f : LREAL := LREAL#12.34; (* LREAL# prefix → CReal(ty=Some LREAL) *)
            g : BYTE := BYTE#16#FF;   (* BYTE# prefix → CBitString(ty=Some BYTE) *)
            h : WORD := WORD#16#ABCD; (* WORD# prefix → CBitString(ty=Some WORD) *)
        END_VAR

        (* Literals in assignment statements - also need to be verified *)
        a := 100;                    (* unprefixed → ty=None *)
        c := DINT#1000;             (* DINT# prefix → ty=Some DINT *)
        d := REAL#3.14;             (* REAL# prefix → ty=Some REAL *)
        END_PROGRAM
    """.replace('\n', ''))
    assert rc == 0

    with open(fdump, 'r') as fp:
        scheme = json.load(fp)

    # ------------------------------------------------------------------
    # Auxiliary recursive lookup function: extract all constant node 
    # information from the JSON tree
    # ------------------------------------------------------------------
    def find_constants(node):
        """Traverse the JSON tree recursively, returning a list of all constant nodes.
        
        Each element is a (tag, type_str_or_none, value) tuple:
          - tag: "Integer" / "Real" / "BitString"
          - type_str_or_none: typename string list or None
          - value: int or float
        """
        results = []
        if isinstance(node, list):
            # yojson encoding of variant: ["Tagname", arg0, arg1, arg2, ...]
            # Three forms of constant:
            #   ["Integer", ti_dict, type_opt, int_val]
            #   ["Real",    ti_dict, type_opt, float_val]
            #   ["BitString", ti_dict, type_opt, int_val]
            if (len(node) >= 4 and isinstance(node[0], str)
                    and node[0] in ("Integer", "Real", "BitString")):
                tag = node[0]
                # node[1] is Tok_info dict, node[2] is elementary_ty option, node[3] is value
                ty_opt = node[2]  # Array of strings such as ["INT"] or None
                val = node[3]
                results.append((tag, ty_opt, val))
            for child in node:
                results.extend(find_constants(child))
        elif isinstance(node, dict):
            for child in node.values():
                results.extend(find_constants(child))
        return results

    consts = find_constants(scheme)
    assert len(consts) > 0, 'no constants found in dump'

    # Build index by tag+value to assert
    by_key = {(tag, val): ty_opt for tag, ty_opt, val in consts}

    # ---- CInteger: no prefix → None -------------------------------------------------
    assert ("Integer", 123) in by_key
    assert by_key[("Integer", 123)] is None, \
        f'bare integer 123 should have ty=None, got {by_key[("Integer", 123)]}'

    assert ("Integer", 100) in by_key
    assert by_key[("Integer", 100)] is None, \
        f'bare integer 100 should have ty=None, got {by_key[("Integer", 100)]}'

    print(by_key)
    # ---- CInteger: type prefix → Some(typename) --------------------------------------
    assert ("Integer", 456) in by_key
    assert by_key[("Integer", 456)] == ["INT"], \
        f'INT#456 should have ty="INT", got {by_key[("Integer", 456)]}'

    assert ("Integer", 789) in by_key
    assert by_key[("Integer", 789)] == ["UINT"], \
        f'UINT#789 should have ty="UINT", got {by_key[("Integer", 789)]}'

    assert ("Integer", 1000) in by_key
    assert by_key[("Integer", 1000)] == ["DINT"], \
        f'DINT#1000 should have ty="DINT", got {by_key[("Integer", 1000)]}'

    # ---- CReal: no prefix → None ----------------------------------------------------
    # Find the Real that value≈1.23
    real_123 = [(tag, ty, v) for tag, ty, v in consts
                if tag == "Real" and abs(v - 1.23) < 1e-9]
    assert len(real_123) >= 1, 'no Real constant ~1.23 found'
    _, ty_123, _ = real_123[0]
    assert ty_123 is None, \
        f'bare real 1.23 should have ty=None, got {ty_123}'

    # ---- CReal: type prefix → Some(typename) ----------------------------------------
    real_789 = [(tag, ty, v) for tag, ty, v in consts
                if tag == "Real" and abs(v - 7.89) < 1e-9]
    assert len(real_789) >= 1, 'no Real constant ~7.89 found'
    _, ty_789, _ = real_789[0]
    assert ty_789 == ["REAL"], \
        f'REAL#7.89 should have ty="REAL", got {ty_789}'

    real_1234 = [(tag, ty, v) for tag, ty, v in consts
                 if tag == "Real" and abs(v - 12.34) < 1e-9]
    assert len(real_1234) >= 1, 'no Real constant ~12.34 found'
    _, ty_1234, _ = real_1234[0]
    assert ty_1234 == ["LREAL"], \
        f'LREAL#12.34 should have ty="LREAL", got {ty_1234}'

    real_314 = [(tag, ty, v) for tag, ty, v in consts
                if tag == "Real" and abs(v - 3.14) < 1e-9]
    assert len(real_314) >= 1, 'no Real constant ~3.14 found'
    _, ty_314, _ = real_314[0]
    assert ty_314 == ["REAL"], \
        f'REAL#3.14 should have ty="REAL", got {ty_314}'

    # ---- CBitString: type prefix → Some(typename) -----------------------------------
    # BYTE#16#FF → value is 255 (0xFF)
    assert ("BitString", 255) in by_key, \
        f'BYTE#16#FF (value=255) not found. All BitStrings: {[(t,v) for t,_,v in consts if t=="BitString"]}'
    assert by_key[("BitString", 255)] == ["BYTE"], \
        f'BYTE#16#FF should have ty="BYTE", got {by_key[("BitString", 255)]}'

    # WORD#16#ABCD → value is 43981 (0xABCD)
    assert ("BitString", 43981) in by_key, \
        f'WORD#16#ABCD (value=43981) not found'
    assert by_key[("BitString", 43981)] == ["WORD"], \
        f'WORD#16#ABCD should have ty="WORD", got {by_key[("BitString", 43981)]}'
    os.remove(fdump)


def _syntax_errors(warns):
    return [w for w in warns if w.id in ('ParserError', 'LexingError')]


def test_string_literal_charset():
    """Space, non-ASCII bytes and `$` escapes are valid string characters."""
    warns, rc = check_program(
        """
        PROGRAM p
        VAR
          s : STRING := 'a b, $$ $L $N $P $R $T $l $n $p $r $t $' $41 "q"';
          w : WSTRING := "a b, $$ $N $T $" $0041 'q'";
          u : STRING := 'Schließen привет';
        END_VAR
        s := 'State Transition: ';
        w := " ";
        END_PROGRAM
        """.replace('\n', ''))
    assert not _syntax_errors(warns), _syntax_errors(warns)
    assert rc == 0
    with DumpManager('stdin.dump.json'):
        pass


def test_string_literal_rejects_unknown_escape():
    warns, rc = check_program(
        """
        PROGRAM p
        VAR s : STRING := '$Q'; END_VAR
        s := 'x';
        END_PROGRAM
        """.replace('\n', ''))
    e = _syntax_errors(warns)
    assert rc == 1
    assert len(e) == 1 and e[0].id == 'LexingError', warns
    with DumpManager('stdin.dump.json'):
        pass


def test_control_keywords_case_insensitive():
    """`if`, `If` and `IF` are the same keyword (IEC 61131-3, 2.1.3)."""
    p = """
        PROGRAM p
        VAR i, x : INT; END_VAR
        IF x = 1 THEN x := 2; ELSIF x = 2 THEN x := 3; ELSE x := 4; END_IF;
        CASE x OF 1: x := 2; ELSE x := 3; END_CASE;
        FOR i := 10 TO 1 BY -1 DO IF i = 3 THEN CONTINUE; END_IF; EXIT; END_FOR;
        WHILE x < 10 DO x := x + 1; END_WHILE;
        REPEAT x := x - 1; UNTIL x = 0 END_REPEAT;
        RETURN;
        END_PROGRAM
        """.replace('\n', '')
    kws = ['END_REPEAT', 'END_WHILE', 'END_CASE', 'END_FOR', 'END_IF',
           'CONTINUE', 'REPEAT', 'RETURN', 'ELSIF', 'UNTIL', 'WHILE',
           'EXIT', 'ELSE', 'THEN', 'CASE', 'FOR', 'IF', 'OF', 'TO', 'BY', 'DO']

    def recase(f):
        out = p
        for k in kws:
            out = re.sub(rf'\b{k}\b', f(k), out)
        return out

    dumps = []
    for src in (p, recase(str.lower), recase(str.capitalize)):
        warns, rc = check_program(src)
        assert not _syntax_errors(warns), (src, _syntax_errors(warns))
        assert rc == 0
        with open('stdin.dump.json') as fp:
            dumps.append(json.load(fp))
        os.remove('stdin.dump.json')
    assert dumps[0] == dumps[1] == dumps[2]


def test_keyword_prefixed_identifiers():
    warns, rc = check_program(
        """
        PROGRAM p
        VAR iffy, format, todo, done, ofs, bypass, exits : INT; END_VAR
        iffy := format + todo + done + ofs + bypass + exits;
        END_PROGRAM
        """.replace('\n', ''))
    assert not _syntax_errors(warns), _syntax_errors(warns)
    assert rc == 0
    with DumpManager('stdin.dump.json'):
        pass


def _find_case_stmts(node):
    if isinstance(node, list):
        if node and node[0] == 'Case':
            yield node
        for c in node:
            yield from _find_case_stmts(c)
    elif isinstance(node, dict):
        for c in node.values():
            yield from _find_case_stmts(c)


def _label(e):
    c = e[2][2]
    return c[2] if c[0] == 'EnumValue' else c


def test_case_enum_labels():
    """CASE labels may be enumerated values (IEC 61131-3, B.3.2.3)."""
    warns, rc = check_program(
        """
        TYPE E : (A, B, C, D); END_TYPE
        PROGRAM p
        VAR CONSTANT K : INT := 7; END_VAR
        VAR x : E; y : INT; END_VAR
        CASE x OF
          A: y := 1; y := 2;
          B, C: f(); y := 3;
          E#D: y := 4;
        ELSE
          y := 5;
        END_CASE;
        CASE y OF
          1, 2: y := 0;
          K: y := 1;
          3..5: y := 2;
        END_CASE;
        END_PROGRAM
        """.replace('\n', ''))
    assert not _syntax_errors(warns), _syntax_errors(warns)
    with open('stdin.dump.json') as fp:
        cases = list(_find_case_stmts(json.load(fp)))
    os.remove('stdin.dump.json')
    assert len(cases) == 2
    sels = cases[0][3]
    assert [[_label(l) for l in s['case']] for s in sels] == \
        [['A'], ['B', 'C'], ['D']]
    assert [len(s['body']) for s in sels] == [2, 2, 1]
    assert len(cases[0][4]) == 1
    sels = cases[1][3]
    assert [len(s['case']) for s in sels] == [2, 1, 1]
    assert _label(sels[1]['case'][0]) == 'K'
    assert [len(s['body']) for s in sels] == [1, 1, 1]


def test_case_label_errors():
    for body in ('A y := 1;', 'y := 1; A: y := 2;'):
        warns, rc = check_program(
            f"""
            TYPE E : (A, B); END_TYPE
            PROGRAM p VAR x : E; y : INT; END_VAR
            CASE x OF {body} END_CASE;
            END_PROGRAM
            """.replace('\n', ''))
        e = _syntax_errors(warns)
        assert rc == 1
        assert len(e) == 1 and e[0].id == 'ParserError', (body, warns)
        with DumpManager('stdin.dump.json'):
            pass


def test_enum_value_initializers():
    """Variables, struct elements and array elements of an enumerated type
    may be initialized with an enumerated value (IEC 61131-3, B.1.3.3)."""
    warns, rc = check_program(
        """
        TYPE E : (A, B, C); END_TYPE
        TYPE S : STRUCT e : E := B; END_STRUCT; END_TYPE
        FUNCTION_BLOCK fb
        VAR_INPUT i : E := C; END_VAR
        VAR x : E := B; z : E := E#C; s : S; END_VAR
        x := z;
        END_FUNCTION_BLOCK
        """.replace('\n', ''))
    assert not _syntax_errors(warns), _syntax_errors(warns)
    with DumpManager('stdin.dump.json'):
        pass


def test_syntax_error_column_is_token_start():
    """The reported column is where the offending token starts, i.e. the
    column the context caret points at."""
    for src, tok in (
            ('PROGRAM p VAR x : INT; END_VAR x := 1 abcdef@; END_PROGRAM', ';'),
            ('PROGRAM p VAR x : INT; END_VAR x := 1; @END_VAR END_PROGRAM', 'END_VAR'),
            ('PROGRAM p VAR x : INT; END_VAR x := 1; END_PROGRAM @END_PROGRAM', 'END_PROGRAM'),
            ("PROGRAM p VAR s : STRING := 'a@$Qb'; END_VAR END_PROGRAM", '$')):
        col = src.index('@') + 1
        src = src.replace('@', '')
        warns, rc = check_program(src)
        e = _syntax_errors(warns)
        assert rc == 1
        assert len(e) == 1, (src, warns)
        assert src[col - 1:].startswith(tok)
        assert e[0].column == col, (src, e[0].column, col)
        caret = [ln for ln in e[0].context.splitlines() if '^' in ln][0]
        assert caret.index('^') - caret.index('|') - 1 == col, e[0].context
        with DumpManager('stdin.dump.json'):
            pass


def test_subscript_lists():
    """`m[i, j]` and `m[i][j]` are array variables (IEC 61131-3, B.1.4.2)."""
    warns, rc = check_program(
        """
        TYPE R : ARRAY[0..1] OF INT; END_TYPE
        TYPE M : ARRAY[0..1] OF R; END_TYPE
        PROGRAM p
        VAR m : ARRAY[1..2, 1..3] OF INT; n : M; i, x : INT; END_VAR
        m[1, 2] := n[0][1];
        n[i][i + 1] := m[i, i + 1] + m[2, 3];
        IF m[1, 1] > n[1][0] THEN x := MAX(m[1, 1], n[0][0]); END_IF;
        END_PROGRAM
        """.replace('\n', ''))
    assert not _syntax_errors(warns), _syntax_errors(warns)
    assert rc == 0
    with DumpManager('stdin.dump.json'):
        pass


def test_pragmas_keep_line_numbers(tmp_path):
    f = tmp_path / 'p.st'
    f.write_text('PROGRAM p\n{a\nb\n}\nVAR x : INT; END_VAR\nx := 1 2;\nEND_PROGRAM\n')
    warns, rc = run_checker([str(f)])
    e = _syntax_errors(warns)
    assert rc == 1
    assert len(e) == 1 and e[0].id == 'ParserError', warns
    assert (e[0].linenr, e[0].column) == (6, 8)


def test_pragma_errors():
    for src, msg in (
            ('PROGRAM p VAR x : INT; END_VAR x := 1; {never closed END_PROGRAM',
             'Pragma is not terminated'),
            ('PROGRAM p VAR x : INT; END_VAR x := 1; } END_PROGRAM',
             'Unexpected char: }')):
        warns, rc = check_program(src)
        e = _syntax_errors(warns)
        assert rc == 1
        assert len(e) == 1 and e[0].id == 'LexingError' and e[0].msg == msg, warns
        with DumpManager('stdin.dump.json'):
            pass


def _array_inits(scheme):
    return {v['var']['loc'][1]['name']: [c[3] for c in v['ty_spec'][3]]
            for pou in scheme['programs'] for v in pou['variables']
            if v['ty_spec'] and v['ty_spec'][0] == 'DTyDeclArrayType'}


def test_array_init_repetition():
    """`n(v)` repeats `v` n times, `n()` n default values (IEC 61131-3,
    B.1.3.3)."""
    warns, rc = check_program(
        """
        PROGRAM p
        VAR
          a : ARRAY[1..5] OF INT := [2(7), 3, 2()];
          b : ARRAY[1..4] OF INT := [4(0)];
          c : ARRAY[1..3] OF INT := [4(1)];
        END_VAR
        a[1] := b[1] + c[1];
        END_PROGRAM
        """.replace('\n', ''))
    assert not _syntax_errors(warns), _syntax_errors(warns)
    ws = filter_warns(warns, 'OutOfBounds')
    assert [w.msg for w in ws] == \
        ['C: Array initializer list exceeds capacity. Last 1 values will be lost.'], ws
    with open('stdin.dump.json') as fp:
        inits = _array_inits(json.load(fp))
    os.remove('stdin.dump.json')
    assert inits == {'A': [7, 7, 3, 0, 0], 'B': [0, 0, 0, 0], 'C': [1, 1, 1, 1]}


def test_program_configuration_connections():
    """`PROGRAM inst WITH t : prg (...)` (IEC 61131-3, B.1.7)."""
    warns, rc = check_program(
        """
        PROGRAM prg VAR_INPUT i : INT; END_VAR VAR x : INT; END_VAR x := i; END_PROGRAM
        CONFIGURATION cfg
          RESOURCE r ON PLC
            TASK t (INTERVAL := T#10ms, PRIORITY := 1);
            PROGRAM inst WITH t : prg (i := 1);
            PROGRAM inst2 : prg (i := 2);
          END_RESOURCE
        END_CONFIGURATION
        """.replace('\n', ''))
    assert not _syntax_errors(warns), _syntax_errors(warns)
    with DumpManager('stdin.dump.json'):
        pass


def _dump_of(src):
    warns, rc = check_program(src)
    assert not _syntax_errors(warns), (src, _syntax_errors(warns))
    with open('stdin.dump.json') as fp:
        d = json.load(fp)
    os.remove('stdin.dump.json')
    return d


def test_time_and_date_prefixes_case_insensitive():
    """`t#`, `d#` are the same prefixes as `T#`, `D#` (IEC 61131-3,
    tables 7 and 8: `t#14.7d`, `t#25h15m`, `d#1984-06-25`)."""
    p = """
        PROGRAM p
        VAR t : TIME; lt : LTIME; d : DATE; ld : LDATE; END_VAR
        t := T#14.7d; t := T#25h15m; t := T#-14ms; lt := LT#1s;
        d := D#1984-06-25; ld := LD#1984-06-25;
        END_PROGRAM
        """.replace('\n', '')
    low = re.sub(r'\b(LT|LD|T|D)#', lambda m: m.group(1).lower() + '#', p)
    assert 't#14.7d' in low and 'lt#1s' in low and 'ld#1984' in low
    assert _dump_of(p) == _dump_of(low)


def test_duration_units_case_insensitive():
    """Duration units may be upper- or lower-case (IEC 61131-3, 2.2.3.1)."""
    p = """
        PROGRAM p
        VAR t : LTIME; END_VAR
        t := LT#1d2h3m4s5ms6us7ns;
        END_PROGRAM
        """.replace('\n', '')
    dumps = [_dump_of(p.replace('1d2h3m4s5ms6us7ns', u)) for u in (
        '1d2h3m4s5ms6us7ns', '1D2H3M4S5MS6US7NS', '1d2h3m4s5Ms6Us7Ns', '1d2h3m4s5mS6uS7nS')]
    assert all(d == dumps[0] for d in dumps)


def _no_pos(node):
    if isinstance(node, dict):
        return {k: _no_pos(v) for k, v in node.items() if k not in ('linenr', 'col')}
    if isinstance(node, list):
        return [_no_pos(c) for c in node]
    return node


def test_duration_unit_underscores():
    """Units of a duration may be separated by underlines (IEC 61131-3,
    2.2.3.1 and table 7: `t#25h_15m`, `t#5d_14h_12m_18s_3.5ms`)."""
    p = """
        PROGRAM p
        VAR t : TIME; l : LTIME; END_VAR
        t := t#25h_15m; t := t#5d_14h_12m_18s_3.5ms; t := TIME#-1m_30s;
        l := LT#1ms_5us_3ns;
        END_PROGRAM
        """.replace('\n', '')
    plain = re.sub(r'(?<=[dhms])_(?=\d)', '', p)
    assert 't#5d14h12m18s3.5ms' in plain and 'LT#1ms5us3ns' in plain
    assert _no_pos(_dump_of(p)) == _no_pos(_dump_of(plain))
    for bad in ('T#1d_', 'T#1d__2h', 'T#1.5d_2h', 'T#1d_ 2h'):
        warns, rc = check_program(
            f'PROGRAM p VAR t : TIME; END_VAR t := {bad}; END_PROGRAM')
        assert rc == 1 and len(_syntax_errors(warns)) == 1, (bad, warns)
        with DumpManager('stdin.dump.json'):
            pass


def test_identifier_underscore_digit():
    """An identifier may start with an underline followed by a digit
    (IEC 61131-3, B.1.1)."""
    warns, rc = check_program(
        """
        PROGRAM p
        VAR _1abc, _9, _x1 : INT; END_VAR
        _1abc := _9 + _x1;
        END_PROGRAM
        """.replace('\n', ''))
    assert not _syntax_errors(warns), _syntax_errors(warns)
    assert rc == 0
    with DumpManager('stdin.dump.json'):
        pass
    for bad in ('__x', '_'):
        warns, rc = check_program(
            f'PROGRAM p VAR {bad} : INT; END_VAR {bad} := 1; END_PROGRAM')
        e = _syntax_errors(warns)
        assert rc == 1 and len(e) == 1 and e[0].id == 'LexingError', (bad, warns)
        with DumpManager('stdin.dump.json'):
            pass


def test_real_exponent_case_insensitive():
    """`exponent ::= ('E' | 'e') ['+'|'-'] integer` (IEC 61131-3, B.1.2.1)."""
    p = """
        PROGRAM p
        VAR r : LREAL; END_VAR
        r := 1.5E3; r := 2.0E-3; r := 1.0E+2;
        END_PROGRAM
        """.replace('\n', '')
    low = re.sub(r'(?<=\d)E(?=[+-]?\d)', 'e', p)
    assert '1.5e3' in low and '2.0e-3' in low and '1.0e+2' in low
    d = _dump_of(low)
    assert d == _dump_of(p)
    s = json.dumps(d)
    assert all(f', {v}]' in s for v in (1500.0, 0.002, 100.0)), s


def test_bool_literals_case_insensitive():
    """TRUE and FALSE are keywords, so their case is not significant
    (IEC 61131-3, 2.1.3); they must never be read as variables."""
    d = _dump_of(
        """
        PROGRAM p
        VAR b, trueish, false_x : BOOL; END_VAR
        b := tRuE; b := fAlSe; b := bool#1; b := Bool#0;
        b := bOOl#TrUe; b := BOOL#false; b := trueish; b := false_x;
        END_PROGRAM
        """.replace('\n', ''))
    assert list(_find_bool_constants(d)) == [True, False, True, False, True, False]
    s = json.dumps(d)
    assert '"name": "TRUE"' not in s and '"name": "FALSE"' not in s
    assert '"name": "TRUEISH"' in s and '"name": "FALSE_X"' in s


def test_equ_is_not_a_keyword():
    """EQU is not an IEC 61131-3 keyword (annex C)."""
    warns, rc = check_program(
        'PROGRAM p VAR equ, Equ_1 : INT; END_VAR equ := Equ_1 + 1; END_PROGRAM')
    assert not _syntax_errors(warns), _syntax_errors(warns)
    with DumpManager('stdin.dump.json'):
        pass


def _run_raw(path, *args):
    """Runs the checker and decodes its JSON output strictly as UTF-8."""
    p = subprocess.run([binary_default, '-o', 'json', '-q', *args, str(path)],
                       capture_output=True)
    return json.loads(p.stdout.decode('utf-8')), p.returncode


def test_diagnostics_are_valid_utf8(tmp_path):
    """Non-ASCII input never produces invalid UTF-8 in the output."""
    for src, msg in (
            ('x := 1; ы'.encode(), 'Unexpected char: ы'),
            (b'x := 1; \xe4', 'Unexpected char: \\xE4')):
        f = tmp_path / 'p.st'
        f.write_bytes(b'PROGRAM p VAR x : INT; END_VAR ' + src + b' END_PROGRAM\n')
        warns, rc = _run_raw(f)
        e = [w for w in warns if w['id'] == 'LexingError']
        assert rc == 1 and len(e) == 1 and e[0]['msg'] == msg, warns
    f.write_bytes(b"PROGRAM p VAR s : STRING := '\xe4'; x : INT; END_VAR x := 1 2; END_PROGRAM\n")
    warns, rc = _run_raw(f)
    e = [w for w in warns if w['id'] == 'ParserError']
    assert rc == 1 and len(e) == 1 and "'\\xE4'" in e[0]['context'], warns


def test_utf8_bom(tmp_path):
    """A UTF-8 byte order mark is not part of the program text."""
    bom = b'\xef\xbb\xbf'
    src = 'PROGRAM p VAR x : INT; END_VAR x := 1 2; END_PROGRAM\n'
    f = tmp_path / 'p.st'
    f.write_bytes(bom + src.encode())
    warns, rc = _run_raw(f)
    e = [w for w in warns if w['id'] in ('ParserError', 'LexingError')]
    assert rc == 1 and len(e) == 1, warns
    assert (e[0]['linenr'], e[0]['column']) == (1, src.index('2') + 1)
    a, b = tmp_path / 'a.st', tmp_path / 'b.st'
    a.write_bytes(bom + b'FUNCTION f : INT f := 1; END_FUNCTION\n')
    b.write_bytes(bom + b'PROGRAM p VAR x : INT; END_VAR x := f(); END_PROGRAM\n')
    warns, rc = _run_raw(b, '-m', str(a))
    assert not [w for w in warns if w['id'] in ('ParserError', 'LexingError')], warns


def test_string_prefix_case_insensitive():
    p = """
        PROGRAM p
        VAR s : STRING; END_VAR
        s := STRING#'a b'; s := STRING#'c';
        END_PROGRAM
        """.replace('\n', '')
    low = p.replace("STRING#'a", "string#'a").replace("STRING#'c", "String#'c")
    assert "string#'a b'" in low and "String#'c'" in low
    assert _dump_of(p) == _dump_of(low)


def test_subrange_var_decl():
    """Variables may be declared with a subrange specification
    (IEC 61131-3, B.1.4.3: `var1_init_decl ::= var1_list ':'
    (simple_spec_init | subrange_spec_init | enumerated_spec_init)`)."""
    d = _dump_of(
        """
        FUNCTION_BLOCK fb
        VAR_INPUT i : USINT (1..8) := 8; END_VAR
        VAR r : INT (0..10) := 5; a, b : SINT (-5..5); END_VAR
        r := a;
        END_FUNCTION_BLOCK
        """.replace('\n', ''))
    vs = {v['var']['loc'][1]['name']: (v['ty_spec'], v['was_init'])
          for v in d['function_blocks'][0]['variables']}
    assert vs == {
        'I': (['DTyDeclSubrange', [['USINT'], 1, 8], 8], True),
        'R': (['DTyDeclSubrange', [['INT'], 0, 10], 5], True),
        'A': (['DTyDeclSubrange', [['SINT'], -5, 5], -5], False),
        'B': (['DTyDeclSubrange', [['SINT'], -5, 5], -5], False),
    }, vs


def test_subrange_var_decl_needs_integer_type():
    warns, rc = check_program(
        'PROGRAM p VAR x : REAL (0..1); END_VAR x := 0.5; END_PROGRAM')
    e = _syntax_errors(warns)
    assert rc == 1 and len(e) == 1 and e[0].id == 'ParserError', warns
    with DumpManager('stdin.dump.json'):
        pass


_PATH_PRG = (
    'TYPE Cell : STRUCT lo : INT; hi : INT; END_STRUCT; END_TYPE '
    'PROGRAM p VAR c : ARRAY[1..3] OF Cell; g : ARRAY[0..1, 0..1] OF Cell; '
    'k : Cell; w : WORD; i, n : INT; b : BOOL; END_VAR %s END_PROGRAM')


def test_field_after_subscript():
    """`a[i].f` is a structured variable (IEC 61131-3, B.1.4.2)."""
    for body in (
            'n := c[1].lo;',
            'c[1].lo := n;',
            'n := c[i].lo + c[i + 1].hi;',
            'n := g[1, 0].lo;',
            'g[i, 1].hi := g[0, i].lo;',
            'n := k.arr[1].lo;',
            'k.arr[1].lo := n;',
            'n := k.arr[1].sub.arr2[i, 2].lo;',
            'k.arr[1].sub.arr2[i, 2].lo := n;',
            'n := c[c[1].lo].hi;',
            'c[c[1].lo].hi := c[c[2].hi].lo;',
            'n := c [ 1 ] . lo;',
            'n := k . lo;',
            'n := k .lo;',
            'n := k. lo;',
            'n := k.(* x *)lo;',
            'n := k.{x}lo;',
            'IF c[1].lo > c[2].hi AND k.lo = c[i].hi THEN n := 1; END_IF',
            'CASE c[i].lo OF 1: c[1].hi := 2; k.lo := 3; 2: n := c[2].lo; END_CASE',
            'CASE n OF E.A, E.sub.B: c[1].lo := 2; E.C: k.hi := 3; END_CASE',
            'FOR i := c[1].lo TO c[2].hi BY k.lo DO n := n + c[i].lo; END_FOR',
            'WHILE c[n].lo <> 0 DO n := n + 1; END_WHILE',
            'REPEAT n := c[n].lo; UNTIL c[n].hi = 0 END_REPEAT',
            'n := fn(c[1].lo, k.hi, o => c[2].hi);',
            'lib.fn(a := c[1].lo, o => k.hi);',
            'n := lib.sub.fn(c[1].lo);',
            'n := -c[1].lo ** 2;',
            'b := NOT c[1].flag;'):
        warns, rc = check_program(_PATH_PRG % body)
        assert not _syntax_errors(warns), (body, _syntax_errors(warns))
        with DumpManager('stdin.dump.json'):
            pass


def test_field_names_are_not_keywords():
    """An identifier after `.` is a field name even if it spells a keyword."""
    for f in ('single', 'on', 'at', 'to', 'by', 'of', 'type', 'task', 'int',
              'time', 'date', 'string', 'true', 'FALSE', 'if', 'end_if',
              'mod', 'not', 'and', 'ref', 'null', 'var', 'exit', 'return'):
        for body in (f'b := k.{f};', f'k.{f} := b;', f'b := c[1].{f};',
                     f'c[i].{f} := b;', f'b := c[1].x.{f}.y;'):
            warns, rc = check_program(_PATH_PRG % body)
            assert not _syntax_errors(warns), (body, _syntax_errors(warns))
            with DumpManager('stdin.dump.json'):
                pass


def test_bit_access():
    """`v.5` and `v.%X5` address a bit of a variable (IEC 61131-3 Table 16)."""
    for body in ('b := w.3;', 'w.4 := b;', 'b := w.%X5;', 'w.%X6 := TRUE;',
                 'b := w.%X0 AND b;', 'b := k.flags.7;', 'b := k.flags.%X8;',
                 'b := c[1].flags.9;', 'c[1].flags.%X10 := b;',
                 'b := c[1].%X1;', 'IF w.0 OR w.%X1 THEN n := 1; END_IF'):
        warns, rc = check_program(_PATH_PRG % body)
        assert not _syntax_errors(warns), (body, _syntax_errors(warns))
        with DumpManager('stdin.dump.json'):
            pass


def test_dot_neighbours():
    """Splitting identifiers at `.` must not disturb ranges and literals."""
    warns, rc = check_program(
        """
        TYPE R : INT (0..10); END_TYPE
        PROGRAM p
        VAR a : ARRAY[1..2] OF REAL; r : REAL := 1.5; q : INT (0..9);
        d : TIME := T#1.5s; m AT %MW10.3 : WORD; n : INT; END_VAR
        r := 2.25 + a[1] * 1.0e3;
        d := T#2h_3.5m;
        %MW10.3 := 16#FF;
        CASE n OF 1..5: n := 0; 6, 7..9: n := 1; END_CASE;
        END_PROGRAM
        """.replace('\n', ''))
    assert not _syntax_errors(warns), _syntax_errors(warns)
    with DumpManager('stdin.dump.json'):
        pass


def test_malformed_paths():
    for src, tok in (
            ('n := @.lo;', '.'),
            ('n := k.@;', ';'),
            ('n := k@..lo;', '..'),
            ('n := k.lo.@;', ';'),
            ('n := c[1]@..lo;', '..'),
            ('n := c[1].@[2];', '['),
            ('n := c[1].@;', ';'),
            ('n := c[1].lo.@[1];', '['),
            ('n := 1.5@.lo;', '.'),
            ('k. @:= 1;', ':='),
            ('c[1]. @:= 1;', ':='),
            ('fn(k.lo @:= 1);', ':='),
            ('n := k.@+ 1;', '+')):
        src = _PATH_PRG % src
        col = src.index('@') + 1
        src = src.replace('@', '')
        warns, rc = check_program(src)
        e = _syntax_errors(warns)
        assert rc == 1, src
        assert len(e) == 1 and e[0].id == 'ParserError', (src, warns)
        assert src[col - 1:].startswith(tok)
        assert e[0].column == col, (src, e[0].column, col)
        with DumpManager('stdin.dump.json'):
            pass


def test_declared_names_are_plain_identifiers():
    for src in (
            'PROGRAM p VAR a.b : INT; END_VAR END_PROGRAM',
            'PROGRAM p.q VAR a : INT; END_VAR END_PROGRAM',
            'TYPE S : STRUCT a.b : INT; END_STRUCT; END_TYPE',
            'TYPE S.T : INT; END_TYPE',
            'FUNCTION f.g : INT VAR a : INT; END_VAR END_FUNCTION'):
        warns, rc = check_program(src)
        e = _syntax_errors(warns)
        assert rc == 1 and len(e) == 1 and e[0].id == 'ParserError', (src, warns)
        with DumpManager('stdin.dump.json'):
            pass


def test_qualified_names():
    """Type, POU and enum names may be qualified with `.`."""
    warns, rc = check_program(
        """
        PROGRAM p
        VAR a : lib.Cell; b : ARRAY[1..2] OF lib.sub.Cell; e : lib.Mode := lib.Mode#RUN; n : INT; END_VAR
        n := lib.sub.fn(1);
        lib.fb(x := n);
        END_PROGRAM
        """.replace('\n', ''))
    assert not _syntax_errors(warns), _syntax_errors(warns)
    with DumpManager('stdin.dump.json'):
        pass


def _find_sym_vars(node):
    if isinstance(node, list):
        if len(node) == 2 and node[0] == 'SymVar' and isinstance(node[1], dict):
            yield node[1]
        for child in node:
            yield from _find_sym_vars(child)
    elif isinstance(node, dict):
        for child in node.values():
            yield from _find_sym_vars(child)


def test_variable_paths_in_dump():
    """A symbolic variable is dumped as its root name and a selector list."""
    warns, rc = check_program(_PATH_PRG % (
        'k.sub.lo := c[1].hi; g[i, 1].sub.arr[n + 1].lo := w.5; b := c[2].flags.%X3; n := i;'))
    assert not _syntax_errors(warns), _syntax_errors(warns)
    with open('stdin.dump.json') as fp:
        scheme = json.load(fp)
    os.remove('stdin.dump.json')
    assert scheme['version'] == '0.2'
    use = [v for v in _find_sym_vars(scheme['programs'][0]['statements'])]

    def path(v):
        return [s if s[0] != 'Part' else ['Part'] for s in v['path']]
    got = {(v['name'], json.dumps(path(v))) for v in use}
    assert got == {
        ('K', '[["Field", "SUB"], ["Field", "LO"]]'),
        ('C', '[["Index", [1]], ["Field", "HI"]]'),
        ('G', '[["Index", [null, 1]], ["Field", "SUB"], ["Field", "ARR"], ["Index", [null]], ["Field", "LO"]]'),
        ('W', '[["Bit", 5]]'),
        ('B', '[]'),
        ('C', '[["Index", [2]], ["Field", "FLAGS"], ["Part"]]'),
        ('N', '[]'),
        ('I', '[]'),
    }, got
    assert all(v['ti']['raw'].upper() == v['name'] for v in use)


def test_nested_array_init():
    """Nested initializer lists are flattened in row-major order."""
    warns, rc = check_program(
        """
        TYPE G : ARRAY[0..1, 0..2] OF INT := [[1, 2, 3], [4, 5, 6]]; END_TYPE
        PROGRAM p
        VAR
          a : ARRAY[0..1, 0..1] OF INT := [[5, 6], [7, 8]];
          b : ARRAY[1..2, 1..2] OF INT := [2([3, 4])];
          c : ARRAY[1..2, 1..2] OF INT := [[1, 2], 2(9)];
          d : ARRAY[0..1, 0..1, 0..1] OF INT := [[[1, 2], [3, 4]], [[5, 6], 2()]];
          e : ARRAY[0..1, 0..1] OF INT := [[1, 2], [3, 4, 5]];
        END_VAR
        a[0, 0] := b[1, 1] + c[1, 1] + d[0, 0, 0] + e[0, 0];
        END_PROGRAM
        """.replace('\n', ''))
    assert not _syntax_errors(warns), _syntax_errors(warns)
    ws = filter_warns(warns, 'OutOfBounds')
    assert [w.msg for w in ws] == \
        ['E: Array initializer list exceeds capacity. Last 1 values will be lost.'], ws
    with open('stdin.dump.json') as fp:
        inits = _array_inits(json.load(fp))
    os.remove('stdin.dump.json')
    assert inits == {'A': [5, 6, 7, 8], 'B': [3, 4, 3, 4], 'C': [1, 2, 9, 9],
                     'D': [1, 2, 3, 4, 5, 6, 0, 0], 'E': [1, 2, 3, 4, 5]}


def test_nested_array_init_errors():
    for init in ('[[1, 2],]', '[[]]', '[[1, 2]', '[2([])]', '[[1, 2]]]', '[1, [2, 3'):
        warns, rc = check_program(
            f'PROGRAM p VAR a : ARRAY[0..1, 0..1] OF INT := {init}; END_VAR a[0, 0] := 1; END_PROGRAM')
        e = _syntax_errors(warns)
        assert rc == 1 and len(e) == 1 and e[0].id == 'ParserError', (init, warns)
        with DumpManager('stdin.dump.json'):
            pass


def _find_calls(node, name):
    if isinstance(node, list):
        if len(node) == 4 and node[0] == 'FuncCall' and isinstance(node[2], dict) \
                and node[2].get('name') == name:
            yield node[3]
        for c in node:
            yield from _find_calls(c, name)
    elif isinstance(node, dict):
        for c in node.values():
            yield from _find_calls(c, name)


def test_call_positional_not_argument():
    """`NOT x` is an expression, so it can be a positional argument
    (IEC 61131-3, B.3.2.2); `NOT x => v` stays an inverted output."""
    d = _dump_of(
        """
        FUNCTION pick : INT
        VAR_INPUT c : BOOL; d : BOOL; END_VAR
        pick := 1;
        END_FUNCTION
        PROGRAM p
        VAR run, stop : BOOL; n : INT; tm : TON; END_VAR
        n := SEL(NOT run, 10, 20);
        stop := MOVE(NOT run);
        n := pick(stop, NOT run);
        n := pick(NOT run AND stop, stop);
        tm(NOT Q => stop);
        END_PROGRAM
        """.replace('\n', ''))
    sel = list(_find_calls(d, 'SEL'))
    assert len(sel) == 1 and [a['name'] for a in sel[0]] == [None, None, None]
    assert sel[0][0]['stmt'][2][0] == 'Un'
    assert len(list(_find_calls(d, 'MOVE'))) == 1
    picks = list(_find_calls(d, 'PICK'))
    assert [len(a) for a in picks] == [2, 2]
    assert picks[0][1]['stmt'][2][0] == 'Un'
    assert picks[1][0]['stmt'][2][0] == 'Bin'
    tm = list(_find_calls(d, 'TM'))
    assert len(tm) == 1 and tm[0][0]['name'] == 'Q' and tm[0][0]['inverted'] is True


def _unary_ops(node):
    if isinstance(node, list):
        if len(node) == 4 and node[0] == 'Un':
            yield node[2][0]
        for c in node:
            yield from _unary_ops(c)
    elif isinstance(node, dict):
        for c in node.values():
            yield from _unary_ops(c)


def test_not_is_not_negation():
    """`NOT x` is logical negation, `-x` arithmetic negation."""
    d = _dump_of(
        """
        PROGRAM p
        VAR b, c : BOOL; i : INT; END_VAR
        b := NOT b;
        i := -i;
        b := NOT (b AND c);
        i := -(i + 1);
        b := MOVE(NOT c);
        END_PROGRAM
        """.replace('\n', ''))
    assert list(_unary_ops(d)) == ['NOT', 'NEG', 'NOT', 'NEG', 'NOT']


def test_task_init_all_inputs():
    """`'(' ['SINGLE' ':=' data_source ','] ['INTERVAL' ':=' data_source ',']
    'PRIORITY' ':=' integer ')'` (IEC 61131-3, B.1.7)."""
    cfg = """
        PROGRAM prg VAR x : INT; END_VAR x := 1; END_PROGRAM
        CONFIGURATION c
          VAR_GLOBAL trig : BOOL; END_VAR
          RESOURCE r ON PLC
            TASK t1(SINGLE := trig, INTERVAL := T#20ms, PRIORITY := 2);
            TASK t2(SINGLE := trig, PRIORITY := 1);
            TASK t3(INTERVAL := T#5ms, PRIORITY := 0);
            TASK t4(PRIORITY := 3);
            PROGRAM i1 WITH t1 : prg;
          END_RESOURCE
        END_CONFIGURATION
        """.replace('\n', '')
    warns, rc = check_program(cfg)
    assert not _syntax_errors(warns), _syntax_errors(warns)
    with DumpManager('stdin.dump.json'):
        pass
    bad = cfg.replace('SINGLE := trig, INTERVAL := T#20ms', 'SINGLE trig, INTERVAL T#20ms')
    warns, rc = check_program(bad)
    e = _syntax_errors(warns)
    assert rc == 1 and len(e) == 1 and e[0].id == 'ParserError', warns
    with DumpManager('stdin.dump.json'):
        pass


def test_task_init_values_kept():
    d = _dump_of(
        """
        PROGRAM prg VAR x : INT; END_VAR x := 1; END_PROGRAM
        CONFIGURATION c
          VAR_GLOBAL trig : BOOL; END_VAR
          RESOURCE r ON PLC
            TASK t1(SINGLE := trig, INTERVAL := T#20ms, PRIORITY := 2);
            TASK t2(SINGLE := trig, PRIORITY := 1);
            TASK t3(INTERVAL := T#5ms, PRIORITY := 0);
            TASK t4(PRIORITY := 3);
            PROGRAM i1 WITH t1 : prg;
          END_RESOURCE
        END_CONFIGURATION
        """.replace('\n', ''))
    tasks = d['configurations'][0]['resources'][0]['tasks']
    got = {t['name']: (t['single'] and t['single'][1]['loc'][1]['name'],
                       t['interval'] and t['interval'][1][2]['ms'],
                       t['priority']) for t in tasks}
    assert got == {'T1': ('TRIG', 20.0, 2), 'T2': ('TRIG', None, 1),
                   'T3': (None, 5.0, 0), 'T4': (None, None, 3)}, got


def test_case_label_list_not_empty():
    """`case_list ::= case_list_element {',' case_list_element}`
    (IEC 61131-3, B.3.2.3): an arm has at least one label."""
    d = _dump_of(
        """
        PROGRAM p VAR x, y, a : INT; END_VAR
        CASE x OF
          1: y := a;
          -1: y := 2;
        END_CASE;
        END_PROGRAM
        """.replace('\n', ''))
    sels = list(_find_case_stmts(d))[0][3]
    assert [len(s['case']) for s in sels] == [1, 1]
    assert [len(s['body']) for s in sels] == [1, 1]
    for body in (': y := 1;', '1: y := a -1: y := 2;'):
        warns, rc = check_program(
            f'PROGRAM p VAR x, y, a : INT; END_VAR CASE x OF {body} END_CASE; END_PROGRAM')
        e = _syntax_errors(warns)
        assert rc == 1 and len(e) == 1 and e[0].id == 'ParserError', (body, warns)
        with DumpManager('stdin.dump.json'):
            pass


def test_string_length_in_parentheses():
    """`STRING(n)`, as CODESYS and TwinCAT write it, is `STRING[n]`."""
    p = """
        TYPE Name : STRING[20]; Rec : STRUCT tag : WSTRING[8]; END_STRUCT; END_TYPE
        FUNCTION label : STRING[16]
        VAR_INPUT prefix : STRING[4]; END_VAR
        label := prefix;
        END_FUNCTION
        PROGRAM p
        VAR s : STRING[10] := 'abc'; w : WSTRING[5] := "hi"; d : STRING; END_VAR
        s := label(prefix := 'x');
        END_PROGRAM
        """.replace('\n', '')
    paren = re.sub(r'\b(W?STRING)\[(\d+)\]', r'\1(\2)', p)
    assert 'STRING(20)' in paren and 'WSTRING(8)' in paren and 'STRING(16)' in paren
    assert _no_pos(_dump_of(p)) == _no_pos(_dump_of(paren))
    warns, rc = check_program(
        "PROGRAM p VAR s : STRING(2) := 'abc'; END_VAR s := 'x'; END_PROGRAM")
    assert [w.msg for w in filter_warns(warns, 'OutOfBounds')] == \
        ['Length of initialization string literal exceeds string length (3 > 2)']
    with DumpManager('stdin.dump.json'):
        pass


def test_configuration_several_global_sections():
    """CONSTANT and RETAIN qualify a whole VAR_GLOBAL section, so a
    configuration or resource with both kinds of globals needs several."""
    d = _dump_of(
        """
        PROGRAM prg VAR x : INT; END_VAR x := 1; END_PROGRAM
        CONFIGURATION plant
          VAR_GLOBAL CONSTANT limit : INT := 10; END_VAR
          VAR_GLOBAL run AT %QX0.0 : BOOL; level : INT; END_VAR
          VAR_GLOBAL RETAIN total : DINT; END_VAR
          RESOURCE cpu ON PLC
            VAR_GLOBAL CONSTANT period : TIME := T#10ms; END_VAR
            VAR_GLOBAL count : INT; END_VAR
            TASK cyclic(INTERVAL := period, PRIORITY := 1);
            PROGRAM main WITH cyclic : prg;
          END_RESOURCE
        END_CONFIGURATION
        """.replace('\n', ''))
    cfg = d['configurations'][0]
    names = lambda vs: sorted(v['var']['loc'][1]['name'] for v in vs)
    assert names(cfg['variables']) == ['LEVEL', 'LIMIT', 'RUN', 'TOTAL']
    assert names(cfg['resources'][0]['variables']) == ['COUNT', 'PERIOD']


def test_output_assignment_source():
    """In `fb(Q => v)` the output `Q` is sent to `v`."""
    d = _dump_of(
        """
        PROGRAM p
        VAR tm : TON; done, idle, go : BOOL; spent : TIME; END_VAR
        tm(IN := go, PT := T#1s, Q => done, ET => spent);
        tm(NOT Q => idle);
        END_PROGRAM
        """.replace('\n', ''))
    def sendto(a):
        e = a['stmt'][2]
        assert e[0] == 'Bin' and e[3] == ['SENDTO'], a
        return (a['name'], e[2][2]['loc'][1]['name'], e[4][2]['loc'][1]['name'], a['inverted'])
    calls = list(_find_calls(d, 'TM'))
    got = [sendto(a) for c in calls for a in c if a['stmt'][2][3] == ['SENDTO']]
    assert got == [('Q', 'Q', 'DONE', False), ('ET', 'ET', 'SPENT', False),
                   ('Q', 'Q', 'IDLE', True)], got
