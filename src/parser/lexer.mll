(* Based on IEC61131-3 3rd edition: ANNEX A - Formal specification of language elements *)
{
  open Parser
  open Lexing
  open Core

  open IECCheckerCore

  exception LexingError of string

  let incr_linenum lexbuf =
    let pos = lexbuf.Lexing.lex_curr_p in
      lexbuf.Lexing.lex_curr_p <- { pos with
      Lexing.pos_lnum = pos.Lexing.pos_lnum + 1;
      Lexing.pos_bol = pos.Lexing.pos_cnum;
    }

  (* Hack around ocamllex to emulate the yyless() of flex. The semantic
     is not exactly the same than yyless(), so I use yyback() instead.
     http://my.safaribooksonline.com/book/programming/flex/9780596805418/a-reference-for-flex-specifications/yyless *)
  let yyback n lexbuf =
    lexbuf.Lexing.lex_curr_pos <- lexbuf.Lexing.lex_curr_pos - n;
    let currp = lexbuf.Lexing.lex_curr_p in
    lexbuf.Lexing.lex_curr_p <- { currp with
      Lexing.pos_cnum = currp.Lexing.pos_cnum - n;
    }

  (* Keyword tables are necessary to get rid of transition table overflow errors.
     See: http://caml.inria.fr/pub/docs/manual-ocaml-4.00/manual026.html#toc111 *)
  (* This keyword table is also required to handle case-insensitive syntax of IEC 61131-3. *)
  let keywords_table = Stdlib.Hashtbl.create 97
  let () =
    Stdlib.List.iter (fun (x,y) -> Stdlib.Hashtbl.add keywords_table x y)
      [
  (* {{{ Generic data types *)
      "any",                T_ANY;
      "any_derived",        T_ANY_DERIVED;
      "any_elementary",     T_ANY_ELEMENTARY;
      "any_magnitude",      T_ANY_MAGNITUDE;
      "any_num",            T_ANY_NUM;
      "any_real",           T_ANY_REAL;
      "any_int",            T_ANY_INT;
      "any_bit",            T_ANY_BIT;
      "any_string",         T_ANY_STRING;
      "any_date",           T_ANY_DATE;
  (* }}} *)
  (* {{{ Operators *)
      "xor",                T_XOR;
      "or",                 T_OR;
      "and",                T_AND;
  (* }}} *)
  (* {{{ Elementary data types *)
      "ltod",               T_LTOD;
      "tod",                T_TOD;
      "ltime_of_day",       T_LTIME_OF_DAY;
      "time_of_day",        T_TIME_OF_DAY;
      "ldt",                T_LDT;
      "dt",                 T_DT;
      "ldate_and_time",     T_LDATE_AND_TIME;
      "date_and_time",      T_DATE_AND_TIME;
      "ldate",              T_LDATE;
      "date",               T_DATE;
      "ltime",              T_LTIME;
      "time",               T_TIME;
      "bool",               T_BOOL;
      "wchar",              T_WCHAR;
      "char",               T_CHAR;
      "string",             T_STRING;
      "wstring",            T_WSTRING;
      "ulint",              T_ULINT;
      "udint",              T_UDINT;
      "uint",               T_UINT;
      "usint",              T_USINT;
      "lint",               T_LINT;
      "dint",               T_DINT;
      "int",                T_INT;
      "sint",               T_SINT;
      "real",               T_REAL;
      "lreal",              T_LREAL;
      "lword",              T_LWORD;
      "dword",              T_DWORD;
      "word",               T_WORD;
      "byte",               T_BYTE;
      "sint",               T_SINT;
  (* }}} *)
  (* {{{ Keywords *)
      "null",               T_NULL;
      "ref",                T_REF;
      "ref_to",             T_REF_TO;
      "end_type",           T_END_TYPE;
      "type",               T_TYPE;
      "end_var",            T_END_VAR;
      "var_global",         T_VAR_GLOBAL;
      "var_config",         T_VAR_CONFIG;
      "var_access",         T_VAR_ACCESS;
      "var_external",       T_VAR_EXTERNAL;
      "var_temp",           T_VAR_TEMP;
      "var_in_out",         T_VAR_IN_OUT;
      "var_output",         T_VAR_OUTPUT;
      "var_input",          T_VAR_INPUT;
      "var",                T_VAR;
      "constant",           T_CONSTANT;
      "task",               T_TASK;
      "struct",             T_STRUCT;
      "end_struct",         T_END_STRUCT;
      "overlap",            T_OVERLAP;
      "array",              T_ARRAY;
      "read_only",          T_READ_ONLY;
      "read_write",         T_READ_WRITE;
      "priority",           T_PRIORITY;
      "interval",           T_INTERVAL;
      "single",             T_SINGLE;
      "end_resource",       T_END_RESOURCE;
      "on",                 T_ON;
      "resource",           T_RESOURCE;
      "end_configuration",  T_END_CONFIGURATION;
      "configuration",      T_CONFIGURATION;
      "end_function_block", T_END_FUNCTION_BLOCK;
      "function_block",     T_FUNCTION_BLOCK;
      "end_function",       T_END_FUNCTION;
      "function",           T_FUNCTION;
      "end_program",        T_END_PROGRAM;
      "program",            T_PROGRAM;
      "class",              T_CLASS;
      "end_class",          T_END_CLASS;
      "final",              T_FINAL;
      "abstract",           T_ABSTRACT;
      "extends",            T_EXTENDS;
      "implements",         T_IMPLEMENTS;
      "interface",          T_INTERFACE;
      "end_interface",      T_END_INTERFACE;
      "method",             T_METHOD;
      "end_method",         T_END_METHOD;
      "public",             T_PUBLIC;
      "protected",          T_PROTECTED;
      "private",            T_PRIVATE;
      "internal",           T_INTERNAL;
      "override",           T_OVERRIDE;
      "non_retain",         T_NON_RETAIN;
      "retain",             T_RETAIN;
      "with",               T_WITH;
      "at",                 T_AT;
      "mod",                T_MOD;
      "not",                T_NOT;
  (* }}} *)
      ]

  let ctrl_keywords_table = Stdlib.Hashtbl.create 31
  let () =
    Stdlib.List.iter (fun (x,y) -> Stdlib.Hashtbl.add ctrl_keywords_table x y)
      [
      "if",         (fun ti -> T_IF(ti));
      "then",       (fun ti -> T_THEN(ti));
      "elsif",      (fun ti -> T_ELSIF(ti));
      "else",       (fun ti -> T_ELSE(ti));
      "end_if",     (fun ti -> T_END_IF(ti));
      "case",       (fun ti -> T_CASE(ti));
      "of",         (fun ti -> T_OF(ti));
      "end_case",   (fun ti -> T_END_CASE(ti));
      "for",        (fun ti -> T_FOR(ti));
      "to",         (fun ti -> T_TO(ti));
      "by",         (fun ti -> T_BY(ti));
      "do",         (fun ti -> T_DO(ti));
      "end_for",    (fun ti -> T_END_FOR(ti));
      "while",      (fun ti -> T_WHILE(ti));
      "end_while",  (fun ti -> T_END_WHILE(ti));
      "repeat",     (fun ti -> T_REPEAT(ti));
      "end_repeat", (fun ti -> T_END_REPEAT(ti));
      "until",      (fun ti -> T_UNTIL(ti));
      "exit",       (fun ti -> T_EXIT(ti));
      "continue",   (fun ti -> T_CONTINUE(ti));
      "return",     (fun ti -> T_RETURN(ti));
      ]
}

let string_prefix = ['S' 's'] ['T' 't'] ['R' 'r'] ['I' 'i'] ['N' 'n'] ['G' 'g'] '#'
let common_char_value = [' ' '!' '#' '%' '&' '('-'@' 'A'-'Z' '['-'`' 'a'-'z' '{'-'~' '\128'-'\255']
let common_char_escape = '$' ['$' 'L' 'N' 'P' 'R' 'T' 'l' 'n' 'p' 'r' 't']

let whitespace = ['\r' '\t' ' ']

(* Letters, digits and identifiers *)
let letter	    = ['A'-'Z' 'a'-'z']
let digit		= ['0'-'9']
let octal_digit	= ['0'-'7']
let hex_digit   = digit | ['A'-'F'] | ['a'-'f']

let integer = digit+(('_')?digit)*
let bit = ['0' '1']
let binary_integer = '2' '#' (('_')?bit)+
let octal_integer = '8' '#' (('_')?octal_digit)+
let hex_integer = '1' '6' '#' (('_')?hex_digit)+

let kw_false = ['F' 'f'] ['A' 'a'] ['L' 'l'] ['S' 's'] ['E' 'e']
let kw_true = ['T' 't'] ['R' 'r'] ['U' 'u'] ['E' 'e']
let bool_prefix = ['B' 'b'] ['O' 'o'] ['O' 'o'] ['L' 'l'] '#'
let bool_false = kw_false | bool_prefix (kw_false | '0')
let bool_true = kw_true | bool_prefix (kw_true | '1')

let exponent = ['E' 'e'] (['+' '-'])? integer

(* The correct definition for real would be:
   let real = integer '.' integer (exponent)?

   But there is also definition of fix_point in Table 8 / Table 9:
   integer '.' integer

   This means that parser should be able to figure out what kind of token we
   have based on the current context.
 *)
let real = integer '.' integer exponent

let fix_point = integer '.' integer

(* Time literals *)
let fix_point_d = (integer | (integer '.' integer)) ('d' | 'D')
let fix_point_h = (integer | (integer '.' integer)) ('h' | 'H')
let fix_point_m = (integer | (integer '.' integer)) ('m' | 'M')
let fix_point_s = (integer | (integer '.' integer)) ('s' | 'S')
let fix_point_ms = (integer | (integer '.' integer)) (['m' 'M'] ['s' 'S'])
let fix_point_us = (integer | (integer '.' integer)) (['u' 'U'] ['s' 'S'])
let fix_point_ns = (integer | (integer '.' integer)) (['n' 'N'] ['s' 'S'])

let label = ('_' (letter | digit) | letter) ['A'-'Z' 'a'-'z' '0'-'9' '_']*

rule initial tokinfo =
  parse
  (* {{{ Common *)
  | whitespace+          { initial tokinfo lexbuf }
  | "\239\187\191"
  {
    let p = lexbuf.lex_start_p in
    if p.pos_cnum = p.pos_bol then
      lexbuf.lex_curr_p <- { lexbuf.lex_curr_p with pos_bol = lexbuf.lex_curr_p.pos_cnum };
    initial tokinfo lexbuf
  }
  | '\n'                 { incr_linenum lexbuf; initial tokinfo lexbuf }
  | ":="                 { T_ASSIGN }
  | "?="                 { T_ASSIGN_REF }
  | "=>"                 { T_SENDTO }
  | "."                  { T_DOT }
  | "^"                  { T_DEREF }
  | ">="                 { T_GE }
  | "<="                 { T_LE }
  | ">"                  { T_GT }
  | "-"                  { T_MINUS }
  | "+"                  { T_PLUS }
  | "<"                  { T_LT }
  | "<>"                 { T_NEQ }
  | "="                  { T_EQ }
  | "/"                  { T_DIV }
  | "**"                 { T_POW }
  | "*"                  { T_MUL }
  | ".."                 { T_RANGE }
  | "{"                  { pragma (initial tokinfo) 1 lexbuf }
  | "["                  { T_LBRACK }
  | "]"                  { T_RBRACK }
  | "("                  { T_LPAREN }
  | ")"                  { T_RPAREN }
  | ":"                  { T_COLON }
  | ","                  { T_COMMA }
  | ";"                  { T_SEMICOLON }
  | "#"                  { T_SHARP }
  (* }}} *)

  (* {{{ Helpers for datetime types *)
  | ['T' 't'] '#'                { T_TSHARP }
  | ['L' 'l'] ['T' 't'] '#'      { T_LTSHARP }
  | ['D' 'd'] '#'                { T_DSHARP }
  | ['L' 'l'] ['D' 'd'] '#'      { T_LDSHARP }
  (* }}} *)

  (* {{{ ST operators *)
  | "&"      { T_AND }
  (* }}} *)

  (* {{{ Boolean literals *)
  | bool_false
  {
      (* Printf.printf "BOOL_VALUE: false\n"; *)
      let ti = tokinfo lexbuf in
      T_BOOL_VALUE(false, ti)
  }
  | bool_true
  {
      (* Printf.printf "BOOL_VALUE: true\n"; *)
      let ti = tokinfo lexbuf in
      T_BOOL_VALUE(true, ti)
  }
  (* }}} *)

  (* {{{ Case-insensitive lexing of identifiers and reserved keywords. *)
  | label as v
  {
    match Stdlib.Hashtbl.find_opt ctrl_keywords_table (String.lowercase v) with
    | Some f -> f (tokinfo lexbuf)
    | None ->
    try
      let keyword = Stdlib.Hashtbl.find keywords_table (String.lowercase v) in
      (* Printf.printf "KEYWORD: %s\n" v; *)
      keyword
      with Not_found -> begin
        (* Printf.printf "ID: %s\n" v; *)
        T_IDENTIFIER(String.uppercase(v), Tok_info.create_with_raw lexbuf v)
      end
  }
  (* }}} *)

  (* {{{ Integer literals *)
  | integer as i
  {
      let v = int_of_string i in
      (* Printf.printf "INTEGER: %s -> %d\n" i v; *)
      let ti = tokinfo lexbuf in
      T_INTEGER(v, ti)
  }
  | binary_integer as i
  {
      let v = int_of_string ("0b" ^ (String.slice i 2 (String.length i))) in
      (* Printf.printf "BINARY_INTEGER: %s -> %d\n" i v; *)
      let ti = tokinfo lexbuf in
      T_BINARY_INTEGER(v, ti)
  }
  | octal_integer as i
  {
      let v = int_of_string ("0o" ^ (String.slice i 2 (String.length i))) in
      (* Printf.printf "OCTAL_INTEGER: %s -> %d\n" i v; *)
      let ti = tokinfo lexbuf in
      T_BINARY_INTEGER(v, ti)
  }
  | hex_integer as i
  {
      let v = int_of_string ("0x" ^ (String.slice i 3 (String.length i))) in
      (* Printf.printf "HEX_INTEGER: %s -> %d\n" i v; *)
      let ti = tokinfo lexbuf in
      T_BINARY_INTEGER(v, ti)
  }
  (* }}} *)

  (* {{{ Real literal *)
  | real as r
  {
      let v = float_of_string r in
      (* Printf.printf "REAL_VALUE: %s -> %f\n" r v; *)
      let ti = tokinfo lexbuf in
      T_REAL_VALUE(v, ti)
  }
  (* }}} *)

  (* {{{ Fixed point literal *)
  | fix_point as fp
  {
      (* Printf.printf "FIX_POINT_VALUE: %s\n" fp; *)
      let ti = tokinfo lexbuf in
      T_FIX_POINT_VALUE(fp, ti)
  }
  (* }}} *)

  (* {{{ Time intervals *)
  (* Units of an integer value may be followed by '_' and the next unit. The
     digit after '_' is matched only to check it is there and pushed back. *)
  | (integer as i) ['d' 'D'] '_' digit
  { yyback 1 lexbuf; T_TIME_INTERVAL_D(float_of_string i, tokinfo lexbuf) }
  | (integer as i) ['h' 'H'] '_' digit
  { yyback 1 lexbuf; T_TIME_INTERVAL_H(float_of_string i, tokinfo lexbuf) }
  | (integer as i) ['m' 'M'] '_' digit
  { yyback 1 lexbuf; T_TIME_INTERVAL_M(float_of_string i, tokinfo lexbuf) }
  | (integer as i) ['s' 'S'] '_' digit
  { yyback 1 lexbuf; T_TIME_INTERVAL_S(float_of_string i, tokinfo lexbuf) }
  | (integer as i) ['m' 'M'] ['s' 'S'] '_' digit
  { yyback 1 lexbuf; T_TIME_INTERVAL_MS(float_of_string i, tokinfo lexbuf) }
  | (integer as i) ['u' 'U'] ['s' 'S'] '_' digit
  { yyback 1 lexbuf; T_TIME_INTERVAL_US(float_of_string i, tokinfo lexbuf) }
  | fix_point_d as v
  {
      let vf = float_of_string (String.slice v 0 ((String.length v) - 1)) in
      (* Printf.printf "TIME_D: %s -> %f\n" v vf; *)
      let ti = tokinfo lexbuf in
      T_TIME_INTERVAL_D(vf, ti)
  }
  | fix_point_h as v
  {
      let vf = float_of_string (String.slice v 0 ((String.length v) - 1)) in
      (* Printf.printf "TIME_H: %s -> %f\n" v vf; *)
      let ti = tokinfo lexbuf in
      T_TIME_INTERVAL_H(vf, ti)
  }
  | fix_point_m as v
  {
      let vf = float_of_string (String.slice v 0 ((String.length v) - 1)) in
      (* Printf.printf "TIME_M: %s -> %f\n" v vf; *)
      let ti = tokinfo lexbuf in
      T_TIME_INTERVAL_M(vf, ti)
  }
  | fix_point_s as v
  {
      let vf = float_of_string (String.slice v 0 ((String.length v) - 1)) in
      (* Printf.printf "TIME_S: %s -> %f\n" v vf; *)
      let ti = tokinfo lexbuf in
      T_TIME_INTERVAL_S(vf, ti)
  }
  | fix_point_ms as v
  {
      let vf = float_of_string (String.slice v 0 ((String.length v) - 2)) in
      (* Printf.printf "TIME_MS: %s -> %f\n" v vf; *)
      let ti = tokinfo lexbuf in
      T_TIME_INTERVAL_MS(vf, ti)
  }
  | fix_point_us as v
  {
      let vf = float_of_string (String.slice v 0 ((String.length v) - 2)) in
      (* Printf.printf "TIME_US: %s -> %f\n" v vf; *)
      let ti = tokinfo lexbuf in
      T_TIME_INTERVAL_US(vf, ti)
  }
  | fix_point_ns as v
  {
      let vf = float_of_string (String.slice v 0 ((String.length v) - 2)) in
      (* Printf.printf "TIME_NS: %s -> %f\n" v vf; *)
      let ti = tokinfo lexbuf in
      T_TIME_INTERVAL_NS(vf, ti)
  }
  (* }}} *)

  (* {{{ Misc. *)
  | "(*"             { comment (initial tokinfo) 1 lexbuf }
  | "//"             { singleline_comment (initial tokinfo) lexbuf }
  | "%"              { let ti = tokinfo lexbuf in direct_variable (Syntax.DirVar.create ti) ti lexbuf }
  | string_prefix '\'' { let ti = tokinfo lexbuf in sstring_literal (Buffer.create 19) ti lexbuf }
  | '\''             { let ti = tokinfo lexbuf in sstring_literal (Buffer.create 19) ti lexbuf }
  | string_prefix '"'  { let ti = tokinfo lexbuf in dstring_literal (Buffer.create 19) ti lexbuf }
  | '"'              { let ti = tokinfo lexbuf in dstring_literal (Buffer.create 19) ti lexbuf }
  | eof              { T_EOF }
  | ['\192'-'\255'] ['\128'-'\191']* as u { raise (LexingError ("Unexpected char: " ^ u)) }
  | _                { raise (LexingError ("Unexpected char: " ^ Lexing.lexeme lexbuf)) }
  (* }}} *)

  (* {{{ Token following T_DOT: field names are never keywords, digits are a bit number *)
and field tokinfo = parse
  | whitespace+ { field tokinfo lexbuf }
  | '\n'        { incr_linenum lexbuf; field tokinfo lexbuf }
  | "(*"        { comment (field tokinfo) 1 lexbuf }
  | "//"        { singleline_comment (field tokinfo) lexbuf }
  | "{"         { pragma (field tokinfo) 1 lexbuf }
  | label as v  { T_IDENTIFIER(String.uppercase v, Tok_info.create_with_raw lexbuf v) }
  | digit+ as v { T_INTEGER(int_of_string v, Tok_info.create_with_raw lexbuf v) }
  | ""          { initial tokinfo lexbuf }
  (* }}} *)

  (* {{{ String literals *)
and sstring_literal buf ti = parse
  | '"' { Buffer.add_char buf '"'; sstring_literal buf ti lexbuf }
  | common_char_value+ | common_char_escape | '$' '\'' | '$' hex_digit hex_digit
  {
    Buffer.add_string buf (Lexing.lexeme lexbuf);
    sstring_literal buf ti lexbuf
  }
  | '\''
  {
    (* Printf.printf "SSTRING: %s" (Buffer.contents buf); *)
    T_SSTRING_LITERAL((Buffer.contents buf), ti)
  }
  | eof { raise (LexingError "String is not terminated") }
  | _   { raise (LexingError ("Illegal string character: " ^ (Lexing.lexeme lexbuf))) }

and dstring_literal buf ti = parse
  | '\'' { Buffer.add_char buf '\''; dstring_literal buf ti lexbuf }
  | common_char_value+ | common_char_escape | '$' '"' | '$' hex_digit hex_digit hex_digit hex_digit
  {
    Buffer.add_string buf (Lexing.lexeme lexbuf);
    dstring_literal buf ti lexbuf
  }
  | '"'
  {
    (* Printf.printf "DSTRING: %s" (Buffer.contents buf); *)
    T_DSTRING_LITERAL((Buffer.contents buf), ti)
  }
  | eof { raise (LexingError "String is not terminated") }
  | _   { raise (LexingError ("Illegal string character: " ^ (Lexing.lexeme lexbuf))) }
  (* }}}*)

  (* {{{ Direct variables *)
and direct_variable var ti = parse
  | "I" | "Q" | "M"
  {
    match (Syntax.DirVar.get_loc var) with
    (* Can't set twice *)
    | Some _ -> raise (LexingError ("Invalid direct variable location: " ^ (Lexing.lexeme lexbuf)))
    | None   -> (
      let loc_opt = Syntax.DirVar.location_of_string (Lexing.lexeme lexbuf) in
      match loc_opt with
      | None      -> raise (LexingError ("Invalid direct variable location: " ^ (Lexing.lexeme lexbuf)))
      | Some(loc) -> (
        let var = Syntax.DirVar.set_loc var loc in
        direct_variable var ti lexbuf
      )
    )
  }
  | "X" | "B" | "W" | "D" | "L"
  {
    match (Syntax.DirVar.get_size var) with
    (* Can't set twice *)
    | Some _ -> raise (LexingError ("Invalid direct variable size: " ^ (Lexing.lexeme lexbuf)))
    | None   -> (
      let size_opt = Syntax.DirVar.size_of_string (Lexing.lexeme lexbuf) in
      match size_opt with
      | None     -> raise (LexingError ("Invalid direct variable size: " ^ (Lexing.lexeme lexbuf)))
      | Some(sz) -> (
        let var = Syntax.DirVar.set_size var sz in
        direct_variable var ti lexbuf
      )
    )
  }
  | digit+
  {
    (* First digit in the path *)
    let path_value = int_of_string (Lexing.lexeme lexbuf) in
    let var = Syntax.DirVar.set_path var [path_value] in
    direct_variable var ti lexbuf
  }
  | '.' digit+
  {
    let str_val = (Lexing.lexeme lexbuf) in
    let new_item = int_of_string (String.slice str_val 1 (String.length str_val)) in
    let path_value = Syntax.DirVar.get_path var in
    if List.is_empty path_value then
      (* something like '%QD.1' *)
      raise (LexingError ("Invalid direct variable path: " ^ (Lexing.lexeme lexbuf)))
    else
      let new_path = path_value @ [new_item] in
      let var = Syntax.DirVar.set_path var new_path in
      direct_variable var ti lexbuf
  }
  | '*'
  {
    if (Syntax.DirVar.get_is_partly_located var) then
      (* Can't set twice *)
      raise (LexingError ("Invalid direct variable definition: " ^ (Lexing.lexeme lexbuf)))
    else
      let var = Syntax.DirVar.set_is_partly_located var true in
      direct_variable var ti lexbuf
  }
  | eof { T_EOF }
  | _ as c
  {
    (* Printf.printf "DIR_VAR=%s\n" (Syntax.DirVar.to_string var); *)
    yyback (String.length (Lexing.lexeme lexbuf)) lexbuf;
    T_DIR_VAR(var)
  }
  (* }}}*)

  (* {{{ Comments *)
and comment k depth = parse
  | '(' '*' {comment k (depth + 1) lexbuf}
  | '*' ')' {if depth = 1 then k lexbuf else comment k (depth-1) lexbuf}
  | '\n' {let () = new_line lexbuf in comment k depth lexbuf}
  | _ {comment k depth lexbuf}
  | eof { raise (LexingError ("Comment is not terminated")) }
and singleline_comment k = parse
  | '\n'   { incr_linenum lexbuf; k lexbuf }
  | eof    { T_EOF }
  | _      { singleline_comment k lexbuf }
  (* }}} *)

  (* {{{ Pragmas *)
and pragma k depth = parse
  | '{'  { pragma k (depth + 1) lexbuf }
  | '}'  { if depth = 1 then k lexbuf else pragma k (depth - 1) lexbuf }
  | '\n' { incr_linenum lexbuf; pragma k depth lexbuf }
  | eof  { raise (LexingError "Pragma is not terminated") }
  | _    { pragma k depth lexbuf }
  (* }}} *)

{
  let token tokinfo =
    let d = ref false in
    fun lexbuf ->
      let t = if !d then field tokinfo lexbuf else initial tokinfo lexbuf in
      d := (match t with T_DOT -> true | _ -> false);
      t

  let read_file parser (filename: string) =
  try
    let fh = In_channel.create filename in
    let lex = Lexing.from_channel fh in
    lex.Lexing.lex_curr_p <- {lex.Lexing.lex_curr_p with Lexing.pos_fname = filename};
    try
      let terms = parser lex in
      In_channel.close fh;
      terms
    with err ->
      (* Close the file in case of any parsing errors. *)
      In_channel.close fh;
      raise err
  with err ->
    (* Any errors when opening or closing a file are fatal. *)
    Printf.printf "Error while reading file\n" ;
    raise err
}

(* vim: set foldmethod=marker foldlevel=0 foldenable sw=2 tw=120 : *)
