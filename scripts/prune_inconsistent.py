import sys
import os
import z3


def check(arr):
    mappings = {}
    gated = []
    cter = 0
    s = z3.Solver()
    for i in arr:
        i = i.split(",")
        if len(i) < 2:
            continue
        if i[0].startswith("isset"):
            sym, is_defined = i[1], int(i[2])
            if f"gated_{sym}" not in mappings:
                gated.append(sym)
                mappings[f"gated_{sym}"] = z3.Bool(f"gated_{sym}")
            s.add(mappings[f"gated_{sym}"] == True if is_defined == 0 else False)
            
        sym, decision, val, direction, cvt = (i[1]), int(i[2]), int(i[3]), int(i[4]), int(i[5])
        decision = decision if direction == 0 else not decision
        if f"gated_{sym}" not in mappings:
            gated.append(sym)
            mappings[f"gated_{sym}"] = z3.Bool(f"gated_{sym}")
            s.add(mappings[f"gated_{sym}"] == True)
        if sym not in mappings:
            if cvt == 4:
                mappings[sym] = z3.Int(f"k_{sym}")
            if cvt == 2 or cvt == 3:
                mappings[sym] = z3.Bool(f"k_{sym}")
            if cvt == 6:
                mappings[sym] = z3.String(f"k_{sym}")
        if i[0].startswith("20"): # IS_SMALLER_OR_EQUAL
            if decision:
                if cvt == 4:
                    s.add(mappings[sym] <= int(val))
                if cvt == 2 or cvt == 3:
                    s.add(mappings[sym] <= 1 if 't' in val else 0)
                if cvt == 6:
                    assert 0
        elif i[0].startswith("18") or i[0].startswith("16"): # neq
            if decision:
                if cvt == 4:
                    s.add(mappings[sym] != int(val))
                if cvt == 2 or cvt == 3:
                    s.add(mappings[sym] != 't' in val)
                if cvt == 6:
                    s.add(mappings[sym] != val)
        elif i[0].startwith("17") or i[0].startwith("15"): # eq
            if decision:
                if cvt == 4:
                    s.add(mappings[sym] == int(val))
                if cvt == 2 or cvt == 3:
                    s.add(mappings[sym] == 't' in val)
                if cvt == 6:
                    s.add(mappings[sym] == val)
        elif i[0].startwith("19"): # IS_SMALLER	
            if decision:
                if cvt == 4:
                    s.add(mappings[sym] < int(val))
                if cvt == 2 or cvt == 3:
                    s.add(mappings[sym] < 1 if 't' in val else 0)
                if cvt == 6:
                    assert 0
    return s.check()

directory = sys.argv[1]
for i in os.listdir(directory):
    try:
        if i.endswith(".cons"):
            if not check(open(directory + "/" + i).readlines()):
                print(f"Inconsistency identified {i}")
                os.system(f"rm -f {directory + '/' + i.replace('.cons', '')}")
    except:
        pass
