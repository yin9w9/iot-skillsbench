#!/usr/bin/env python3
"""
Auto test for STM32F746 + STM32CubeHAL.

Flow:
1. Run batch_run.py to generate code.
2. Find latest generated output/Core/Src/main.c.
3. Copy generated main.c into an existing STM32CubeIDE project.
4. Build project with STM32CubeIDE headless build.
5. Flash ELF with STM32_Programmer_CLI.
6. Ask user for behavioral pass/fail.

Example:
python scripts/auto_test_stm32.py ^
  -i tasks/level1/level1-stm32f746-STM32CubeHAL.txt ^
  -t Random_LCD_Button ^
  --stm32-project C:/Users/ddoll/STM32CubeIDE/workspace_1.16.0/F746_Test ^
  --cubeide "C:/ST/STM32CubeIDE_1.16.0/STM32CubeIDE/stm32cubeidec.exe" ^
  --programmer "C:/Program Files/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI.exe"
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent


def load_config_and_output_dir(config_path: str, output_base: str | None) -> tuple[dict, str]:
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    board = config.get("input", {}).get("board", "stm32f746")
    framework = config.get("input", {}).get("framework", "STM32CubeHAL")
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
        str(PROJECT_ROOT / "batch_run.py"),
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


def copy_generated_main_to_cube_project(generated_output: Path, stm32_project: Path) -> bool:
    candidates = [
        generated_output / "Core" / "Src" / "main.c",
        generated_output / "main.c",
        generated_output / "src" / "main.c",
    ]

    generated_main = None
    for candidate in candidates:
        if candidate.exists():
            generated_main = candidate
            break

    if generated_main is None:
        print("ERROR: could not find generated main.c in:")
        print(generated_output)
        return False

    target_main = stm32_project / "Core" / "Src" / "main.c"
    if not target_main.exists():
        print("ERROR: target CubeIDE main.c does not exist:")
        print(target_main)
        return False

    backup_main = target_main.with_suffix(".c.bak")
    shutil.copy2(target_main, backup_main)
    shutil.copy2(generated_main, target_main)

    print(f"Copied generated main.c:")
    print(f"  from: {generated_main}")
    print(f"  to:   {target_main}")
    print(f"Backup saved:")
    print(f"  {backup_main}")

    return True


def build_cubeide_project(cubeide: Path, workspace: Path, project_name: str) -> bool:
    cmd = [
        str(cubeide),
        "--launcher.suppressErrors",
        "-nosplash",
        "-application", "org.eclipse.cdt.managedbuilder.core.headlessbuild",
        "-data", str(workspace),
        "-cleanBuild", project_name,
    ]

    print("Building STM32 project:")
    print(" ".join(cmd))

    result = subprocess.run(cmd)
    return result.returncode == 0


def find_elf(stm32_project: Path) -> Path | None:
    elf_files = list(stm32_project.rglob("*.elf"))
    if not elf_files:
        return None
    return max(elf_files, key=lambda p: p.stat().st_mtime)


def flash_stm32(programmer: Path, elf_path: Path) -> bool:
    cmd = [
        str(programmer),
        "-c", "port=SWD",
        "-w", str(elf_path),
        "-v",
        "-rst",
    ]

    print("Flashing STM32:")
    print(" ".join(cmd))

    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Auto test STM32F746 + STM32CubeHAL generated code.")
    parser.add_argument("-i", "--input", required=True, help="Input task list file")
    parser.add_argument("-t", "--task", required=True, help="Task ID")
    parser.add_argument("-c", "--config", default="config.yaml", help="Config file")
    parser.add_argument("-o", "--output", default="output/auto_test_stm32", help="Output base directory")

    parser.add_argument("--stm32-project", required=True, help="Path to existing STM32CubeIDE project")
    parser.add_argument("--workspace", required=True, help="STM32CubeIDE workspace path")
    parser.add_argument("--project-name", required=True, help="STM32CubeIDE project name")

    parser.add_argument("--cubeide", required=True, help="Path to stm32cubeidec.exe")
    parser.add_argument("--programmer", required=True, help="Path to STM32_Programmer_CLI.exe")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path

    stm32_project = Path(args.stm32_project)
    workspace = Path(args.workspace)
    cubeide = Path(args.cubeide)
    programmer = Path(args.programmer)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}")
        sys.exit(1)

    if not stm32_project.exists():
        print(f"ERROR: STM32 project not found: {stm32_project}")
        sys.exit(1)

    if not cubeide.exists():
        print(f"ERROR: CubeIDE command not found: {cubeide}")
        sys.exit(1)

    if not programmer.exists():
        print(f"ERROR: STM32 programmer not found: {programmer}")
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

    if not copy_generated_main_to_cube_project(generated_output, stm32_project):
        sys.exit(1)

    if not build_cubeide_project(cubeide, workspace, args.project_name):
        print("ERROR: STM32CubeIDE build failed")
        sys.exit(1)

    elf_path = find_elf(stm32_project)
    if elf_path is None:
        print("ERROR: no .elf file found after build")
        sys.exit(1)

    print(f"Found ELF: {elf_path}")

    if not flash_stm32(programmer, elf_path):
        print("ERROR: STM32 flash failed")
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