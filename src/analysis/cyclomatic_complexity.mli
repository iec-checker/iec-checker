(** McCabe cyclomatic complexity of a POU. *)
open IECCheckerCore
module S = Syntax

val eval_mccabe : S.iec_library_element -> int
(** [eval_mccabe pou] is 1 plus one for each [IF], [ELSIF], [CASE]
    selection, [FOR], [WHILE] and [REPEAT] in [pou]. Boolean operators in
    conditions are not counted. *)
