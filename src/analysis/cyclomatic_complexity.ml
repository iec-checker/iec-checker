open Core
open IECCheckerCore

module S = Syntax
module AU = Ast_util

let rec decisions stmts =
  List.fold stmts ~init:0 ~f:(fun acc s -> acc + decisions_of s)

and decisions_of = function
  | S.StmIf (_, _, body, elsifs, els) -> 1 + decisions body + decisions elsifs + decisions els
  | S.StmElsif (_, _, body) -> 1 + decisions body
  | S.StmCase (_, _, sels, els) ->
    List.fold sels ~init:(decisions els) ~f:(fun acc (cs : S.case_selection) -> acc + 1 + decisions cs.body)
  | S.StmFor (_, _, body) | S.StmWhile (_, _, body) | S.StmRepeat (_, body, _) -> 1 + decisions body
  | S.StmExpr _ | S.StmFuncCall _ | S.StmEmpty _ | S.StmExit _ | S.StmContinue _ | S.StmReturn _ -> 0

let eval_mccabe elem = 1 + decisions (AU.get_top_stmts elem)
