#!/usr/bin/env python3
"""
netlist_leaf_counter.py

Traverse a hierarchical Verilog / Verilog-AMS netlist and count "leaf" devices:
instances whose type/module name does NOT have a corresponding `module <name>`
definition in the given netlist file.

-------------------------------------------------------------------------------
HOW TO RUN (Linux/macOS shell)
-------------------------------------------------------------------------------
python3 netlist_leaf_counter.py /path/to/netlist.vams
python3 netlist_leaf_counter.py /path/to/netlist.vams -t TOP_MODULE
python3 netlist_leaf_counter.py /path/to/netlist.vams --list-tops
python3 netlist_leaf_counter.py /path/to/netlist.vams --dump-leaves

-------------------------------------------------------------------------------
HOW TO USE FROM PYTHON (script or interpreter)
-------------------------------------------------------------------------------
from pathlib import Path
from netlist_leaf_counter import netlist_leaf_counter

result = netlist_leaf_counter(
    netlist_path=Path("/path/to/netlist.vams"),
    top="TOP_MODULE",          # or None to auto-infer tops
    list_tops=False,           # True -> prints only the inferred tops
    dump_leaves=True           # True -> prints breakdown by leaf type
)

# result is a dict:
# { "tops": [...], "total": <int>, "breakdown": { <leaf_type>: <count>, ... } }
-------------------------------------------------------------------------------
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional

# Keywords that imply a statement head is not an instantiation
RESERVED_HEAD = {
    'module', 'endmodule',
    'primitive', 'endprimitive',
    'input', 'output', 'inout', 'wire', 'wreal', 'tri', 'supply0', 'supply1',
    'real', 'integer', 'time', 'reg', 'logic',
    'electrical', 'ground', 'discipline', 'nature',
    'parameter', 'localparam', 'typedef',
    'assign', 'always', 'initial', 'analog',
    'function', 'endfunction', 'task', 'endtask',
    'generate', 'endgenerate', 'for', 'if', 'case', 'endcase', 'begin', 'end',
    'import', 'export',
}

# Comments and attributes
COMMENT_BLOCK_RE = re.compile(r'/\*.*?\*/', re.DOTALL)
COMMENT_LINE_RE  = re.compile(r'//.*?$', re.MULTILINE)
ATTR_BLOCK_RE    = re.compile(r'\(\*.*?\*\)', re.DOTALL)  # Verilog attributes: (* ... *)

MODULE_DEF_RE = re.compile(r'^\s*module\s+([A-Za-z_]\w*)\b', re.MULTILINE)
ENDMODULE_RE   = re.compile(r'^\s*endmodule\b', re.MULTILINE)

IDENT_RE = re.compile(r'[A-Za-z_]\w*')  # identifier token


def strip_comments_and_attrs(text: str) -> str:
    """Remove /* ... */, // ... EOL, and Verilog attributes (* ... *)."""
    text = COMMENT_BLOCK_RE.sub('', text)
    text = COMMENT_LINE_RE.sub('', text)
    text = ATTR_BLOCK_RE.sub('', text)
    return text


def split_statements_in_module(body: str) -> List[str]:
    """Split module body into simple statements by ';' (attributes already stripped)."""
    parts: List[str] = []
    buf: List[str] = []
    for ch in body:
        buf.append(ch)
        if ch == ';':
            parts.append(''.join(buf).strip())
            buf = []
    if buf:
        rest = ''.join(buf).strip()
        if rest:
            parts.append(rest)
    return parts


