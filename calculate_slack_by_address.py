import math
import pandas as pd

def queued_lengths(addr: int) -> list[int]:
    """
    Return the list of 'length blocks' actually queued for address `addr`,
    following the same packing rule as before.

    Rules:
      - total slack ahead = addr - 0.5
      - the length at router position r is L(r) = floor(log2(addr - r + 1)) + 1
      - greedily pack contiguous blocks of length L(r) until slack is exhausted
      - if the first block doesn't fit, return []
    """
    total_slack = addr - 0.5
    L1 = math.floor(math.log2(addr)) + 1
    if total_slack < L1:
        return []

    used = 0.0
    r = 1
    blocks = []
    while r <= addr:
        Lr = math.floor(math.log2(addr - r + 1)) + 1
        if used + Lr <= total_slack:
            blocks.append(Lr)
            used += Lr
            r += Lr
        else:
            break
    return blocks

def capacity(addr: int) -> int:
    return len(queued_lengths(addr))

if __name__ == "__main__":
    N = 1581
    df = pd.DataFrame({"addr": range(1, N + 1)})
    df["slack_ahead"] = df["addr"] - 0.5
    df["len_addr"] = df["addr"].apply(lambda a: math.floor(math.log2(a)) + 1)
    df["queued_lengths"] = df["addr"].apply(queued_lengths)
    df["capacity"] = df["queued_lengths"].apply(len)

    # Sanity checks from your examples
    examples = {1:0, 2:0, 3:1, 4:1, 5:1, 6:2}
    for a, expect in examples.items():
        got = df.loc[df.addr == a, "capacity"].item()
        assert got == expect, f"addr {a}: expected {expect}, got {got}"

    # Show a small illustrative slice
    demo_addrs = list(range(1, 21)) + [31, 32, 63, 64, 65, 127, 128, 129]
    demo = df[df.addr.isin(demo_addrs)][["addr", "slack_ahead", "len_addr", "queued_lengths", "capacity"]]
    print(demo.to_string(index=False))

    # Save CSV with a readable 'queued_lengths_str'
    df_out = df.copy()
    df_out["queued_lengths_str"] = df_out["queued_lengths"].apply(lambda L: "[" + ", ".join(map(str, L)) + "]")
    df_out.drop(columns=["queued_lengths"], inplace=True)
    out_csv = "address_capacity_with_blocks_1_1581.csv"
    df_out.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    # (Optional) averages up to thresholds
    thresholds = [5, 16, 50, 158, 500, 1581]
    averages = {t: df.loc[df.addr <= t, "capacity"].mean() for t in thresholds}
    print("\nMean capacity up to thresholds (inclusive):")
    for t in thresholds:
        print(f"  ≤ {t:4d}: {averages[t]}")
