import re
from pathlib import Path
from typing import Dict, List, Optional, Iterable, Tuple
import numpy as np
import pandas as pd

"""
Parser for BPM blocks formatted as:
("BPMNAME"-> {{x_values},{y_values},{z_values}})

- Joins numbers split across lines using a trailing backslash.
- Extracts all BPMs and returns numpy arrays.
"""

# Pattern for matching numbers
_NUM_RE = re.compile(r'[+-]?(?:\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?', re.DOTALL)

# Parentheses with double-curly arrays
_PATTERN = re.compile(
    r'\("\s*([^"]+)\s*"\s*->\s*'
    r'\{\s*\{\s*([^{}]*)\}\s*,\s*'
    r'\{\s*([^{}]*)\}\s*,\s*'
    r'\{\s*([^{}]*)\}\s*\}\s*'
    r'\)',
    re.DOTALL
)

def _join_line_continuations(s: str) -> str:
    # Turn "1234\\\n   5678" -> "12345678"
    return re.sub(r'\\\s*\n\s*', '', s)

# Class for parsing, reading, extracting and summarizing BPM data

class BPMDataParen:
    def __init__(self, data: Dict[str, Dict[str, np.ndarray]]):
        self._data = data

    # Method to read BPM data from a file
    @classmethod
    def from_file(cls, path: str) -> "BPMDataParen":
        p = Path(path)
        text = _join_line_continuations(p.read_text())
        results: Dict[str, Dict[str, np.ndarray]] = {}
        for m in _PATTERN.finditer(text):
            name = m.group(1)
            a1, a2, a3 = m.group(2), m.group(3), m.group(4)
            x = np.array([float(x) for x in _NUM_RE.findall(a1)], dtype=float)
            y = np.array([float(x) for x in _NUM_RE.findall(a2)], dtype=float)
            z = np.array([float(x) for x in _NUM_RE.findall(a3)], dtype=float)
            results[name] = {"x": x, "y": y, "z": z}
        return cls(results)

    # Method to return a list of all BPM names
    def list_bpms(self) -> List[str]:
        return sorted(self._data.keys())

    # Method to get BPM data for a specific component
    def get(self, bpm: str, component: str) -> np.ndarray:
        comp = component.lower().strip()
        if comp not in ("x", "y", "z"):
            raise ValueError("component must be 'x', 'y', or 'z'")
        return self._data[bpm][comp]

    # Method to summarize BPM lengths
    def summary_lengths(self) -> "pd.DataFrame":
        """
        Return a DataFrame with one row per BPM:
        columns = ['BPM', 'len_x', 'len_y', 'len_z'].
        """
        rows = []
        for name in self.list_bpms():
            x = self.get(name, "x")
            y = self.get(name, "y")
            z = self.get(name, "z")
            rows.append({
                "BPM": name,
                "len_x": int(x.size),
                "len_y": int(y.size),
                "len_z": int(z.size),
            })
        return pd.DataFrame(rows).sort_values("BPM").reset_index(drop=True)

    # Method to summarize BPM statistics
    def summary_stats(self, percentiles=(5, 50, 95)) -> "pd.DataFrame":
        """
        Return a tidy DataFrame with one row per (BPM, component),
        including n, mean, std, min, selected percentiles, and max.

        Parameters
        ----------
        percentiles : tuple of ints/floats in [0,100]
            Percentiles to include (e.g., (5,50,95)).
        """
        def stats_for(arr: np.ndarray):
            if arr.size == 0:
                base = dict(n=0, mean=np.nan, std=np.nan, min=np.nan, max=np.nan, median=np.nan)
                for p in percentiles:
                    base[f"p{int(p):02d}"] = np.nan
                return base
            out = dict(
                n=int(arr.size),
                mean=float(np.mean(arr)),
                std=float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0,
                min=float(np.min(arr)),
                max=float(np.max(arr)),
                median=float(np.median(arr)),
            )
            # add requested percentiles
            for p in percentiles:
                out[f"p{int(p):02d}"] = float(np.percentile(arr, p))
            return out

        rows = []
        for name in self.list_bpms():
            for comp in ("x", "y", "z"):
                st = stats_for(self.get(name, comp))
                st.update({"BPM": name, "component": comp})
                rows.append(st)

        cols_order = ["BPM", "component", "n", "mean", "std", "min"] \
                     + [f"p{int(p):02d}" for p in percentiles] \
                     + ["median", "max"]
        df = pd.DataFrame(rows)
        # keep consistent column order if all present
        df = df[[c for c in cols_order if c in df.columns]]
        return df.sort_values(["BPM", "component"]).reset_index(drop=True)

    # Method to write BPM .data to an sdds-like file
    def to_sdds(
        self,
        path: str,
        beam: str = "Unknown",
        ring_id: str = "",
        turns: Optional[int] = None,
        fmt: str = "{:.7g}",
        header_lines: Optional[Iterable[str]] = None,
    ) -> None:
        """
        Write an SDDS-like ASCII file with:
            0 BPM x1 x2 ... xN
            1 BPM y1 y2 ... yN

        'turns':
          - If None, uses the most common x length across BPMs.
          - Otherwise, all arrays are trimmed/padded to 'turns'.
        """
        names = self.list_bpms()
        lens = [self.get(n, "x").size for n in names]
        if turns is None:
            from collections import Counter
            turns = Counter(lens).most_common(1)[0][0] if lens else 0

        def normalize(a: np.ndarray, N: int) -> np.ndarray:
            if a.size > N: return a[:N]
            if a.size < N: return np.pad(a, (0, N - a.size), mode="constant")
            return a

        p = Path(path)
        with p.open("w", encoding="utf-8") as f:
            f.write("# SDDSASCIIFORMAT v1\n")
            f.write(f"# Beam: {beam}\n")
            if ring_id:
                f.write(f"# RingID: {ring_id}\n")
            f.write(f"# number of turns : {float(turns):16.7f}\n")
            f.write(f"# number of monitors : {float(len(names)):16.7f}\n")
            if header_lines:
                for line in header_lines:
                    f.write("# " + str(line).rstrip() + "\n")

            for name in names:
                x = normalize(self.get(name, "x"), turns)
                y = normalize(self.get(name, "y"), turns)
                if y.size == 0 and turns > 0:
                    y = np.zeros(turns, dtype=float)
                xs = " ".join(fmt.format(v) for v in x)
                ys = " ".join(fmt.format(v) for v in y)
                f.write(f"0 {name} {xs}\n")
                f.write(f"1 {name} {ys}\n")




