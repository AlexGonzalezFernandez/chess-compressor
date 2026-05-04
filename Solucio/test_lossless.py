#!/usr/bin/env python3
#
# Passa tots els .pgn del directori de tests pel compressor i comprova que
# comprimir + descomprimir torna exactament el fitxer original (comparant
# el sha256). Alhora mesura temps per calcular kB/s.
#
# Us: python3 test_lossless.py [directori_de_tests]
# Per defecte busca a ../SetPartidesTests

import hashlib
import subprocess
import sys
import tempfile
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXE  = HERE / "compress.cdi"
DEFAULT_TESTS = HERE.parent / "SetPartidesTests"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd):
    t0 = time.perf_counter()
    r  = subprocess.run(cmd, capture_output=True)
    dt = time.perf_counter() - t0
    if r.returncode != 0:
        sys.stderr.write(r.stderr.decode(errors="replace"))
        raise SystemExit("comanda ha fallat: %s" % cmd)
    return dt


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return "%.1f %s" % (n, unit)
        n /= 1024
    return "%.1f TB" % n


def test_one(pgn_path):
    orig_size = pgn_path.stat().st_size
    orig_sha  = sha256(pgn_path)

    with tempfile.TemporaryDirectory() as tmpd:
        tmpd = Path(tmpd)
        cdi  = tmpd / (pgn_path.name + ".cdi")
        back = tmpd / (pgn_path.name + ".back")

        t_c = run([str(EXE), str(pgn_path), str(cdi)])
        comp_size = cdi.stat().st_size

        t_d = run([str(EXE), str(cdi), str(back)])
        back_sha = sha256(back)

    return {
        "name" : pgn_path.name,
        "orig" : orig_size,
        "comp" : comp_size,
        "ratio": (orig_size / comp_size) if comp_size else float("inf"),
        "ok"   : orig_sha == back_sha,
        "c_kbs": (orig_size / t_c / 1024) if t_c else float("inf"),
        "d_kbs": (orig_size / t_d / 1024) if t_d else float("inf"),
    }


def main():
    tests_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TESTS
    if not tests_dir.is_dir():
        sys.stderr.write("no existeix el directori: %s\n" % tests_dir)
        return 1
    if not EXE.exists():
        sys.stderr.write("no trobo l'executable: %s\n" % EXE)
        return 1

    pgns = sorted(tests_dir.glob("*.pgn"))
    if not pgns:
        sys.stderr.write("cap .pgn a %s\n" % tests_dir)
        return 1

    total_orig = 0
    total_comp = 0
    all_ok = True

    print("%-22s %10s %10s %7s %9s %9s  ok" %
          ("fitxer", "original", "comprimit", "ratio", "c kB/s", "d kB/s"))
    print("-" * 78)

    for p in pgns:
        r = test_one(p)
        total_orig += r["orig"]
        total_comp += r["comp"]
        all_ok = all_ok and r["ok"]
        print("%-22s %10s %10s %7.3f %9.1f %9.1f  %s" %
              (r["name"], human(r["orig"]), human(r["comp"]),
               r["ratio"], r["c_kbs"], r["d_kbs"],
               "ok" if r["ok"] else "FAIL"))

    print("-" * 78)
    total_ratio = (total_orig / total_comp) if total_comp else float("inf")
    print("%-22s %10s %10s %7.3f" %
          ("TOTAL", human(total_orig), human(total_comp), total_ratio))

    exe_size = EXE.stat().st_size + (HERE / "compress.src").stat().st_size
    penalty  = max(0, exe_size - 250 * 1024)
    R = total_orig / (total_comp + penalty)

    print()
    print("mida executable (.cdi + .src): %s  (penalitzacio: %s)" %
          (human(exe_size), human(penalty)))
    print("R = %.3f" % R)
    print("lossless: %s" %
          ("tot identic" if all_ok else "HI HA DIFERENCIES"))

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
