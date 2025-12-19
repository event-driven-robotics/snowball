# -*- coding: utf-8 -*-
"""
Streaming analysis for massive VCSV files (100 GB+ friendly)
with edge semantics matched to the original array-based version
and an optional progress bar.
"""

import os
import re
from typing import Dict, Iterable, List, Tuple, Optional

# Optional tqdm progress
try:
    from tqdm import tqdm
except Exception:  # pragma: no cover
    tqdm = None


# -----------------------------
# Header parsing (VCSV)
# -----------------------------

class VCSVHeader:
    """
    Minimal header information for streaming:
      - signal_names: ordered list of signal names
      - name_to_idx: mapping signal name -> logical value-column index (0-based among values)
      - value_token_index(j): given logical index j, returns the 0-based CSV token index
        for the value on each data line (accounting for time + alternating value,label).
    """
    def __init__(self, signal_names: List[str]):
        self.signal_names = signal_names
        self.name_to_idx = {n: i for i, n in enumerate(signal_names)}

    @staticmethod
    def from_file(f) -> "VCSVHeader":
        """
        Assumes the file cursor is at the beginning.
        VCSV layout (from your previous parser):
          line 0: (ignored)
          line 1: signal names with optional (param=val)
          line 2-3: (ignored)
          line 4: unit names (ignored)
          line 5: units (ignored)
          line 6+: data rows
        """
        lines = []
        for _ in range(6):
            line = f.readline()
            if not line:
                raise ValueError("Unexpected EOF while reading VCSV header.")
            lines.append(line.rstrip("\n"))

        # Extract signal names from line 1
        s1 = lines[1]
        raw_entries = [entry.strip() for entry in s1.split(',')]
        signal_names: List[str] = []
        for entry in raw_entries:
            name = entry.split('(')[0].strip(' ;')
            signal_names.append(name)

        return VCSVHeader(signal_names)

    @staticmethod
    def value_token_index_from_logical(logical_idx: int) -> int:
        """
        Data line token layout:
          token[0] = time
          then for each signal j:
            token[1 + 2*j] = value for signal j
            token[2 + 2*j] = label (ignored)
        """
        return 1 + 2 * logical_idx


# -----------------------------
# Utilities for robust float/bool parsing
# -----------------------------

def _safe_float(tok: str) -> float:
    return float(tok)

def _to_bool_threshold(x: float, threshold: float) -> bool:
    return x > threshold


# -----------------------------
# Streaming analysis
# -----------------------------