def parse_inst_head(stmt: str) -> Optional[Tuple[str, str]]:
    """
    Deterministically parse an instantiation head:
        Type [#( ...balanced... )] Rest...
    Returns (type, rest_after_params) or None if not an instantiation.
    """
    n = len(stmt)
    i = 0

    # skip leading whitespace
    while i < n and stmt[i].isspace():
        i += 1

    # read Type identifier
    m = IDENT_RE.match(stmt, i)
    if not m:
        return None
    typ = m.group(0)
    i = m.end()

    # if the head token is a reserved keyword, bail
    if typ in RESERVED_HEAD:
        return None

    # skip spaces
    while i < n and stmt[i].isspace():
        i += 1

    # optional parameterization: '# ( ...balanced... )'
    if i < n and stmt[i] == '#':
        i += 1
        while i < n and stmt[i].isspace():
            i += 1
        if i >= n or stmt[i] != '(':
            # malformed parameterization
            return None
        # consume balanced parentheses with full nesting
        depth = 0
        while i < n:
            c = stmt[i]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    i += 1  # move past closing ')'
                    break
            i += 1
        # skip trailing spaces
        while i < n and stmt[i].isspace():
            i += 1

    rest = stmt[i:].strip()
    return (typ, rest)


def extract_instance_names(rest: str) -> List[Tuple[str, Optional[Tuple[int, int]]]]:
    """
    Given the remainder of an instantiation statement (after the Type[#()]), extract
    a list of (instance_name, optional_array_range(msb,lsb)) for each instance before its (...).
    Supports forms like:
       inst1 ( ... ), inst2 ( ... )
       inst[3:0] ( ... )
    """
    res: List[Tuple[str, Optional[Tuple[int, int]]]] = []
    i = 0
    n = len(rest)

    def skip_ws(i: int) -> int:
        while i < n and rest[i].isspace():
            i += 1
        return i

    while True:
        i = skip_ws(i)
        if i >= n:
            break

        m = IDENT_RE.match(rest, i)
        if not m:
            break
        inst_name = m.group(0)
        i = m.end()

        # optional array [msb:lsb]
        arr_range: Optional[Tuple[int, int]] = None
        i = skip_ws(i)
        if i < n and rest[i] == '[':
            j = i + 1
            depth = 1
            while j < n and depth > 0:
                if rest[j] == '[':
                    depth += 1
                elif rest[j] == ']':
                    depth -= 1
                j += 1
            inside = rest[i+1:j-1].strip()
            if ':' in inside:
                msb_s, lsb_s = inside.split(':', 1)
                try:
                    msb = int(msb_s, 0)
                    lsb = int(lsb_s, 0)
                    arr_range = (msb, lsb)
                except ValueError:
                    arr_range = None
            i = j
            i = skip_ws(i)

        # expect '(' and skip balanced port list
        if i >= n or rest[i] != '(':
            break
        depth = 0
        while i < n:
            c = rest[i]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1

        res.append((inst_name, arr_range))

        i = skip_ws(i)
        if i < n and rest[i] == ',':
            i += 1
            continue
        else:
            break

    return res


def parse_netlist(text: str):
    """
    Parse netlist into:
      - module_names: set[str]
      - module_insts: dict[module_name] -> list of (type, instname, multiplicity)
      - used_types: set[str] of all types instantiated anywhere
    """
    module_names: Set[str] = set()
    module_insts: Dict[str, List[Tuple[str, str, int]]] = {}
    used_types: Set[str] = set()

    # Strip comments and Verilog attributes first
    text_nc = strip_comments_and_attrs(text)

    # Find modules and their bodies
    modules: List[Tuple[str, int, int]] = []
    for m in MODULE_DEF_RE.finditer(text_nc):
        name = m.group(1)
        module_names.add(name)
        start = m.end()
        m_end = ENDMODULE_RE.search(text_nc, start)
        end = m_end.start() if m_end else len(text_nc)
        modules.append((name, start, end))

    # Parse instantiations
    for name, start, end in modules:
        body = text_nc[start:end]
        stmts = split_statements_in_module(body)
        out_list: List[Tuple[str, str, int]] = []
        for st in stmts:
            st = st.strip()
            if not st:
                continue

            # Quick head token (for early skip)
            head = IDENT_RE.match(st)
            if not head:
                continue
            head_kw = head.group(0)
            if head_kw in RESERVED_HEAD:
                continue

            # Deterministic head parse: Type [#(...)] Rest
            parsed = parse_inst_head(st)
            if not parsed:
                continue
            typ, rest = parsed

            if typ in RESERVED_HEAD:
                continue

            insts = extract_instance_names(rest)
            if not insts:
                continue

            for instname, arr in insts:
                mult = 1
                if arr is not None:
                    msb, lsb = arr
                    mult = abs(msb - lsb) + 1
                out_list.append((typ, instname, mult))
                used_types.add(typ)

        module_insts[name] = out_list

    return module_names, module_insts, used_types


