from pathlib import Path
from netlist_leaf_counter import netlist_leaf_counter

res = netlist_leaf_counter(
    netlist_path=Path("/path/to/netlist.vams"),
    top="paer_32_4_1",          # or None to auto-infer tops
    list_tops=False,         # True -> prints only the inferred tops
    dump_leaves=True         # True -> prints the breakdown by leaf type
)

print(res["tops"])       # list of top modules used
print(res["total"])      # total count of leaf device instances
print(res["breakdown"])  # dict: {leaf_type: count}

