(* Pragmas are permitted anywhere in the program where spaces are allowed
   (IEC 61131-3, 2.1.6). *)
{attribute 'qualified_only'}
{attribute 'strict'}
TYPE E : (A, B); END_TYPE

{IF defined (VARIANT_X)}
FUNCTION_BLOCK fb {attribute 'hide'}
VAR_INPUT {attribute 'hide'}
  i : INT; {attribute 'monitoring' := 'variable'}
END_VAR
VAR
  {attribute 'symbol' := 'readwrite'}
  x : INT := {inline} 1;
END_VAR
{region "Init"}
x := i {info 'a "quoted" text'};
{endregion}
{warning
  'a multi-line pragma'
}
x := x + 1;
{{ nested {pragma} body }}
END_FUNCTION_BLOCK
{END_IF}

PROGRAM empty
{}
END_PROGRAM
