TYPE Probe :
  STRUCT
    raw : INT;
    scaled : REAL;
    flags : WORD;
  END_STRUCT
END_TYPE

TYPE Tank :
  STRUCT
    level : REAL;
    limit : REAL;
    on_ : BOOL;
    kind : INT;
  END_STRUCT
END_TYPE

PROGRAM field_access
  VAR
    tanks : ARRAY[1..4] OF Tank;
    grid : ARRAY[0..2, 0..2] OF Probe;
    plant : Tank;
    w : WORD;
    i, j, n : INT;
    r : REAL;
    b : BOOL;
  END_VAR

  r := tanks[1].level;
  tanks[2].limit := 80.0;
  tanks[i].level := tanks[i + 1].level + plant.limit;
  grid[1, 2].raw := 7;
  n := grid[i, j].raw + grid[0, 0].raw;
  n := site.lines[3].probes[i].raw;
  site.lines[3].probes[i].raw := n;
  tanks[tanks[1].kind].kind := tanks[tanks[2].kind].kind;

  b := drives[1].single AND drive.on OR drives[2].to;
  drive.type := drives[3].type + drive.int + drive.true;
  plant.kind := tanks[3].kind;

  r := tanks [ 1 ] . level;
  r := plant . level;
  r := plant.(* inner *)level;
  r := tanks[1].
         level;
  r := plant. // tail
         limit;

  b := w.3;
  w.4 := b;
  b := w.%X5;
  w.%X6 := TRUE;
  b := grid[1, 1].flags.7;
  b := grid[1, 1].flags.%X8;

  IF tanks[1].level > tanks[1].limit AND NOT tanks[2].on_ THEN
    tanks[1].on_ := FALSE;
  ELSIF plant.level >= tanks[i].limit THEN
    plant.on_ := TRUE;
  END_IF;

  CASE tanks[i].kind OF
    1: tanks[i].on_ := TRUE; plant.kind := 2;
    Mode.IDLE, Mode.sub.RUN: tanks[i].on_ := FALSE;
    Mode#STOP: plant.on_ := FALSE;
  END_CASE;

  FOR i := tanks[1].kind TO tanks[2].kind BY plant.kind DO
    r := r + tanks[i].level;
  END_FOR;

  WHILE tanks[n].level < 1.0 DO
    n := n + 1;
  END_WHILE;

  REPEAT
    n := tanks[n].kind;
  UNTIL tanks[n].on_ END_REPEAT;

  r := MAX(tanks[1].level, plant.level);
  lib.clamp(v := tanks[1].level, hi := plant.limit, q => tanks[2].on_);
  r := -tanks[1].level ** 2.0;
END_PROGRAM
