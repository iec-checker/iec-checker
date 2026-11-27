open Core
module AU = IECCheckerCore.Ast_util
module S = IECCheckerCore.Syntax
module Env = IECCheckerCore.Env
module Warn = IECCheckerCore.Warn
module TI = IECCheckerCore.Tok_info

let str_len = function
  | S.STRING l  -> l
  | S.WSTRING l -> l
  | S.CHAR l    -> l
  | S.WCHAR l   -> l
  | _ -> assert false

let is_wide = function
  | S.WSTRING _ | S.WCHAR _ -> true
  | _ -> false

let literal_length ~wide s =
  let n = String.length s in
  let hex_at i len = i + len <= n && String.for_all (String.sub s ~pos:i ~len) ~f:Char.is_hex_digit in
  let rec go i acc =
    if i >= n then acc
    else if Char.equal s.[i] '$' then
      let skip = if wide && hex_at (i + 1) 4 then 5 else if hex_at (i + 1) 2 then 3 else 2 in
      go (i + skip) (acc + 1)
    else if Int.equal (Char.to_int s.[i] land 0xC0) 0x80 then go (i + 1) acc
    else go (i + 1) (acc + 1)
  in
  go 0 0

(** Compare length of declared string with initializer string size. *)
let check_str_init_size ty_init init_expr =
  let check_length init_str =
    let ty_len = str_len ty_init in
    let init_len = literal_length ~wide:(is_wide ty_init) init_str in
    if ty_len <> init_len then Some (ty_len, init_len) else None
  in
  match init_expr with
  | Some(e) ->
    begin
      match e with
      | S.ExprConstant(_,c) ->
        begin
          match c with
          | S.CString(_, str) -> check_length str
          | _ -> None
        end
      | _ -> None
    end
  | None -> None

(** Search for errors in initial value in declaration of a string type *)
let check_str_init_expr (ti : TI.t) ty_init init_expr =
  match check_str_init_size ty_init init_expr with
  | Some (len_decl, len_init) when (len_init > len_decl) ->
    let msg =
      Printf.sprintf
        "Length of initialization string literal exceeds string length (%d > %d)"
        len_init len_decl
    in
    let w = Warn.mk ti.linenr ti.col "OutOfBounds" msg in
    [ w ]
  | Some _ -> [] (* no violations *)
  | None -> []

(** Search for errors in subrange initialization *)
let check_subrange_init_val (ti : TI.t) ty_spec init_val =
  let (_, lb, ub) = ty_spec in
  if (init_val < lb) || (init_val > ub) then
    let msg =
      Printf.sprintf "Initial subrange value %d does not fit the specified range (%d .. %d)"
        init_val lb ub
    in let w = Warn.mk ti.linenr ti.col "OutOfBounds" msg in [ w ]
  else []

(** Search for errors in array initialization. *)
let check_array_init_val (ti : TI.t) ty_name subranges inval_opt =
  match inval_opt with
  | None -> (* no initializer list *) []
  | Some (inlist) -> begin
      let dimensions_capacity = AU.eval_array_capacity subranges in
      let diff = (List.length inlist) - dimensions_capacity in
      if diff > 0 then begin
        let m = Printf.sprintf
            "%s: Array initializer list exceeds capacity. Last %d values will be lost."
            ty_name diff
        in
        [(Warn.mk ti.linenr ti.col "OutOfBounds" m)]
      end
      else
        []
    end

let check_ty_decl ti ty_name = function
  | S.DTyDeclSingleElement (ty_spec, init_expr) ->
    begin
      match ty_spec with
      | S.DTySpecElementary ty_decl -> (check_str_init_expr ti ty_decl init_expr)
      | S.DTySpecSimple _ | S.DTySpecGeneric _ | S.DTySpecEnum _ -> []
    end
  | S.DTyDeclSubrange (ty_spec, init_val) -> check_subrange_init_val ti ty_spec init_val
  | S.DTyDeclEnumType _ -> []
  | S.DTyDeclArrayType (subranges, _, inval_opt) -> check_array_init_val ti ty_name subranges inval_opt
  | S.DTyDeclRefType _ -> []
  | S.DTyDeclStructType _ -> []

(** [check_var_decls pou] Searching for errors in variables declaration for the
    given [pou]. *)
let check_var_decls pou =
  AU.get_var_decls pou
  |> List.fold_left
    ~init:[]
    ~f:(fun acc var_decl -> begin
          let ty_decl_opt = S.VarDecl.get_ty_spec var_decl
          and var_name = S.VarDecl.get_var_name var_decl in
          match ty_decl_opt with
          | Some (ty_decl) -> acc @ (check_ty_decl (S.VarDecl.get_var_ti var_decl) var_name ty_decl)
          | None -> acc
        end)

let[@warning "-27"] run elements envs =
  List.fold_left elements
    ~f:(fun warns e ->
        let ws = match e with
          | S.IECType (_, ti, (ty_name, ty_spec)) -> check_ty_decl ti ty_name ty_spec
          | _ -> check_var_decls e
        in
        warns @ ws)
    ~init:[]
