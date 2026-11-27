## Unreleased

- Support OCaml 5.1+ and Core 0.16+
- Migrate the project from `Core_kernel` to `Core`
- Driver: remove deprecated `Caml` module calls in the driver and lexer
- Driver: replace *nix-specific `Sys` functions with portable equivalents
- Driver: merge multiple input files via the command line
- Driver: force newlines after raising warnings
- Parser: fix errors after updating Menhir
- Build: simplify installation; add a top-level `Makefile`
- Build: build the project before running the test suite
- CI: update GitHub Actions to the latest packages
- CI: fix `dune not found` error when running `make test`
- Deps: bump `pytest` version to support Python 3.10
- Add `make doc` target and odoc package landing page (#24)
- Integrate `codespell` to the CI and fix errors found (#29)
- Uniform `Detector` API (#27)
- CLI option `--list-checks` (#28)
- Nuke `ZeroDiv` check
- Improve warnings output format (#30)
- Add `--no-color` CLI option (#30)
- Add configuration file (#44)
- lexer: Case-sensitive identifiers
- Add `PLCOpen-N1` (#15)
- Add `PLCOpen-N2` (#34)
- Add `PLCOpen-N4` (#35)
- Add `PLCOpen-N5` (#36)
- Add `PLCOpen-N6` (#37)
- Add `PLCOpen-N8` (#38)
- Add `PLCOpen-N9` (#39)
- Add `PLCOpen-CP16` (#47)
- Add `PLCOpen-CP26` (#52)
- Add `PLCOpen-L13` (#55)
- Add `PLCOpen-L22` (#56)
- Add `PLCOpen-N10` (#40)
- Parser/Lexer: show the problematic token and a source snippet for `ParserError`/`LexingError` (#58)
- Lexer: fix a bug where the `TRUE` boolean literal was silently lexed as `false`, corrupting CP2, CP8, CP25, N3 detectors
- `UnusedVariable`: fix a false positive where variables accessed only via struct-member syntax were reported as unused
- Parser: Allow whitespace only `fb_body`/`fc_body` (#62, @cangkui)
- Parser: Allow empty statement such as `;` (#64, @cangkui)
- Add Dockerfile (#69, @cangkui)
- Parser: Preserve literal types; add bit string literals (#66, @cangkui)
- Add `PLCOpen-N1` (#68, @cangkui)
- Lexer: accept spaces, non-ASCII characters and the `$$ $L $N $P $R $T` escapes in string literals
- Lexer: make control-flow keywords (`IF`, `THEN`, `CASE`, `FOR`, `RETURN`, ...) case-insensitive like all other keywords
- Parser: accept enumerated values (`A`, `E#A`) and named constants as `CASE` labels, and enumerated values as variable, struct and array element initializers
- Parser/Lexer: report the column where the offending token starts in `ParserError`/`LexingError`, matching the context caret
- Parser: accept multi-dimensional (`m[i, j]`) and chained (`m[i][j]`) subscripts in expressions, and chained subscripts on assignment targets
- Lexer: skip `{...}` pragmas anywhere whitespace is allowed; parse array init repetition as `n(v)` (n copies of `v`) and program configuration connections as `PROGRAM inst : prg (...)`
- Python wrapper: fix a deadlock in `run_checker` (used by `checker.py` and the tests) when the checker prints more than the OS pipe buffer
- Lexer: accept lowercase `t#`, `d#`, `lt#` and `ld#` duration and date literal prefixes
- Lexer: accept mixed-case `ms`, `us` and `ns` duration units (`T#5Ms`)
- Lexer: accept underlines between duration units (`T#5d_14h_12m_18s_3.5ms`) and identifiers starting with an underline and a digit (`_1abc`)
- Lexer: accept a lowercase exponent in real literals (`1.5e3`)
- Lexer: lex `TRUE`/`FALSE` and the `BOOL#` prefix case-insensitively; mixed-case spellings such as `tRuE` were silently parsed as variables
- Lexer: stop reserving `EQU`, which is not an IEC 61131-3 keyword, so it can be used as an identifier
- Lexer: skip a UTF-8 byte order mark; report unexpected non-ASCII characters whole, and escape invalid UTF-8 bytes (e.g. Latin-1 sources) in diagnostics so `-o json` output is always valid UTF-8
- Lexer: accept the `STRING#` literal prefix in any case
- Parser: accept subrange specifications in variable declarations (`r : INT (0..10) := 5;`)
- Lexer/Parser: lex `.` as a separate token instead of as a part of identifiers. Field access after a subscript (`a[i].f`, `m[i, j].f.g[k].h`), bit access (`w.%X0`, `w.5`) and whitespace or comments around `.` are accepted; field names that spell a keyword (`x.single`) stay identifiers. Malformed paths (`s..f`, `s.`), qualified names in declarations (`a.b : INT;`) and qualified formal parameter names (`f(s.x := 1)`) are rejected
- Core: represent a symbolic variable as a root identifier and a selector path (`.field`, `[i, j]`, `.5`, `.%X5`) instead of one dotted name. `VarUse.get_name` is the root; subscripts are recorded in expressions too. The JSON dump (version `0.2`) has `path` in place of `array_indexes`
- `PLCOPEN-CP17`: fix false positives for parameters that are read or written only through a field or an element (`inp.f`, `out[i].f := x`); report writes to a field of an input parameter
- `PLCOPEN-CP26`: count writes to a field or an element of a `VAR_EXTERNAL` variable
- `OutOfBounds`: check subscripts on reads (`x := a[9]`) and when a field access follows (`a[9].f`)
- Parser: accept nested array initializers (`[[1, 2], [3, 4]]`, `[2([1, 2])]`); the values are flattened in row-major order
- Parser: accept `NOT x` as a positional call argument (`SEL(NOT a, 1, 2)`); it was taken for the start of `NOT x => v`
- Parser: build `NOT x` as logical negation (`NOT`) instead of arithmetic negation (`NEG`); visible in the JSON dump
- Parser: accept `TASK t(SINGLE := s, INTERVAL := i, PRIORITY := p)`; the non-standard `SINGLE s, INTERVAL i` form without `:=` is rejected
- Parser: keep the `SINGLE`, `INTERVAL` and `PRIORITY` values of a `TASK` in the AST and the JSON dump; they were always `null`
- Parser: reject a `CASE` arm without labels (`: y := 1;`); a missing `;` before a negative label (`y := a` then `-1: ...`) is a syntax error instead of a silent `y := a - 1`
- `PLCOPEN-CP8`, `PLCOPEN-CP28`: report `<>` comparisons, which were never reported; report each comparison once instead of once per enclosing statement; find comparisons nested in other expressions and call arguments (`(r = 1.5) AND b`, `MOVE(t = T#1s)`)
- Parser: accept `STRING(n)` and `WSTRING(n)` as CODESYS and TwinCAT write the string length (standard: `STRING[n]`); listed on the Standard Extensions page
- Parser: accept several `VAR_GLOBAL` sections in a `CONFIGURATION` or `RESOURCE` (e.g. `VAR_GLOBAL CONSTANT` next to `VAR_GLOBAL`), as Beremiz generates them; listed on the Standard Extensions page
- Parser: build an output assignment `fb(Q => v)` as `Q SENDTO v`; it was `v SENDTO v`, so the output parameter was lost. `PLCOPEN-CP25` no longer compares the output parameter with a caller variable of the same name
- CLI: `-` reads the whole program from stdin; only its first line was read, so a multi-line program failed and the rest of the input was ignored. `--interactive` still reads one line
- Parser: accept empty `THEN`, `ELSIF`, `ELSE` branches, `CASE` arms and loop bodies (3rd edition `stmt_list`); in the CFG an empty body passes control on (an empty `REPEAT` body crashed the CFG builder)
- Parser: accept anonymous enumerations in variable declarations (`mode : (IDLE, RUN) := IDLE;`)
- Parser: accept `ARRAY` (with an initializer), subrange and anonymous enumeration types of STRUCT elements. In dumps, `struct_elem_ty` is now tagged: `Single`, `Subrange`, `Enum` or `Array`
- Parser: accept functions without a result type (3rd edition); their `return_ty` is `null` in dumps
- Lexer: an integer above 62 bits (`16#FFFFFFFFFFFFFFFF`) is a `LexingError`; it crashed the checker, or, for a based literal up to 63 bits, was silently wrapped to a negative value
- PLCOPEN-N5: a `VAR_EXTERNAL` declaration is no longer reported as a local shadowing its own global
- PLCOPEN-CP3: `VAR_IN_OUT` and `VAR_EXTERNAL` declarations are no longer reported; the standard allows no initializer there
- UnusedVariable: an FB instance that is only invoked (`c(inc := 2);`) and a variable read inside a nested call (`ABS(ABS(x))`) are no longer reported as unused
- PLCOPEN-CP4: two variables at the same address are reported; addresses of different memory areas (`%IW0`, `%QW1`) are no longer compared
- Warnings name direct variables in the standard order, location prefix first: `%IW0`, was `%WI0` (PLCOPEN-CP1, CP4, N1)
- PLCOPEN-CP9: warnings are reported at the POU name and name the POU (`Code of program MAIN is too complex (...)`); they were all at `0:0`. Dumps of programs carry the program name's `ti`
- CLI: `-i xml` no longer prints the source reconstructed from the XML to stdout, which made `-o json` output invalid JSON
- Lexer: accept `/* ... */` comments (3rd edition); they nest like `(* ... *)`
- Parser: `MOD`, `AND`, `OR` and `XOR` can be called as functions (`MOD(i + 1, 128)`), as the standard functions of tables 24 and 26
- Parser: direct variables can be read in expressions (`r := %IW3 + 1;`, `IF %IX0.0 THEN`); only assignments to them parsed. A misplaced direct variable is named in the parser error, which said `unexpected token end of input` and pointed after the address
- Parser: `REF(x)`, `NULL` and the `r^` dereference can be used in expressions, and `r^ := e` assigns through a reference (3rd edition); they worked only with `?=`. UnusedVariable counts `REF(x)`, also in a `REF_TO` initializer, as a use of `x`
- PLCOPEN-CP8: `=` and `<>` are reported when either side is a variable declared `REAL` or `LREAL` in the POU (`x = y`, `x <> x`); only a REAL literal triggered it
- Warnings are reported at the first character of the token they are about; the column was its last character (`counter` at 3-9 was reported at `:9`), while parser errors already used the first. A signed or typed literal (`-3`, `INT#5`, `T#1h2m`), a qualified enumeration value (`Mode#STOP`), `REF(x)` and a unary expression (`NOT x`, `-x`) are located at their first token. `col` of every `ti` in dumps changes the same way
- PLCOPEN-CP8, PLCOPEN-CP28: reported at the `=` or `<>` operator, was the left operand (`IF speed = 1.5` at `:10`, was `:4`); so is PLCOPEN-CP25 on a comparison with `=` or `<>`. In dumps the `ti` of such a `Bin` expression is at the operator
- PLCOPEN-CP9: McCabe complexity is 1 plus each `IF`, `ELSIF`, `CASE` selection, `FOR`, `WHILE` and `REPEAT`. It counted every control-flow edge twice and every call with arguments as a loop, so straight-line code scored -1 and ten `IF`s scored 36, not 11
- PLCOPEN-CP3: instances of standard function blocks (`TON`, `CTU`, `R_TRIG`, ...) and of function blocks and classes declared in the input are no longer reported; an instance takes the initial values its type declares
- Warnings about the name of a `TYPE`, `CLASS`, `INTERFACE` or `PROGRAM` (PLCOPEN-N4, N6, N8, N9, N10; CP9 for classes) and OutOfBounds warnings on declaration initializers are reported at the name; they were at `0:0`
- PLCOPEN-CP9: the statement count counts each statement once, and each `ELSIF` branch; it also counted the conditions of `IF`/`ELSIF`/`WHILE`, call arguments and calls nested in expressions, and missed `FOR` and `CASE`. The PLCopen example `CHARCURVE` has 18 statements, as the guideline says; it was 27

## 0.4.0 (2022-02-26)

### New PLCOpen rules

- Add `PLCOPEN-CP1` (access to a member shall be by name)
- Rename the `UnreachableCode` check to PLCOPEN-CP2 (all code shall be used)
- Add `PLCOPEN-CP3` (variables shall be initialized before being used); fix a
  false positive on direct variables
- Add `PLCOPEN-CP4` (direct addressing should not overlap)
- Add `PLCOPEN-CP6` (avoid external variables in functions, function blocks
  and classes)
- Add `PLCOPEN-CP8` (floating-point comparison shall not be equality or
  inequality)
- Add `PLCOPEN-CP25` (data type conversion should be explicit), along with the
  variable declaration analysis it requires
- Add `PLCOPEN-CP28` (time and physical measures shall not be compared for
  equality or inequality)
- Add `PLCOPEN-L10` (avoid `CONTINUE` and `EXIT` instructions)

### New input format

- Initial support for the SEL XML input format; allow the `<Type>` XML tag
  to be used instead of `<POUKind>`

### Language / parser support

- Initial support for OOP features of the ST language
- Lexer: allow time literals in uppercase
- Lexer: allow identifiers starting with an underscore
- Lexer: workaround for struct access
- Parser: switch to the new Menhir style throughout
- Parser: allow direct-variable assignment
- Parser: make the semicolon after a type declaration optional
- Parser: allow skipping semicolons after statements
- Parser: support empty variable sections
- Parser: finish access and located variables
- Parser: allow arrays inside `IF` statements
- Parser: fix a parser error on `v16 AT %MW12:INT`

### Driver / CLI

- Recursively traverse nested input directories
- Get rid of magic numbers in return codes
- Define config options for selecting which checks are executed
- Add a Python argument to specify the OCaml binary (#7)
- Fix a crash on non-existent input files
- Fix the case where the checker is run with stdin input

### Bug fixes

- plcopen.xml: fix an XML parser error
- ast_util: fix `get_stmts` for `FOR` loops

### Build / CI

- dune: force the previous Menhir version to avoid regressions
- dune: generate a correct opam file with dependencies
- dune: fix the license metadata
- Remove an unused dependency
- github-actions: update the OCaml version and `avsm/setup-ocaml`
- github-actions: run unit tests on every PR
- ci: fix `pytest`

### Refactor / cleanup

- python: fix formatting and typing warnings
- driver: fix formatting and deprecation warnings
- warn_output: simplify code
- parser: remove dead code

## 0.3.0 (2020-10-27)

- Add the ability to build for Windows; update dependencies
- Fix compatibility with the latest Menhir
- Fix codespell typos across the source tree
- CI: update GitHub Actions configuration; install the `xmlm` dependency

## 0.2.0 (2020-09-05)

- Initial support for the PLCOpen XML input format, including derived types,
  pointers, xhtml tags inside source code, and a workaround for unimplemented
  configurations
- Initial implementation of the PLCOPEN-CP9 rule (limit POU complexity), with
  support for both McCabe complexity and statement count; raise the McCabe
  threshold to a more practical value
- Initial data-flow analysis for arrays, including out-of-bound detection in
  declaration analysis
- Detect declaration errors inside POU local variables, not just globals
- Add `VarUse` module to track additional variable-usage info; record array
  subscription info on `SymVar.t`
- Track variable initialization info in the AST; refactor the AST to separate
  the specification of derived types
- Parser: support reference assign statements (`?=`)
- Parser: allow empty POU bodies
- Parser: support direct variables as task data sources
- Parser: support arrays of all constant expression types
- Parser: simplify `func_call`
- Rewrite the CFG structure
- Build: add a `release` env to dune; add `xmlm` as a dependency
- CI: add a workaround for Menhir regressions

## 0.1.0 (2020-05-11)

- Initial release.
