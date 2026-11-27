(** Describes single token of a parse tree *)

type t = { id : int; linenr : int; col : int; raw : string } [@@deriving yojson, show]
(** Parse tree item.  [linenr] and [col] are the 1-based position of the first
    character of the token.  [raw] stores the original source spelling of the
    token (preserving case) for identifiers; empty string otherwise. *)

val create : Lexing.lexbuf -> t
(** [create] Create new parse tree element from Lexing.lexbuf *)

val create_with_raw : Lexing.lexbuf -> string -> t
(** [create_with_raw lexbuf raw] like {!create} but also records the original
    token text in the [raw] field. *)

val create_at : Lexing.position -> string -> t
(** [create_at pos raw] like {!create_with_raw}, for a token that starts at [pos]. *)

val at : Lexing.position -> t -> t
(** [at pos ti] is [ti] moved to [pos], for an item that starts before its own
    token: a signed or typed literal, a unary expression. *)

val create_dummy : unit -> t
(** [create_dummy] Create a new dummy parse tree element *)

val to_string : t -> string
