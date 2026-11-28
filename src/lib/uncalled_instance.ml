open Core
open IECCheckerCore

module S = Syntax
module AU = Ast_util

let root name = List.hd_exn (String.split name ~on:'.')

let is_local decl =
  match S.VarDecl.get_attr decl with
  | None | Some (S.VarDecl.Var _) | Some S.VarDecl.VarTemp -> true
  | _ -> false

let called elem =
  AU.get_pou_stmts elem
  |> List.filter_map ~f:(function
      | S.StmFuncCall (_, f, _) -> Some (root (S.Function.get_name f))
      | _ -> None)

let uses elem =
  let of_ref = function
    | S.RefSymVar sv -> [ (S.SymVar.get_name sv, `Whole) ]
    | _ -> []
  in
  let in_exprs =
    AU.get_pou_subexprs elem
    |> List.concat_map ~f:(function
        | S.ExprVariable (_, v) ->
          [ (S.VarUse.get_name v, if List.is_empty (S.VarUse.get_path v) then `Whole else `Field) ]
        | S.ExprConstant (_, S.CPointer (_, r)) -> of_ref r
        | _ -> [])
  and in_decls =
    AU.get_var_decls elem
    |> List.concat_map ~f:(fun d ->
        match S.VarDecl.get_ty_spec d with
        | Some (S.DTyDeclRefType (_, _, Some r)) -> of_ref r
        | _ -> [])
  in
  in_exprs @ in_decls

let check_elem types elem =
  let called = called elem and uses = uses elem in
  let used name kind = List.exists uses ~f:(fun (n, k) -> String.equal n name && Poly.equal k kind) in
  AU.get_var_decls elem
  |> List.filter ~f:(fun d -> is_local d && AU.has_type_in types d)
  |> List.filter_map ~f:(fun d ->
      let name = S.VarDecl.get_var_name d in
      if used name `Field && not (used name `Whole) && not (List.mem called name ~equal:String.equal) then
        let ti = S.VarDecl.get_var_ti d in
        let msg = Printf.sprintf "Function block instance %s is used but never called, so its outputs never change" name in
        Some (Warn.mk ti.linenr ti.col "UncalledInstance" msg)
      else None)

let do_check elems =
  let types = AU.fb_types elems in
  List.concat_map elems ~f:(check_elem types)

let detector : Detector.t = {
  id = "UncalledInstance";
  name = "Function block instance is used but never called";
  summary = "An FB instance that is never called keeps the initial values of its outputs.";
  doc_url = "https://iec-checker.github.io/docs/detectors/UncalledInstance";
  check = (fun (i : Detector.inputs) -> do_check i.elements);
}
