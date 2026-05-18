#!/usr/bin/env python3
"""
Auto test for TI MSP430 + MSP430-GCC.

Flow:
1. Run batch_run.py to generate main.c and Makefile.
2. Build with make.
3. Flash with mspdebug.
4. Ask user for behavioral pass/fail.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def load_config_and_output_dir(config_path: str, output_base: str | None) -> tuple[dict, str]:
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    board = config.get("input", {}).get("board", "ti_msp430")
    framework = config.get("input", {}).get("framework", "MSP430-GCC")
    use_skills = config.get("graph", {}).get("use_skills", True)
    skills_dir = config.get("graph", {}).get("skills_dir", "skills-human-expert")
    model_name = config.get("model", {}).get("name", "claude-sonnet-4.5")

    if output_base:
        base_name = output_base
    else:
        base_name = os.path.join("output", f"tasks-{board}-{framework}")

    if use_skills:
        skills_dir_name = os.path.basename(str(skills_dir).rstrip("/"))
        skill_suffix = f"w_skills_{skills_dir_name}"
    else:
        skill_suffix = "wo_skills"

    output_dir = os.path.join(base_name, skill_suffix, model_name)
    return config, output_dir


def find_latest_run_output(output_dir: str, task_id: str) -> Path | None:
    runs_dir = Path(output_dir) / task_id / "runs"
    if not runs_dir.exists():
        return None

    subdirs = [d for d in runs_dir.iterdir() if d.is_dir()]
    if not subdirs:
        return None

    latest = max(subdirs, key=lambda p: p.stat().st_mtime)
    return latest / "output"


def run_batch(input_file: str, task_id: str, config_path: str, output_base: str | None) -> bool:
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "batch_run.py"),
        "-i", input_file,
        "-t", task_id,
    ]

    if output_base:
        cmd.extend(["-o", output_base])

    if config_path:
        cmd.extend(["-c", config_path])

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode == 0


# def run_make(output_path: Path, mcu: str, make_cmd: str) -> bool:
#     cmd = [make_cmd, f"MCU={mcu}"]

#     print("Building MSP430 project:")
#     print(" ".join(cmd))

#     result = subprocess.run(cmd, cwd=output_path)
#     return result.returncode == 0

def run_make(output_path: Path, mcu: str, make_cmd: str) -> bool:
    ti_cgt_root = Path(r"C:\ti\ccs2051\ccs\tools\compiler\ti-cgt-msp430_21.6.1.LTS")
    ccs_msp430_include = Path(r"C:\ti\ccs2051\ccs\ccs_base\msp430\include")

    cl430_path = ti_cgt_root / "bin" / "cl430.exe"
    ti_cgt_include = ti_cgt_root / "include"
    ti_cgt_lib = ti_cgt_root / "lib"
    linker_cmd = ccs_msp430_include / "lnk_msp430fr5994.cmd"

    cmd = [
        str(cl430_path),
        "-vmspx",
        "--code_model=large",
        "--data_model=restricted",
        "--opt_level=2",
        "--printf_support=minimal",
        "--diag_warning=225",
        f"--include_path={ccs_msp430_include}",
        f"--include_path={ti_cgt_include}",
        "--define=__MSP430FR5994__",
        "main.c",
        "-z",
        "--rom_model",
        f"--search_path={ti_cgt_lib}",
        str(linker_cmd),
        "-o",
        "main.out",
    ]

    print("Building MSP430 project with TI cl430:")
    print(" ".join(cmd))

    result = subprocess.run(cmd, cwd=output_path)
    return result.returncode == 0

# def flash_msp430(output_path: Path, elf_name: str, debugger: str, driver: str) -> bool:
#     elf_path = output_path / elf_name
#     if not elf_path.exists():
#         print(f"ERROR: ELF not found: {elf_path}")
#         return False

#     cmd = [
#         debugger,
#         driver,
#         f"prog {elf_name}",
#     ]

#     print("Flashing MSP430:")
#     print(" ".join(cmd))

#     result = subprocess.run(cmd, cwd=output_path)
    # return result.returncode == 0

def flash_msp430(output_path: Path, elf_name: str, debugger: str, driver: str) -> bool:
    out_path = (output_path / elf_name).resolve()
    if not out_path.exists():
        print(f"ERROR: output file not found: {out_path}")
        return False

    dslite_path = Path(
        r"C:\ti\ccs2051\ccs\ccs_base\DebugServer\bin\DSLite.exe"
    ).resolve()

    ccxml_path = (SCRIPTS_DIR / "MSP430FR5994.ccxml").resolve()

    if not dslite_path.exists():
        print(f"ERROR: DSLite not found: {dslite_path}")
        return False

    if not ccxml_path.exists():
        print(f"ERROR: CCXML target config not found: {ccxml_path}")
        return False

    cmd = [
        str(dslite_path),
        "flash",
        f"--config={str(ccxml_path)}",
        str(out_path),
    ]

    print("Flashing MSP430 with DSLite:")
    print(" ".join(cmd))

    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Auto test TI MSP430 + MSP430-GCC generated code.")

    parser.add_argument("-i", "--input", required=True, help="Input task list file")
    parser.add_argument("-t", "--task", required=True, help="Task ID")
    parser.add_argument("-c", "--config", default="config.yaml", help="Config file")
    parser.add_argument("-o", "--output", default="output/auto_test_msp430_gcc", help="Output base directory")

    parser.add_argument("--mcu", default="msp430fr5994", help="MSP430 MCU name for compiler")
    parser.add_argument("--make", default="make", help="Make command")
    parser.add_argument("--debugger", default="mspdebug", help="mspdebug executable")
    parser.add_argument("--driver", default="tilib", help="mspdebug driver, e.g., tilib or rf2500")
    parser.add_argument("--elf", default="main.out", help="Output file name")
    parser.add_argument("--build-only", action="store_true", help="Only build; do not flash")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}")
        sys.exit(1)

    _, output_dir = load_config_and_output_dir(args.config, args.output)

    print(f"Task: {args.task}")
    print(f"Output dir: {output_dir}")

    if not run_batch(str(input_path), args.task, args.config, args.output):
        print("ERROR: batch_run.py failed")
        sys.exit(1)

    generated_output = find_latest_run_output(output_dir, args.task)
    if generated_output is None or not generated_output.exists():
        print("ERROR: no generated output found")
        sys.exit(1)

    if not (generated_output / "main.c").exists():
        print(f"ERROR: generated main.c not found in {generated_output}")
        sys.exit(1)

    if not (generated_output / "Makefile").exists():
        print(f"ERROR: generated Makefile not found in {generated_output}")
        sys.exit(1)

    if not run_make(generated_output, args.mcu, args.make):
        print("ERROR: MSP430-GCC build failed")
        sys.exit(1)

    if args.build_only:
        print("Compile success.")
        sys.exit(0)

    if not flash_msp430(generated_output, args.elf, args.debugger, args.driver):
        print("ERROR: MSP430 flash failed")
        sys.exit(1)

    print("Flash success.")

    while True:
        choice = input("Behavior: (s)uccess or (f)ail? ").strip().lower()
        if choice in ("s", "success"):
            print("Pass")
            sys.exit(0)
        if choice in ("f", "fail"):
            print("Behavioral Fail")
            sys.exit(1)
        print("Please enter s or f.")


if __name__ == "__main__":
    main()