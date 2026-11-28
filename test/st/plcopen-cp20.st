TYPE Pair : STRUCT a : TON; b : TON; END_STRUCT; END_TYPE

FUNCTION Scale : INT
VAR_INPUT v : INT := 0; END_VAR
Scale := v * 2;
END_FUNCTION

PROGRAM demo
VAR
  edge : R_TRIG;
  pulse : TP;
  cnt : CTU;
  pid : TON;
  drive : TON;
  probe : TON;
  reader : TON;
  pair : Pair;
  a : BOOL := FALSE;
  b : BOOL := FALSE;
  mode : INT := 0;
  i : INT := 0;
  n : INT := 0;
END_VAR
edge(CLK := a);
edge(CLK := b);                          (* PLCOPEN-CP20: second call in the cycle *)

pulse(IN := a, PT := T#1s);
IF pulse.Q THEN
  pulse(IN := FALSE);                    (* PLCOPEN-CP20: runs after the first call *)
END_IF;

IF a THEN cnt(CU := TRUE); END_IF;
IF b THEN cnt(CU := TRUE); END_IF;       (* PLCOPEN-CP20: both IFs can be true *)

IF a THEN pid(IN := TRUE); ELSIF b THEN pid(IN := FALSE); ELSE pid(IN := a); END_IF;
CASE mode OF
  1: drive(IN := TRUE);
  2: drive(IN := FALSE);
END_CASE;

FOR i := 1 TO 3 DO reader(IN := a); END_FOR;
pair.a(IN := a);
pair.b(IN := b);
n := Scale(v := n);
n := Scale(v := n);

IF b THEN probe(IN := FALSE); RETURN; END_IF;
probe(IN := TRUE);
END_PROGRAM

PROGRAM late
VAR t : TON; a : BOOL := FALSE; END_VAR
t(IN := a);
IF a THEN t(IN := FALSE); RETURN; END_IF; (* PLCOPEN-CP20: the first call ran before *)
END_PROGRAM