"""
Parser for SDDS-like lines:
  # ... (metadata to skip)
  0 BPM_NAME <numbers ...>   -> component x
  1 BPM_NAME <numbers ...>   -> component y
(No z provided; we synthesize z as zeros_like(x) to maintain x/y/z API.)
"""

# Pattern for matching numbers
_NUM_RE = re.compile(r'[+-]?(?:\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?')

# Class for parsing, reading, extracting and summarizing BPM sdds data
class BPMDataSDDS:
    def __init__(self, data: Dict[str, Dict[str, np.ndarray]]):
        self._data = data

    # Method to read BPM data from a sdds file
    @classmethod
    def from_file(cls, path: str) -> "BPMDataSDDS":
        p = Path(path)
        text = p.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()

        acc: Dict[str, Dict[str, list]] = {}

        for raw in lines:
            s = raw.strip()
            if not s or s.startswith("#"):
                continue

            # Expect: N <name> <numbers...>
            parts = s.split(None, 2)  # split into at most 3 fields
            if len(parts) < 3:
                continue

            n_str, name, payload = parts[0], parts[1], parts[2]
            if n_str not in ("0", "1"):
                continue

            comp = "x" if n_str == "0" else "y"

            # Extract numbers; tolerate commas or spaces
            nums = [float(tok) for tok in _NUM_RE.findall(payload)]
            if not nums:
                continue

            if name not in acc:
                acc[name] = {"x": [], "y": []}
            acc[name][comp].extend(nums)

        # Build final dict; synthesize z = zeros_like(x)
        results: Dict[str, Dict[str, np.ndarray]] = {}
        for name, comps in acc.items():
            x_arr = np.asarray(comps["x"], dtype=float)
            y_arr = np.asarray(comps["y"], dtype=float)

            # If one is missing, mirror with zeros
            if x_arr.size == 0 and y_arr.size > 0:
                x_arr = np.zeros_like(y_arr)
            if y_arr.size == 0 and x_arr.size > 0:
                y_arr = np.zeros_like(x_arr)

            z_arr = np.zeros_like(x_arr)
            results[name] = {"x": x_arr, "y": y_arr, "z": z_arr}

        return cls(results)

    # Method to return a list of all BPM names
    def list_bpms(self) -> List[str]:
        return sorted(self._data.keys())

    # Method to get BPM data for a specific component
    def get(self, bpm: str, component: str) -> np.ndarray:
        comp = component.lower().strip()
        if comp not in ("x", "y", "z"):
            raise ValueError("component must be 'x', 'y', or 'z'")
        if bpm not in self._data:
            raise KeyError(f"BPM '{bpm}' not found. Available: {', '.join(self.list_bpms())}")
        return self._data[bpm][comp]

    # Method to summarize BPM lengths
    def summary_lengths(self) -> pd.DataFrame:
        """
        Return a DataFrame with one row per BPM:
        columns = ['BPM', 'len_x', 'len_y', 'len_z'].
        """
        rows = []
        for name in self.list_bpms():
            x = self.get(name, "x")
            y = self.get(name, "y")
            z = self.get(name, "z")
            rows.append({"BPM": name, "len_x": int(x.size), "len_y": int(y.size), "len_z": int(z.size)})
        return pd.DataFrame(rows).sort_values("BPM").reset_index(drop=True)

    # Method to summarize BPM statistics
    def summary_stats(self, percentiles: tuple[float, ...] = (5, 50, 95)) -> pd.DataFrame:
        """
        Return a tidy DataFrame with one row per (BPM, component),
        including n, mean, std, min, selected percentiles, median, and max.

        Parameters
        ----------
        percentiles : tuple of ints/floats in [0,100]
            Percentiles to include (e.g., (5,50,95)).
        """
        def stats_for(arr: np.ndarray) -> dict:
            if arr.size == 0:
                base = dict(n=0, mean=np.nan, std=np.nan, min=np.nan, max=np.nan, median=np.nan)
                for p in percentiles:
                    base[f"p{int(p):02d}"] = np.nan
                return base
            out = dict(
                n=int(arr.size),
                mean=float(np.mean(arr)),
                std=float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0,
                min=float(np.min(arr)),
                max=float(np.max(arr)),
                median=float(np.median(arr)),
            )
            for p in percentiles:
                out[f"p{int(p):02d}"] = float(np.percentile(arr, p))
            return out

        rows = []
        for name in self.list_bpms():
            for comp in ("x", "y", "z"):
                st = stats_for(self.get(name, comp))
                st.update({"BPM": name, "component": comp})
                rows.append(st)

        cols_order = ["BPM", "component", "n", "mean", "std", "min"] \
                     + [f"p{int(p):02d}" for p in percentiles] \
                     + ["median", "max"]
        df = pd.DataFrame(rows)
        df = df[[c for c in cols_order if c in df.columns]]
        return df.sort_values(["BPM", "component"]).reset_index(drop=True)

    # Method to write BPM sdds data to an .data-like file
    def to_data(
        self,
        path: str,
        include_z: bool = True,
        fmt: str = "{:.7g}",
        sep: str = ",",
        columns: int = 6,
        z_fill: float = 0.0010580705711618066,
        indent: str = "        ",
        scale: float = 1e0,
        header_lines: Optional[Iterable[str]] = None,
    ) -> None:
        """
        Write .data parentheses blocks:
           ("BPM" -> {{x_values}, {y_values}, {z_values}})

        wrap: if set (e.g., 16), inserts a backslash-newline after every 'wrap' values.
        """
        def fmt_array(a: np.ndarray) -> str:
            vals = [fmt.format(v) for v in a]
            if columns and columns > 0:
                lines = []
                for i in range(0, len(vals), columns):
                    lines.append(sep.join(vals[i:i + columns]))
                if not lines:
                    return ""
                # join with newline + indent; no trailing backslashes
                return (",\n").join(lines)
            # single line (no column formatting)
            return sep.join(vals)

        p = Path(path)
        with p.open("w", encoding="utf-8") as f:
            if header_lines:
                f.write("{{")
                for line in header_lines:
                    f.write(str(line).rstrip())
                f.write("},\n")

            f.write("{")
            names = self.list_bpms()
            for idx, name in enumerate(names):
                x = self.get(name, "x")*scale
                y = self.get(name, "y")*scale
                z = np.full_like(x, z_fill, dtype=float)*scale if include_z else np.zeros_like(x)

                # NOTE: you had [1:] here; keeping it, but remove if you don't want to drop the first sample (s position of BPM along accelerator)
                sx = fmt_array(x[1:])
                sy = fmt_array(y[1:])
                sz = fmt_array(z[1:])

                entry = f'("{name}"->\n{{{{{sx}}},\n{{{sy}}},\n{{{sz}}}}})'
                if idx < len(names) - 1:
                    f.write(entry + ",\n")   # add comma for all but the last
                else:
                    f.write(entry + "\n")    # no trailing comma for the last
            f.write("}")
            if header_lines:
                f.write("}")

