open Core
open IECCheckerCore

module S = Syntax
module AU = IECCheckerCore.Ast_util

let real_vars elem =
  AU.get_var_decls elem
  |> List.filter_map ~f:(fun d ->
      match S.VarDecl.get_ty_spec d with
      | Some (S.DTyDeclSingleElement (S.DTySpecElementary (S.REAL | S.LREAL), _)) ->
        Some (S.VarDecl.get_var_name d)
      | _ -> None)

let is_float reals = function
  | S.ExprConstant (_, S.CReal _) -> true
  | S.ExprVariable (_, v) ->
    List.is_empty (S.VarUse.get_path v)
    && List.mem reals (S.VarUse.get_name v) ~equal:String.equal
  | _ -> false

let check_elem elem =
  let is_float = is_float (real_vars elem) in
  AU.get_pou_subexprs elem
  |> List.fold_left ~init:[]
    ~f:(fun acc expr -> begin
          match expr with
          | S.ExprBin(ti, lhs, operator, rhs) -> begin
              match operator with
              | EQ | NEQ -> begin
                  if (is_float lhs) || (is_float rhs) then begin
                    let msg = "Floating point comparison shall not be equality or inequality" in
                    acc @ [(Warn.mk ti.linenr ti.col "PLCOPEN-CP8" msg)]
                  end
                  else acc
                end
              | _ -> acc
            end
          | _ -> acc
        end)

let do_check elems =
  List.fold_left
    ~init:[]
    elems
    ~f:(fun acc elem -> acc @ (check_elem elem))

let detector : Detector.t = {
  id = "PLCOPEN-CP8";
  name = "Floating point comparison shall not be equality or inequality";
  summary =
    "Use a tolerance instead of [=] or [<>] when comparing [REAL] values.";
  doc_url = "https://iec-checker.github.io/docs/detectors/PLCOPEN-CP8";
  check = (fun (i : Detector.inputs) -> do_check i.elements);
}
