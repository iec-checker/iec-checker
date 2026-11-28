open Core
open IECCheckerCore

module S = Syntax
module TI = Tok_info
module AU = Ast_util

type site = {
  name : string;
  ti : TI.t;
  branches : (int * int) list;
  levels : (int * int) list;
  return_at : (int * int) option;
}

let root name = List.hd_exn (String.split name ~on:'.')

let collect_sites instances stmts =
  let sites = ref [] in
  let counter = ref 0 in
  let next () = incr counter; !counter in
  let rec walk_list ~branches ~levels ~return_at stmts =
    let l = next () in
    let returns = List.filter_mapi stmts ~f:(fun i s -> match s with S.StmReturn _ -> Some i | _ -> None) in
    List.iteri stmts ~f:(fun i s ->
        let return_at =
          match List.find returns ~f:(fun r -> r > i) with
          | Some r -> Some (l, r)
          | None -> return_at
        in
        walk_stmt ~branches ~levels:(levels @ [ (l, i) ]) ~return_at s)
  and walk_stmt ~branches ~levels ~return_at = function
    | S.StmFuncCall (_, f, _) ->
      let name = S.Function.get_name f in
      if List.mem instances (root name) ~equal:String.equal then
        sites := { name; ti = S.Function.get_ti f; branches; levels; return_at } :: !sites
    | S.StmIf (_, _, body, elsifs, els) ->
      let n = next () in
      let walk b = walk_list ~branches:(branches @ [ (n, b) ]) ~levels ~return_at in
      walk 0 body;
      List.iteri elsifs ~f:(fun i -> function
          | S.StmElsif (_, _, b) -> walk (i + 1) b
          | s -> walk_stmt ~branches ~levels ~return_at s);
      walk (-1) els
    | S.StmCase (_, _, sels, els) ->
      let n = next () in
      let walk b = walk_list ~branches:(branches @ [ (n, b) ]) ~levels ~return_at in
      List.iteri sels ~f:(fun i (cs : S.case_selection) -> walk i cs.body);
      walk (-1) els
    | S.StmFor (_, _, body) | S.StmWhile (_, _, body) | S.StmRepeat (_, body, _) ->
      walk_list ~branches ~levels ~return_at body
    | _ -> ()
  in
  walk_list ~branches:[] ~levels:[] ~return_at:None stmts;
  List.rev !sites

let exclusive a b =
  List.exists a.branches ~f:(fun (n, x) ->
      List.exists b.branches ~f:(fun (m, y) -> Int.equal n m && not (Int.equal x y)))

let reaches a b =
  match a.return_at with
  | None -> true
  | Some (l, r) -> List.exists b.levels ~f:(fun (l', k) -> Int.equal l l' && k < r)

let both_run a b = (not (exclusive a b)) && reaches a b

let check_scope instances stmts =
  let sites = collect_sites instances stmts in
  List.filter_mapi sites ~f:(fun j b ->
      List.find (List.take sites j) ~f:(fun a -> String.equal a.name b.name && both_run a b)
      |> Option.map ~f:(fun a ->
          let msg =
            Printf.sprintf "Function block instance %s is called more than once per cycle (first call at line %d)"
              b.name a.ti.linenr
          in
          Warn.mk b.ti.linenr b.ti.col "PLCOPEN-CP20" msg))

let check_elem elem =
  let instances = List.map (AU.get_var_decls elem) ~f:S.VarDecl.get_var_name in
  match elem with
  | S.IECClass (_, c) -> List.concat_map c.methods ~f:(fun m -> check_scope instances m.statements)
  | _ -> check_scope instances (AU.get_top_stmts elem)

let do_check elems = List.concat_map elems ~f:check_elem

let detector : Detector.t = {
  id = "PLCOPEN-CP20";
  name = "Function block instances should be called only once";
  summary = "An FB instance called twice in one cycle gives outputs that depend on statement order.";
  doc_url = "https://iec-checker.github.io/docs/detectors/PLCOPEN-CP20";
  check = (fun (i : Detector.inputs) -> do_check i.elements);
}
