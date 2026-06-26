# Agent Collaboration Harness

This framework is designed to enable parallel, organized, and simultaneous agent (and human) collaboration in complex repositories. By isolating workspaces and strictly managing experiment lifecycles, we eliminate merge conflicts and ensure complete provenance for all work.

## Core Principles

1. **Total Workspace Isolation**: Every parallel experiment or task must be performed in a dedicated Git worktree. Agents should never share a local checkout.
2. **Experiment Provenance**: No task starts without an entry in the ideas tracker, and no task ends without updating it.
3. **Automated Completion**: When a task is done, the harness scripts handle merging and worktree cleanup.

## Environment & Infrastructure

- **Machines**: Coordinate with your team/agents to know which machines (e.g., gpu1, gpu2) and which storage (e.g., NAS) to use.
- **NAS Storage**: Code should ideally live on a shared network drive so it is accessible from all compute nodes.
- **tmux**: All long-running tasks, model training, or extensive data processing MUST run inside a `tmux` session to survive network disconnects.
  - Start: `tmux new-session -d -s <session_name> "your command"`
  - Attach: `tmux attach -t <session_name>`

## The Workflow

### 1. Before Starting
- Review `task.md` and `branches.md` to see what is currently active.
- Identify an open task in `ideas.md`.

### 2. Preflight (Starting a Task)
Use the harness script to create a worktree and reserve your branch:
```bash
python harness.py start --idea-id 42 --branch feature/my-new-idea --name "Testing new architecture"
```
This will:
- Check out a new branch and Git worktree in the `-worktrees/` directory.
- Generate a preflight token/manifest for your run.
- Update `branches.md` to reflect your active work.

### 3. Execution
- Change directory into your newly created worktree.
- Run all your code (e.g., training, sweeps) inside a `tmux` session.
- Keep your changes confined to this worktree.

### 4. Completion (Postflight)
Once your experiment or task is complete, run the postflight step from the **main repository checkout** (NOT the worktree):
```bash
cd /path/to/main/repo
python harness.py complete --branch feature/my-new-idea --status completed --notes "Achieved 95% accuracy"
```
This will:
- Merge your branch back into the main development branch.
- Remove the worktree.
- Update `ideas.md` and `branches.md` to mark the task as finished.