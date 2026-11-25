type warn_ty =
  | Inspection
  | InternalError
[@@deriving yojson]

type t = {
  linenr: int;
  column: int;
  file: string;
  id: string;
  msg: string;
  context: string;
  ty: warn_ty [@key "type"];
} [@@deriving yojson]

let valid_utf_8 s =
  if String.is_valid_utf_8 s then s
  else begin
    let b = Buffer.create (String.length s) in
    let rec go i =
      if i < String.length s then begin
        let d = String.get_utf_8_uchar s i in
        let n = Uchar.utf_decode_length d in
        if Uchar.utf_decode_is_valid d then Buffer.add_string b (String.sub s i n)
        else String.iter (fun c -> Buffer.add_string b (Printf.sprintf "\\x%02X" (Char.code c))) (String.sub s i n);
        go (i + n)
      end
    in
    go 0;
    Buffer.contents b
  end

let mk ?(ty=Inspection) ?(file="") ?(context="") linenr column id msg =
  { linenr; column; file; id; msg = valid_utf_8 msg; context = valid_utf_8 context; ty }
let mk_internal ?(id="InternalError") msg = mk ~ty:InternalError 0 0 id msg
let mk_from_lexbuf ?(context="") (lexbuf : Lexing.lexbuf) id msg =
  let pos = lexbuf.lex_start_p in
  mk ~file:(pos.pos_fname) ~context pos.pos_lnum (pos.pos_cnum - pos.pos_bol + 1) id msg

let to_string w =
  match w.ty with
  | Inspection -> Printf.sprintf "%d:%d %s: %s" w.linenr w.column w.id w.msg
  | InternalError -> Printf.sprintf "%s: %s" w.id w.msg

