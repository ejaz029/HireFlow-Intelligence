from pathlib import Path
import hashlib

def checksums(folder: str | Path) -> dict[str, str]:
    root = Path(folder)
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.glob("*.csv"))}

def compare_runs(first: str | Path, second: str | Path) -> dict:
    a, b = checksums(first), checksums(second)
    return {"identical": a == b, "first": a, "second": b, "different_files": sorted(set(a) | set(b) - {k for k in a.keys() & b.keys() if a[k] == b[k]})}
