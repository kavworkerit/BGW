#!/bin/bash

# Read the JSON input from stdin
input=$(cat)

# Extract needed information
model=$(echo "$input" | jq -r '.model.display_name // "Claude"')
current_dir=$(echo "$input" | jq -r '.workspace.current_dir // $(pwd)')
project_dir=$(echo "$input" | jq -r '.workspace.project_dir // ""')

# Convert to home directory notation if possible
if [[ "$current_dir" == /home/* ]]; then
    display_dir="~${current_dir#/home/[^/]*}"
else
    display_dir="$current_dir"
fi

# Get git information if in a git repository
git_info=""
if command -v git >/dev/null 2>&1; then
    git_dir=$(git rev-parse --git-dir 2>/dev/null)
    if [ -n "$git_dir" ]; then
        git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
        if [ -n "$git_branch" ] && [ "$git_branch" != "HEAD" ]; then
            git_info=" [$git_branch]"
        fi
    fi
fi

# Build the status line
printf "%s@%s:%s%s" "$(whoami)" "$(hostname -s)" "$display_dir" "$git_info"