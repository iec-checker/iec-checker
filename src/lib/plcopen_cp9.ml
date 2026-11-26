open Core
open IECCheckerCore
open IECCheckerAnalysis

module AU = Ast_util
module S = Syntax
module CC = Cyclomatic_complexity

let describe_pou = function
  | S.IECProgram (_, p) -> Some ("program " ^ p.name, Some p.ti)
  | S.IECFunction (_, f) -> Some ("function " ^ S.Function.get_name f.id, Some (S.Function.get_ti f.id))
  | S.IECFunctionBlock (_, fb) ->
    Some ("function block " ^ S.FunctionBlock.get_name fb.id, Some (S.FunctionBlock.get_ti fb.id))
  | S.IECClass (_, c) -> Some ("class " ^ c.class_name, None)
  | _ -> None

let mk_warn elem_opt metric =
  match Option.bind elem_opt ~f:describe_pou with
  | Some (what, Some ti) ->
    Warn.mk ti.linenr ti.col "PLCOPEN-CP9" (Printf.sprintf "Code of %s is too complex (%s)" what metric)
  | Some (what, None) ->
    Warn.mk 0 0 "PLCOPEN-CP9" (Printf.sprintf "Code of %s is too complex (%s)" what metric)
  | None -> Warn.mk 0 0 "PLCOPEN-CP9" (Printf.sprintf "Code is too complex (%s)" metric)

let get_mccabe_violations elems cfg =
  let cc = CC.eval_mccabe cfg in
  if cc > Config.mccabe_complexity_threshold () then
    let elem = List.find elems ~f:(fun e -> S.get_pou_id e = Cfg.get_pou_id cfg) in
    [mk_warn elem (Printf.sprintf "%d McCabe complexity" cc)]
  else []

let get_statements_num_violations elem =
  let stmts_num = AU.get_stmts_num elem in
  if stmts_num > Config.statements_num_threshold () then
    [mk_warn (Some elem) (Printf.sprintf "%d statements" stmts_num)]
  else []

let do_check elems cfgs =
  List.fold_left
    cfgs
    ~init:[]
    ~f:(fun acc cfg -> acc @ (get_mccabe_violations elems cfg))
  |> List.append
  @@ List.fold_left
    elems
    ~init:[]
    ~f:(fun acc elem -> acc @ (get_statements_num_violations elem))

let detector : Detector.t = {
  id = "PLCOPEN-CP9";
  name = "Limit the complexity of POU code";
  summary =
    "POUs that exceed McCabe or statement-count thresholds should be split.";
  doc_url = "https://iec-checker.github.io/docs/detectors/PLCOPEN-CP9";
  check = (fun (i : Detector.inputs) -> do_check i.elements i.cfgs);
}

