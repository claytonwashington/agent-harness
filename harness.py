#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import shutil

def run_cmd(cmd, check=True):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True, check=check, text=True, capture_output=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr and check:
        print(res.stderr.strip(), file=sys.stderr)
    return res.stdout.strip()

def get_repo_root():
    try:
        return run_cmd("git rev-parse --show-toplevel")
    except subprocess.CalledProcessError:
        print("Error: Must be run inside a Git repository (or worktree/submodule).")
        sys.exit(1)

def update_idea_status(repo_root, idea_id, new_status):
    ideas_path = os.path.join(repo_root, "ideas.md")
    if not os.path.exists(ideas_path):
        print("Warning: ideas.md not found, skipping status update.")
        return

    with open(ideas_path, "r") as f:
        lines = f.readlines()

    out_lines = []
    in_target_idea = False
    for line in lines:
        if line.startswith(f"### {idea_id}."):
            in_target_idea = True
        elif line.startswith("### "):
            in_target_idea = False
            
        if in_target_idea and line.startswith("**Status**:"):
            out_lines.append(f"**Status**: {new_status}\n")
        else:
            out_lines.append(line)

    with open(ideas_path, "w") as f:
        f.writelines(out_lines)
    print(f"Updated ideas.md for Idea {idea_id} -> {new_status}")

def add_active_branch(repo_root, branch, worktree_path, idea_id, description):
    branches_path = os.path.join(repo_root, "branches.md")
    if not os.path.exists(branches_path):
        print("Warning: branches.md not found.")
        return

    with open(branches_path, "r") as f:
        content = f.read()

    table_header = "|--------|---------------|---------|-------------|--------|\n"
    if table_header in content:
        new_row = f"| {branch} | `{worktree_path}` | {idea_id} | {description} | Active |\n"
        content = content.replace(table_header, table_header + new_row)
        with open(branches_path, "w") as f:
            f.write(content)
        print("Added active branch to branches.md")
    else:
        print("Warning: Could not parse Active Work table in branches.md")

def complete_branch(repo_root, branch, result_notes):
    branches_path = os.path.join(repo_root, "branches.md")
    if not os.path.exists(branches_path):
        return

    with open(branches_path, "r") as f:
        lines = f.readlines()

    out_lines = []
    in_active = False
    in_completed = False
    active_row = None

    for line in lines:
        if "## Active Work" in line:
            in_active = True
            in_completed = False
        elif "## Completed Work" in line:
            in_active = False
            in_completed = True

        if in_active and line.startswith(f"| {branch} |"):
            active_row = line
            continue

        if in_completed and line.startswith("|--------|-------------|--------|"):
            out_lines.append(line)
            if active_row:
                parts = [p.strip() for p in active_row.split("|")]
                if len(parts) >= 6:
                    desc = parts[4]
                    out_lines.append(f"| {branch} | {desc} | {result_notes} |\n")
            continue

        out_lines.append(line)

    with open(branches_path, "w") as f:
        f.writelines(out_lines)
    print("Moved branch to completed section in branches.md")

def cmd_init(args):
    repo_root = get_repo_root()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(script_dir, "templates")
    
    if not os.path.exists(templates_dir):
        print(f"Error: Templates directory not found at {templates_dir}")
        sys.exit(1)
        
    for f in os.listdir(templates_dir):
        src = os.path.join(templates_dir, f)
        dst = os.path.join(repo_root, f)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            print(f"Initialized {f} in repository root.")
        else:
            print(f"File {f} already exists, skipping.")
    print("Initialization complete.")

def cmd_start(args):
    repo_root = get_repo_root()
    repo_name = os.path.basename(repo_root)
    
    safe_branch = args.branch.split("/")[-1]
    worktree_parent = os.path.abspath(os.path.join(repo_root, "..", f"{repo_name}-worktrees"))
    os.makedirs(worktree_parent, exist_ok=True)
    worktree_path = os.path.join(worktree_parent, safe_branch)
    
    run_cmd(f"git worktree add {worktree_path} -b {args.branch}")
    
    update_idea_status(repo_root, args.idea_id, "🔄 IN PROGRESS")
    
    rel_worktree = os.path.relpath(worktree_path, repo_root)
    add_active_branch(repo_root, args.branch, rel_worktree, args.idea_id, args.name)
    
    run_cmd("git add ideas.md branches.md")
    run_cmd(f"git commit -m \"preflight(start): task {args.idea_id} on {args.branch}\"")
    
    print(f"\nSuccessfully started task in worktree: {worktree_path}")

def cmd_complete(args):
    repo_root = get_repo_root()
    repo_name = os.path.basename(repo_root)
    
    run_cmd(f"git checkout {args.target_branch}")
    run_cmd(f"git merge {args.branch}")
    
    safe_branch = args.branch.split("/")[-1]
    worktree_path = os.path.abspath(os.path.join(repo_root, "..", f"{repo_name}-worktrees", safe_branch))
    run_cmd(f"git worktree remove {worktree_path} --force")
    run_cmd(f"git branch -d {args.branch}")
    
    status_map = {
        "completed": "✅ COMPLETE",
        "failed": "❌ FAILED",
        "abandoned": "❌ ABANDONED"
    }
    status_str = status_map[args.status]
    if args.idea_id:
        update_idea_status(repo_root, args.idea_id, status_str)
        
    complete_branch(repo_root, args.branch, f"{args.status}: {args.notes}")
    
    run_cmd("git add ideas.md branches.md")
    run_cmd(f"git commit -m \"preflight(complete): merged {args.branch}\"")
    
    print("\nSuccessfully completed task and cleaned up worktree.")

def main():
    parser = argparse.ArgumentParser(description="Agent Collaboration Harness")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    init_parser = subparsers.add_parser("init", help="Initialize templates in current repo")
    
    start_parser = subparsers.add_parser("start", help="Start a new task/experiment")
    start_parser.add_argument("--idea-id", required=True, help="ID of the idea from ideas.md")
    start_parser.add_argument("--branch", required=True, help="Branch name")
    start_parser.add_argument("--name", required=True, help="Descriptive name")
    
    complete_parser = subparsers.add_parser("complete", help="Complete a task/experiment")
    complete_parser.add_argument("--branch", required=True, help="Branch name to merge")
    complete_parser.add_argument("--target-branch", default="main", help="Branch to merge into (default: main)")
    complete_parser.add_argument("--status", required=True, choices=["completed", "failed", "abandoned"])
    complete_parser.add_argument("--notes", default="", help="Notes on the outcome")
    complete_parser.add_argument("--idea-id", help="Idea ID to mark complete (optional)")
    
    args = parser.parse_args()
    
    if args.command == "init":
        cmd_init(args)
    elif args.command == "start":
        cmd_start(args)
    elif args.command == "complete":
        cmd_complete(args)

if __name__ == "__main__":
    main()