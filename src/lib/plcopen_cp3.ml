open Core
open IECCheckerCore

module S = Syntax
module AU = IECCheckerCore.Ast_util

let std_fbs = [
  "SR"; "RS"; "R_TRIG"; "F_TRIG";
  "CTU"; "CTU_INT"; "CTU_DINT"; "CTU_LINT"; "CTU_UDINT"; "CTU_ULINT";
  "CTD"; "CTD_INT"; "CTD_DINT"; "CTD_LINT"; "CTD_UDINT"; "CTD_ULINT";
  "CTUD"; "CTUD_INT"; "CTUD_DINT"; "CTUD_LINT"; "CTUD_UDINT"; "CTUD_ULINT";
  "TP"; "TP_TIME"; "TP_LTIME"; "TON"; "TON_TIME"; "TON_LTIME"; "TOF"; "TOF_TIME"; "TOF_LTIME";
]

let instance_types elems =
  std_fbs @ List.filter_map elems ~f:(function
      | S.IECFunctionBlock (_, fb) -> Some (S.FunctionBlock.get_name fb.id)
      | S.IECClass (_, c) -> Some c.class_name
      | _ -> None)

let is_instance types decl =
  match S.VarDecl.get_ty_spec decl with
  | Some (S.DTyDeclSingleElement (S.DTySpecSimple t, _)) -> List.mem types t ~equal:String.Caseless.equal
  | _ -> false

let takes_initializer types decl =
  match S.VarDecl.get_attr decl with
  | Some (S.VarDecl.VarInOut | S.VarDecl.VarExternal _) -> false
  | _ -> not (is_instance types decl)

let do_check elems =
  let takes_initializer = takes_initializer (instance_types elems) in
  List.fold_left elems ~init:[] ~f:(fun acc elem -> acc @ (AU.get_var_decls elem))
  |> List.fold_left
    ~init:[]
    ~f:(fun acc decl -> begin
          match S.VarDecl.get_located_at decl with
          | None -> begin
              if takes_initializer decl && not (S.VarDecl.get_was_init decl) then
                let ti = S.VarDecl.get_var_ti decl in
                let msg = Printf.sprintf("Variable %s shall be initialized before being used") @@ S.VarDecl.get_var_name decl in
                let w = Warn.mk ti.linenr ti.col "PLCOPEN-CP3" msg in
                acc @ [w]
              else
                acc
            end
          | _ -> acc
        end)

let detector : Detector.t = {
  id = "PLCOPEN-CP3";
  name = "Variables shall be initialized before being used";
  summary = "Every variable declaration should carry an explicit initializer.";
  doc_url = "https://iec-checker.github.io/docs/detectors/PLCOPEN-CP3";
  check = (fun (i : Detector.inputs) -> do_check i.elements);
}
