open Core
module AU = IECCheckerCore.Ast_util
module S = IECCheckerCore.Syntax
module Warn = IECCheckerCore.Warn

let check_pou elem =
  let module StringSet = Set.Make(String) in

  let get_decl_var_names () =
    AU.get_var_decls elem
    |> List.map ~f:(fun vardecl -> S.VarDecl.get_var_name vardecl)
  in

  let get_use_var_names () =
    let exprs = AU.get_pou_subexprs elem in
    let vars =
      List.filter_map exprs ~f:(function
          | S.ExprVariable (_, v) -> Some (S.VarUse.get_name v)
          | _ -> None)
    and invoked =
      List.filter_map exprs ~f:(function S.ExprFuncCall (_, s) -> Some s | _ -> None)
      |> List.append (AU.get_pou_stmts elem)
      |> List.filter_map ~f:(function
          | S.StmFuncCall (_, f, _) -> Some (S.Function.get_name f)
          | _ -> None)
    in
    vars @ invoked
  in

  let decl_set = StringSet.of_list (get_decl_var_names ())
  and use_set = StringSet.of_list (get_use_var_names ()) in

  Set.diff decl_set use_set
  |> Set.fold ~init:[]
    ~f:(fun acc var_name -> begin
          let ti = AU.get_ti_by_name_exn elem var_name in
          let text = Printf.sprintf "Found unused local variable: %s" var_name in
          acc @ [Warn.mk ti.linenr ti.col "UnusedVariable" text]
        end)

let run elements =
  List.fold_left
    elements
    ~f:(fun warns e ->
        let ws = match e with
          | S.IECProgram _ | S.IECFunction _ | S.IECFunctionBlock _ -> check_pou e
          | _ -> []
        in
        warns @ ws)
    ~init:[]
