open Core
open IECCheckerCore

module S = Syntax
module AU = IECCheckerCore.Ast_util

let get_ty_size = function
  | S.NIL -> 1
  | S.STRING len -> len
  | S.WSTRING len -> len * 2
  | S.CHAR len -> len
  | S.WCHAR len -> len * 2
  | S.TIME -> 8
  | S.LTIME -> 16
  | S.SINT -> 1
  | S.INT -> 2
  | S.DINT -> 4
  | S.LINT -> 8
  | S.USINT -> 1
  | S.UINT -> 2
  | S.UDINT -> 4
  | S.ULINT -> 8
  | S.REAL -> 4
  | S.LREAL -> 8
  | S.DATE -> 8
  | S.LDATE -> 16
  | S.TIME_OF_DAY -> 8
  | S.TOD -> 8
  | S.LTOD -> 16
  | S.DATE_AND_TIME -> 16
  | S.LDATE_AND_TIME -> 16
  | S.DT -> 8
  | S.LDT -> 16
  | S.BOOL -> 1
  | S.BYTE -> 1
  | S.WORD -> 2
  | S.DWORD -> 4
  | S.LWORD -> 8

(** Find a direct variable declared in [elem], other than [orig_decl], whose
    address in the same memory area overlaps [orig_dir_var] with size [size]. *)
(* FIXME: This is horrible slow to call it on each iteration. I have no idea how to implement the cache. *)
let find_overlapping_var elem orig_decl orig_dir_var size =
  let orig_path = S.DirVar.get_path orig_dir_var in
  let orig_loc = S.DirVar.get_loc orig_dir_var in
  if List.is_empty orig_path || Option.is_none orig_loc then
    None
  else begin
    let orig_last_path_num = List.last_exn orig_path in
    AU.get_var_decls elem
    |> List.fold_left
      ~init:None
      ~f:(fun acc var_decl -> begin
            match acc with
            | Some acc -> Some acc
            | None when phys_equal var_decl orig_decl -> None
            | None -> begin
                match S.VarDecl.get_located_at var_decl with
                | Some dir_var when Poly.equal (S.DirVar.get_loc dir_var) orig_loc -> begin
                    let path = S.DirVar.get_path dir_var in
                    if (List.is_empty path ||
                        not @@ phys_equal (List.length path) (List.length orig_path) ||
                        not @@ List.equal Int.equal
                          (List.take orig_path ((List.length orig_path) - 1))
                          (List.take path ((List.length path) - 1))) then
                      acc
                    else begin
                      let last_path_num = List.last_exn path in
                      if last_path_num = orig_last_path_num ||
                         (last_path_num < orig_last_path_num && last_path_num + size > orig_last_path_num) ||
                         (last_path_num > orig_last_path_num && last_path_num < orig_last_path_num + size) then
                        Some dir_var
                      else
                        acc
                    end
                  end
                | _ -> acc
              end
          end)
  end

let check_elem elem =
  AU.get_var_decls elem
  |> List.fold_left
    ~init:[]
    ~f:(fun acc decl -> begin
          match S.VarDecl.get_ty_spec decl with
          | Some S.DTyDeclSingleElement (elem_spec, _) -> begin
              match elem_spec with
              | S.DTySpecElementary elem_spec -> begin
                  match S.VarDecl.get_located_at decl with
                  | Some dir_var -> begin
                      let size = get_ty_size elem_spec in
                      match find_overlapping_var elem decl dir_var size with
                      | Some overlapped_dir_var -> begin
                          let ti = S.VarDecl.get_var_ti decl in
                          let msg =
                            Printf.sprintf("Address of direct variable %s (size %d) should not overlap with direct variable %s")
                            (S.DirVar.get_name dir_var) size
                            (S.DirVar.get_name overlapped_dir_var)
                          in
                          let w = Warn.mk ti.linenr ti.col "PLCOPEN-CP4" msg in
                          acc @ [w];
                        end
                      | _ -> acc
                    end
                  | _ -> acc
                end
              | _ -> acc
            end
          | _ -> acc
        end)

let do_check elems =
  List.fold_left elems ~init:[] ~f:(fun acc elem -> acc @ (check_elem elem))

let detector : Detector.t = {
  id = "PLCOPEN-CP4";
  name = "Direct addressing should not overlap";
  summary =
    "Two directly-addressed variables must not occupy overlapping memory.";
  doc_url = "https://iec-checker.github.io/docs/detectors/PLCOPEN-CP4";
  check = (fun (i : Detector.inputs) -> do_check i.elements);
}
