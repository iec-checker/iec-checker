TYPE Cfg : STRUCT gain : INT := 1; END_STRUCT; END_TYPE

CLASS Valve
VAR open : BOOL := FALSE; END_VAR
END_CLASS

FUNCTION_BLOCK Latch
VAR_INPUT set : BOOL := FALSE; END_VAR
VAR_OUTPUT q : BOOL := FALSE; END_VAR
IF set THEN q := TRUE; END_IF;
END_FUNCTION_BLOCK

FUNCTION_BLOCK Relay
VAR_IN_OUT shared : TON; END_VAR
VAR_OUTPUT q : BOOL := FALSE; END_VAR
q := shared.Q;
END_FUNCTION_BLOCK

PROGRAM plant
VAR
  latch : SR;
  mine : Latch;
  pulse : TON;
  passed : TON;
  pointed : TON;
  relay : Relay;
  cfg : Cfg;
  valve : Valve;
  drive : Lib_Drive;
  r : REF_TO TON;
  lamp : BOOL := FALSE;
  go : BOOL := FALSE;
  n : INT := 0;
END_VAR
lamp := latch.Q1;               (* UncalledInstance: read, never called *)
mine.set := go;
lamp := mine.q OR lamp;         (* UncalledInstance: input written, output read *)
pulse(IN := go, PT := T#1s);
lamp := pulse.Q;
relay(shared := passed);
lamp := passed.Q AND relay.q;
r := REF(pointed);
lamp := pointed.Q;
n := cfg.gain;
lamp := valve.open AND drive.Ready;
END_PROGRAM