def analyse_case_streaming(
    file_path_and_name: str,
    num_inputs: int,
    *,
    req_name_fmt: str,          # e.g. "/req_p<{idx}>" or "/req_s<{idx}>"
    req_indices: Iterable[int], # iterable of int indices for requests
    finish_signal_name: str,    # e.g. "/req_ack_out" or "/out_s<0>"
    energy_signal_name: str = "/V0/MINUS",
    threshold: float = 0.9,
    vdd: float = 1.8,
    integral_mode: str = "trapz",   # kept for API compatibility; streaming uses trapezoids
    verbose: bool = True,
    progress: bool = True,
) -> Dict[str, float]:
    """
    Single-pass streaming version with O(1) memory regardless of file size.
    Semantics match the original array implementation:
      - start at sample index of earliest first-true (include trapezoid from t[start] onward)
      - end at last falling-edge index (exclude trapezoid that ends exactly at that sample)
    """

    # Prepare request names list in a fixed order
    req_names = [req_name_fmt.format(idx=i) for i in req_indices]

    # State we’ll compute:
    first_true_time: Dict[str, Optional[float]] = {n: None for n in req_names}
    req_times_sum = 0.0
    req_times_count = 0
    start_time: Optional[float] = None  # earliest first-true among reqs

    falls_seen = 0
    finished_times: List[float] = []

    # Energy integration state
    in_window = False
    prev_time: Optional[float] = None
    prev_current: Optional[float] = None
    total_charge = 0.0
    last_area_added = 0.0  # track the most recent trapezoid area

    prev_finish_bool: Optional[bool] = None

    file_size = None
    try:
        file_size = os.path.getsize(file_path_and_name)
    except Exception:
        file_size = None

    bytes_read = 0

    with open(file_path_and_name, "r") as f:
        header = VCSVHeader.from_file(f)
        header_bytes = f.tell()  # bytes read after header
        bytes_read += header_bytes

        # Column lookups
        try:
            finish_logical_idx = header.name_to_idx[finish_signal_name]
        except KeyError:
            raise ValueError(f"Finish/Output signal '{finish_signal_name}' not found in header.")

        try:
            energy_logical_idx = header.name_to_idx[energy_signal_name]
        except KeyError:
            raise ValueError(f"Energy/current signal '{energy_signal_name}' not found in header.")

        req_logical_idxs: Dict[str, int] = {}
        for rn in req_names:
            if rn not in header.name_to_idx:
                raise ValueError(f"Request signal '{rn}' not found in header.")
            req_logical_idxs[rn] = header.name_to_idx[rn]

        # Map logical indices -> token indices on each data row
        finish_tok_idx = VCSVHeader.value_token_index_from_logical(finish_logical_idx)
        energy_tok_idx = VCSVHeader.value_token_index_from_logical(energy_logical_idx)
        req_tok_idx: Dict[str, int] = {
            n: VCSVHeader.value_token_index_from_logical(j)
            for n, j in req_logical_idxs.items()
        }

        pbar = None
        if progress and tqdm is not None and file_size:
            pbar = tqdm(total=file_size, unit="B", unit_scale=True, desc="Analysing VCSV", leave=False)
            pbar.update(bytes_read)

        for line in f:
            bytes_read += len(line)
            if tqdm is not None and pbar is not None:
                pbar.update(len(line))

            toks = line.rstrip("\n").split(',')

            # Time
            try:
                t = _safe_float(toks[0])
            except Exception:
                continue

            # Finish & energy values
            try:
                finish_val = _safe_float(toks[finish_tok_idx])
                energy_val = _safe_float(toks[energy_tok_idx])
            except Exception:
                continue

            finish_bool = _to_bool_threshold(finish_val, threshold)

            # First-true detection for req signals
            for rn, ti in req_tok_idx.items():
                if first_true_time[rn] is not None:
                    continue
                try:
                    vreq = _safe_float(toks[ti])
                except Exception:
                    continue
                if _to_bool_threshold(vreq, threshold):
                    first_true_time[rn] = t
                    req_times_sum += t
                    req_times_count += 1
                    if start_time is None or t < start_time:
                        start_time = t

            # --- Integration step with matched semantics ---
            # We want to include the trapezoid from t[start] to t[start+1].
            # That means: BEFORE computing the area at (prev_time -> t),
            # if prev_time >= start_time, we should be "in_window".
            if not in_window and start_time is not None and prev_time is not None and prev_time >= start_time:
                in_window = True

            # Compute trapezoid if we have a previous sample
            last_area_added = 0.0
            if prev_time is not None and prev_current is not None and in_window:
                dt = t - prev_time
                if dt > 0.0:
                    last_area_added = 0.5 * (prev_current + energy_val) * dt
                    total_charge += last_area_added

            # Detect falling edges on finish
            fall_now = (prev_finish_bool is not None and prev_finish_bool and not finish_bool)
            if fall_now:
                falls_seen += 1
                finished_times.append(t)

                if falls_seen >= num_inputs:
                    # Match array semantics: exclude the trapezoid that ENDS exactly at this sample.
                    # We just added that area (prev_time -> t), so remove it.
                    total_charge -= last_area_added
                    in_window = False  # stop further integration

            # Advance previous sample state
            prev_time = t
            prev_current = energy_val
            prev_finish_bool = finish_bool

        if tqdm is not None and pbar is not None:
            pbar.close()

    # Sanity checks & final metrics
    missing = [n for n, tt in first_true_time.items() if tt is None]
    if missing:
        raise ValueError(f"The following request signals never went high (>{threshold}): {missing}")

    if falls_seen == 0:
        raise ValueError(f"No falling edges found on '{finish_signal_name}'.")
    if falls_seen != num_inputs:
        raise AssertionError(
            f"Expected {num_inputs} falling edges on '{finish_signal_name}', found {falls_seen}."
        )

    req_time_mean = req_times_sum / float(req_times_count)
    finished_time_mean = sum(finished_times) / float(len(finished_times))
    mean_latency = finished_time_mean - req_time_mean

    energy = total_charge * vdd
    energy_per_input = energy / num_inputs

    if verbose:
        print("Mean_latency:", mean_latency)
        print("Energy per input:", energy_per_input)

    return {
        "mean_latency": mean_latency,
        "energy_total": energy,
        "energy_per_input": energy_per_input,
        "start_time": start_time if start_time is not None else float("nan"),
        "finished_time_mean": finished_time_mean,
        "falls_seen": float(falls_seen),
    }


# -----------------------------
# Convenience wrappers (same signatures as before)
# -----------------------------

def analyse_p(file_path_and_name: str, num_inputs: int, **kwargs):
    """Streaming wrapper for the 'p' case."""
    return analyse_case_streaming(
        file_path_and_name,
        num_inputs,
        req_name_fmt="/req_p<{idx}>",
        req_indices=range(1, num_inputs * 2, 2),
        finish_signal_name="/req_ack_out",
        **kwargs,
    )

def analyse_s(file_path_and_name: str, num_inputs: int, **kwargs):
    """Streaming wrapper for the 's' case."""
    return analyse_case_streaming(
        file_path_and_name,
        num_inputs,
        req_name_fmt="/req_s<{idx}>",
        req_indices=range(num_inputs),
        finish_signal_name="/out_s<0>",
        **kwargs,
    )


# -----------------------------
# Script entry (params + calls)
# Edit the file paths and params here before running:
# -----------------------------

if __name__ == "__main__":
    num_inputs = 5
    # Big files are fine here; this walks them once.
    file_path_and_name_p = ('/path/to/paer_nom_5.vcsv')
    file_path_and_name_s = ('/path/to/snbl_5.vcsv')

    print("Num inputs", num_inputs)

    print("P:")
    res_p = analyse_p(
        file_path_and_name_p,
        num_inputs,
        threshold=0.9,
        vdd=1.8,
        verbose=True,
        progress=True,   # progress bar (requires tqdm)
    )
    print(res_p)
    print()

    print("S:")
    res_s = analyse_s(
        file_path_and_name_s,
        num_inputs,
        threshold=0.9,
        vdd=1.8,
        verbose=True,
        progress=True,   # progress bar (requires tqdm)
    )
    print(res_s)
    print()

