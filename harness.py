#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os

def run_cmd(cmd, check=True):
    print(f"Running: {cmd}")
    return subprocess.run(cmd, shell=True, check=check, text=True)

def start(args):
    print(f"Starting task {args.idea_id} on branch {args.branch}")
    
    # 1. Ensure we are in a git repository
    if not os.path.isdir('.git'):
        print("Error: Must be run from the root of a Git repository.")
        sys.exit(1)
        
    # 2. Add worktree
    worktree_path = f"../{os.path.basename(os.getcwd())}-worktrees/{args.branch.split('/')[-1]}"
    run_cmd(f"git worktree add {worktree_path} -b {args.branch}")
    
    print(f"\nSuccessfully created worktree at {worktree_path}")
    print("Remember to update branches.md and your ideas tracker!")

def complete(args):
    print(f"Completing task on branch {args.branch}")
    
    # 1. Merge the branch
    run_cmd(f"git merge {args.branch}")
    
    # 2. Remove the worktree
    worktree_path = f"../{os.path.basename(os.getcwd())}-worktrees/{args.branch.split('/')[-1]}"
    run_cmd(f"git worktree remove {worktree_path} --force")
    
    # 3. Delete the branch
    run_cmd(f"git branch -d {args.branch}")
    
    print("\nSuccessfully completed task and cleaned up worktree.")
    print("Remember to update branches.md and mark your idea as complete!")

def main():
    parser = argparse.ArgumentParser(description="Agent Collaboration Harness")
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Start command
    start_parser = subparsers.add_parser('start', help="Start a new task/experiment")
    start_parser.add_argument('--idea-id', required=True, help="ID of the idea from ideas.md")
    start_parser.add_argument('--branch', required=True, help="Branch name (e.g., feature/my-idea)")
    start_parser.add_argument('--name', required=True, help="Descriptive name of the task")
    
    # Complete command
    complete_parser = subparsers.add_parser('complete', help="Complete a task/experiment")
    complete_parser.add_argument('--branch', required=True, help="Branch name to merge and clean up")
    complete_parser.add_argument('--status', required=True, choices=['completed', 'failed', 'abandoned'])
    complete_parser.add_argument('--notes', default='', help="Notes on the outcome")
    
    args = parser.parse_args()
    
    if args.command == 'start':
        start(args)
    elif args.command == 'complete':
        complete(args)

if __name__ == '__main__':
    main()