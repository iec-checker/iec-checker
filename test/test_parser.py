"""Tests for parser and lexer."""
import sys
import os
import json
import re

sys.path.append(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../src"))
from python.core import run_checker, check_program, filter_warns  # noqa
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
