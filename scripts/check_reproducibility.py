from pathlib import Path
import hashlib, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
BACKEND=ROOT/"backend"
OUT=ROOT/"data"/"repro_check_a"
TMP=ROOT/"data"/"repro_check_b"
GT=ROOT/"data"/"ground_truth"
GT_A=ROOT/"data"/"repro_check_a_ground_truth"
GT_B=ROOT/"data"/"repro_check_b_ground_truth"
def digest(folder):
    files=[p for p in folder.iterdir() if p.is_file() and p.suffix in {".csv", ".json", ".sql"}]
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
def run():
    for folder in (OUT,TMP,GT_A,GT_B):
        if folder.exists(): shutil.rmtree(folder)
    subprocess.run([sys.executable,"-m","generator.generate","--scale","full","--seed","20261022","--output",str(OUT)],cwd=BACKEND,check=True,stdout=subprocess.DEVNULL)
    shutil.copytree(GT,GT_A)
    first={"data":digest(OUT),"ground_truth":digest(GT_A)}
    subprocess.run([sys.executable,"-m","generator.generate","--scale","full","--seed","20261022","--output",str(TMP)],cwd=BACKEND,check=True,stdout=subprocess.DEVNULL)
    shutil.copytree(GT,GT_B)
    second={"data":digest(TMP),"ground_truth":digest(GT_B)}
    assert first==second, "Same-seed generated export checksums differ"
    print(f"PASS: {len(first['data']) + len(first['ground_truth'])} generated exports have identical SHA-256 checksums")
if __name__=="__main__": run()