def find_roots(module_names: Set[str], module_insts: Dict[str, List[Tuple[str, str, int]]]) -> List[str]:
    """Modules not instantiated by any other module."""
    instantiated: Set[str] = set()
    for _m, insts in module_insts.items():
        for typ, _inst, _mult in insts:
            if typ in module_names:
                instantiated.add(typ)
    roots = sorted([m for m in module_names if m not in instantiated])
    return roots


def count_leaves(module_insts, module_names, start_modules: List[str]):
    """DFS from each start module; count insts whose type not in module_names."""
    from collections import defaultdict
    leaf_counts = defaultdict(int)
    for start in start_modules:
        stack: List[Tuple[str, int]] = [(start, 1)]
        while stack:
            mod, scale = stack.pop()
            for typ, _instname, mult in module_insts.get(mod, []):
                total_mult = scale * mult
                if typ in module_names:
                    stack.append((typ, total_mult))
                else:
                    leaf_counts[typ] += total_mult
    return dict(leaf_counts)


def netlist_leaf_counter(netlist_path: Path, top: Optional[str] = None,
                         list_tops: bool = False, dump_leaves: bool = False):
    """
    Programmatic API: analyze a netlist and return a dict with tops, total, breakdown.
    - netlist_path: Path to .v/.vams file
    - top: optional top module name; if None, inferred (roots)
    - list_tops: if True, prints inferred tops
    - dump_leaves: if True, prints leaf-type breakdown

    Returns:
        {
          "tops": <list of tops (inferred or [top])>,
          "total": <int>,
          "breakdown": { <leaf_type>: <count>, ... }
        }
    """
    text = netlist_path.read_text(encoding="utf-8", errors="ignore")
    module_names, module_insts, _used_types = parse_netlist(text)

    roots = find_roots(module_names, module_insts)
    if top:
        if top not in module_names:
            raise ValueError(f"Top '{top}' not found among modules: {sorted(module_names)}")
        start_modules = [top]
    else:
        start_modules = roots

    if list_tops:
        print("Inferred top modules:", ", ".join(roots) if roots else "(none)")

    if not start_modules:
        # No obvious root; fall back to counting across all modules
        start_modules = sorted(module_names)

    leaf_counts = count_leaves(module_insts, module_names, start_modules)
    total = sum(leaf_counts.values())

    if dump_leaves:
        if leaf_counts:
            by_count = sorted(leaf_counts.items(), key=lambda kv: (-kv[1], kv[0]))
            print("Breakdown by type:")
            w = max((len(k) for k,_ in by_count), default=4)
            for k, v in by_count:
                print(f"  {k:<{w}}  {v}")
        else:
            print("Breakdown by type: (no leaf instances found)")

    return {
        "tops": start_modules if top else roots,
        "total": total,
        "breakdown": leaf_counts,
    }


def main():
    ap = argparse.ArgumentParser(
        description="Count leaf devices (types without module definitions) in a hierarchical Verilog/VAMS netlist."
    )
    ap.add_argument("netlist", type=Path, help="Path to netlist (.v/.vams)")
    ap.add_argument(
        "-t", "--top",
        help="Top module name (optional). If omitted, inferred as modules not instantiated by others."
    )
    ap.add_argument("--list-tops", action="store_true", help="Just list inferred top modules and exit.")
    ap.add_argument("--dump-leaves", action="store_true", help="Print the full leaf-type breakdown.")
    args = ap.parse_args()

    result = netlist_leaf_counter(
        netlist_path=args.netlist,
        top=args.top,
        list_tops=args.list_tops,
        dump_leaves=args.dump_leaves,
    )

    # Always print the headline count for CLI usability
    print(f"Total leaf device instances: {result['total']}")
    if not args.dump_leaves:
        if result['tops']:
            print("Top modules:", ", ".join(result['tops']))


if __name__ == "__main__":
    main()

