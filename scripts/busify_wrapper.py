#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
busify_wrapper.py

Usage:
  python busify_wrapper.py /path/to/sadc__encoder.v

Creates /path/to/sadc__encoder__bussed.v:
- Indexed scalar ports collapsed into buses (direction preserved)
- Submodule named associations rewritten to bus slices
- Duplicate body declarations for ports (wire/reg/logic) removed
"""

from __future__ import annotations
import re
import sys
from pathlib import Path
from typing import Dict, Tuple, List, Set

# ---------- regexes ----------
RE_MODULE      = re.compile(r'^\s*module\s+(\w+)\s*\(', re.M)
RE_ENDMODULE   = re.compile(r'^\s*endmodule\b', re.M)
RE_PORT_DECL   = re.compile(r'^\s*(input|output|inout)\b([^;]*);', re.M)
RE_SUBINST     = re.compile(r'(\b\w+\b)\s+(\b\w+\b)\s*\((.*?)\);\s*', re.S)
RE_NAMED_ASSOC = re.compile(r'\.(\w+)\s*\(\s*([^)]+?)\s*\)')
RE_NETDECL     = re.compile(r'^\s*(wire|reg|logic)\b([^;]*);', re.M)

IDENT    = r'[A-Za-z_]\w*'
RE_IDENT = re.compile(rf'^{IDENT}$')
RE_NUMS  = re.compile(r'\d+')

# ---------- helpers ----------
def find_module_span(text: str) -> Tuple[int, int, int]:
    m = RE_MODULE.search(text)
    if not m:
        raise SystemExit("ERROR: could not find 'module <name>('")
    start = m.start()

    # find end of header ');'
    i = m.end()
    depth = 1
    j = i
    while j < len(text):
        ch = text[j]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                k = j + 1
                while k < len(text) and text[k].isspace():
                    k += 1
                if k < len(text) and text[k] == ';':
                    header_end = k + 1
                    break
        j += 1
    else:
        raise SystemExit("ERROR: could not locate end of module header ');'")

    e = RE_ENDMODULE.search(text, header_end)
    if not e:
        raise SystemExit("ERROR: could not find 'endmodule'")
    return start, header_end, e.start()

def tokenize_names_from_decl(text: str) -> List[str]:
    t = re.sub(r'\[[^\]]*\]', ' ', text)  # strip ranges
    t = re.sub(r'\b(reg|wire|logic|signed|unsigned)\b', ' ', t)
    names: List[str] = []
    for tok in re.split(r'[,\s]+', t):
        if tok and RE_IDENT.match(tok):
            names.append(tok)
    return names

def numeric_spans(name: str) -> List[Tuple[int, int]]:
    return [m.span() for m in RE_NUMS.finditer(name)]

def group_indexed_ports(port_dir: Dict[str, str]) -> Tuple[Dict[Tuple[str, str], Dict[int, str]], Set[str]]:
    """
    Group ports by replacing exactly ONE digit run with '{idx}'.
    key: (direction, skeleton) -> { idx : original_scalar_name }
    Return (bus_groups, scalars_not_in_any_bus_group).
    """
    tmp: Dict[Tuple[str, str], Dict[int, str]] = {}
    for nm, direction in port_dir.items():
        spans = numeric_spans(nm)
        if not spans:
            continue
        for (a, b) in spans:
            idx_txt = nm[a:b]
            idx = int(idx_txt)
            skeleton = nm[:a] + '{idx}' + nm[b:]
            key = (direction, skeleton)
            tmp.setdefault(key, {})
            tmp[key][idx] = nm

    bus_groups = {k: v for k, v in tmp.items() if len(v) >= 2}
    members = {nm for mapping in bus_groups.values() for nm in mapping.values()}
    scalars = {nm for nm in port_dir.keys() if nm not in members}
    return bus_groups, scalars

def skeleton_to_busbase(skeleton: str) -> str:
    return skeleton.replace('{idx}', '')

def rewrite_instances_with_buses(text: str, bus_groups) -> str:
    # scalar name -> (base, idx)
    scalar_to_bus: Dict[str, Tuple[str, int]] = {}
    for (_direction, skeleton), ixmap in bus_groups.items():
        base = skeleton_to_busbase(skeleton)
        for idx, nm in ixmap.items():
            scalar_to_bus[nm] = (base, idx)

    out: List[str] = []
    last = 0
    for m in RE_SUBINST.finditer(text):
        out.append(text[last:m.start()])
        mod, inst, plist = m.groups()
        rebuilt = []
        for p in RE_NAMED_ASSOC.finditer(plist):
            portname, sig = p.groups()
            sig_clean = sig.strip()
            if sig_clean in scalar_to_bus:
                base, idx = scalar_to_bus[sig_clean]
                sig_new = f"{base}[{idx}]"
            else:
                sig_new = sig_clean
            rebuilt.append(f".{portname}({sig_new})")
        new_plist = ', '.join(rebuilt) if rebuilt else plist
        out.append(f"{mod} {inst} ({new_plist});\n")
        last = m.end()
    out.append(text[last:])
    return ''.join(out)

def header_port_order(bus_groups, scalars, port_dir) -> List[str]:
    buses_in, buses_out, buses_io = [], [], []
    for (direction, skeleton) in bus_groups.keys():
        base = skeleton_to_busbase(skeleton)
        if direction == 'input':
            buses_in.append(base)
        elif direction == 'output':
            buses_out.append(base)
        else:
            buses_io.append(base)
    ordered = buses_in + buses_out + buses_io
    # append scalars in original declaration encounter order
    for nm, _dir in port_dir.items():
        if nm in scalars:
            ordered.append(nm)
    # dedup preserve order
    seen: Set[str] = set()
    final: List[str] = []
    for p in ordered:
        if p not in seen:
            final.append(p); seen.add(p)
    return final

def build_port_decls(bus_groups, scalars, port_dir) -> List[str]:
    decls: List[str] = []
    # buses
    for (direction, skeleton), ixmap in bus_groups.items():
        msb, lsb = max(ixmap.keys()), min(ixmap.keys())
        base = skeleton_to_busbase(skeleton)
        decls.append(f"{direction} wire [{msb}:{lsb}] {base};")
    # scalars
    for nm, direction in port_dir.items():
        if nm in scalars:
            decls.append(f"{direction} wire {nm};")
    return decls

def strip_port_like_net_decls(body: str, port_names: Set[str]) -> str:
    """
    Remove (or prune) any 'wire|reg|logic' declaration in the body that redeclares a port name.
    If a decl lists multiple names, keep only the non-port ones; if none remain, drop the decl.
    """
    out: List[str] = []
    last = 0
    for m in RE_NETDECL.finditer(body):
        out.append(body[last:m.start()])

        kind = m.group(1)
        tail = m.group(2)

        # extract one optional width (first []), for reconstruction
        width_m = re.search(r'\[[^\]]*\]', tail)
        width = width_m.group(0) + ' ' if width_m else ''

        # collect identifiers and filter out ports
        names = tokenize_names_from_decl(tail)
        keep = [n for n in names if n not in port_names]

        if keep:
            out.append(f"{kind} {width}{', '.join(keep)};\n")
        # else drop the whole declaration

        last = m.end()
    out.append(body[last:])
    return ''.join(out)

# ---------- entry point (not named 'main') ----------
def busify_sadc_encoder_file(inp_path: Path) -> Path:
    inp_path = Path(inp_path)
    src = inp_path.read_text(encoding='utf-8', errors='replace')

    # preserve backtick preamble lines at top (e.g. `timescale)
    preamble_lines = []
    for ln in src.splitlines():
        if ln.strip().startswith('`'):
            preamble_lines.append(ln)
        else:
            break
    preamble = ('\n'.join(preamble_lines) + '\n') if preamble_lines else ''

    mod_start, header_end, endmod_start = find_module_span(src)
    module_name = RE_MODULE.search(src).group(1)
    body_text   = src[header_end:endmod_start]

    # collect port directions within module body span
    port_dir: Dict[str, str] = {}
    for d in RE_PORT_DECL.finditer(src, header_end, endmod_start):
        direction = d.group(1)
        for nm in tokenize_names_from_decl(d.group(2)):
            port_dir[nm] = direction
    if not port_dir:
        raise SystemExit("ERROR: no port declarations (input/output/inout) found.")

    # group into buses
    bus_groups, scalars = group_indexed_ports(port_dir)

    # build sets used for filtering duplicate decls
    members_in_groups = {nm for mapping in bus_groups.values() for nm in mapping.values()}
    bus_bases = {skeleton_to_busbase(skel) for (_dir, skel) in bus_groups.keys()}
    # These are names we will declare at top level: bus bases + scalar ports
    top_level_port_names: Set[str] = set(scalars) | bus_bases

    # rewrite instances
    body_rewritten = rewrite_instances_with_buses(body_text, bus_groups)

    # remove any input/output/inout declarations in the body (already handled at top)
    body_no_port_decls = RE_PORT_DECL.sub('', body_rewritten)

    # remove duplicate wire/reg/logic declarations for port names (both scalars and grouped members)
    # Anything that declares a port (scalar) or any of the original grouped members should be removed.
    # We remove dupes for: all original scalar port names + all grouped member names + any bus base names.
    port_like_names = set(port_dir.keys()) | members_in_groups | bus_bases
    body_clean = strip_port_like_net_decls(body_no_port_decls, port_like_names)

    # assemble header & decls
    header_ports = header_port_order(bus_groups, scalars, port_dir)
    decls        = build_port_decls(bus_groups, scalars, port_dir)

    new: List[str] = []
    new.append(preamble)
    new.append(f"module {module_name} (\n    " + ", ".join(header_ports) + "\n);\n\n")
    if decls:
        new.append("// Port declarations (auto-generated)\n")
        for dline in decls:
            new.append(dline + "\n")
        new.append("\n")
    new.append("// ---- Body (instances rewritten to use bus slices) ----\n")
    new.append(body_clean.strip() + "\n")
    new.append("endmodule\n")

    out_path = inp_path.with_name(inp_path.stem + "__bussed.v")
    out_path.write_text(''.join(new), encoding='utf-8')
    return out_path

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python busify_wrapper.py /path/to/sadc__encoder.v")
        sys.exit(2)
    out = busify_sadc_encoder_file(Path(sys.argv[1]))
    print(f"Wrote {out}")
