import os
import subprocess
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    print("=" * 70)
    print("[VERIDION CI/CD] Running Local Testing Pipeline...")
    print("=" * 70)

    # Detect python executable in venv
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_python_win = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
    venv_python_posix = os.path.join(root_dir, ".venv", "bin", "python")

    if os.path.exists(venv_python_win):
        python_bin = venv_python_win
    elif os.path.exists(venv_python_posix):
        python_bin = venv_python_posix
    else:
        python_bin = sys.executable

    # 1. Run pytest test suite
    print(f"\n[1/2] Executing pytest test suite using: {python_bin}")
    cmd = [python_bin, "-m", "pytest", "backend/tests", "-v"]
    result = subprocess.run(cmd, cwd=root_dir)

    if result.returncode != 0:
        print("\n[ERROR] [VERIDION CI/CD] Tests failed! Aborting git push.")
        sys.exit(result.returncode)

    # 2. Run benchmark evaluation verification
    print("\n[2/2] Verifying reproducible evaluation benchmark (20 scenarios)...")
    bench_cmd = [
        python_bin,
        "-c",
        "from backend.app.services.evaluation_service import EvaluationService; s = EvaluationService.evaluate_all(); print(f'Evaluated {s.total_scenarios} scenarios successfully. Full protocol recall: {s.metrics[\"VERIDION_PROTOCOL\"][\"avg_issue_recall\"]}')"
    ]
    bench_result = subprocess.run(bench_cmd, cwd=root_dir)

    if bench_result.returncode != 0:
        print("\n[ERROR] [VERIDION CI/CD] Benchmark evaluation check failed!")
        sys.exit(bench_result.returncode)

    print("\n" + "=" * 70)
    print("[SUCCESS] [VERIDION CI/CD] All local pre-push checks passed successfully!")
    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
