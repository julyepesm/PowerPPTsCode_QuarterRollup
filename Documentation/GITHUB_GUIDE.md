# Basic Git and GitHub Guide

This guide contains the essential Git and GitHub commands and concepts so you can manage your repository autonomously without spending AI tokens.

## 1. Initial Configuration
If you just installed Git, you need to configure your name and email (the one you use on GitHub):
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

## 2. Basic Daily Operations

### Check the status of your files
```bash
git status
```
*Shows which files have been modified, which are staged to be committed, and what branch you are on.*

### Add changes (Stage)
To let Git know which changes you want to include in your next commit:
```bash
git add file_name.py  # Adds a specific file
git add .             # Adds ALL modified files
```

### Save your changes (Commit)
```bash
git commit -m "Descriptive message of what you changed"
```
*The message should be short but clear, for example: "Added button to flatten slides in the UI".*

### Send your changes to GitHub (Push)
```bash
git push origin your_branch_name
```
*If you are on the main branch, it will be `git push origin main`. If it is your first time pushing a new branch, use `git push -u origin your_branch_name`*

## 3. Working with Branches
Branches allow you to make changes without affecting the main code until you are ready.

### Create and switch to a new branch
```bash
git checkout -b new_branch_name
```
*(This is the command we just used to create the current branch)*

### List all local branches
```bash
git branch
```

### Switch to an existing branch
```bash
git checkout branch_name
```

## 4. Update your code (Pull changes from others)
If you work in a team or made changes directly on the GitHub website, you need to pull them to your local computer.

### Download and merge changes from GitHub
```bash
git pull origin main
```
*If you made local changes that conflict with the remote ones, Git will ask you to resolve them.*

## 5. Save changes temporarily (Stash)
If you have half-finished changes but need to switch branches or do a quick `git pull`:
```bash
git stash          # Saves your changes temporarily and cleans the working directory
git stash pop      # Restores the changes you had saved
git stash list     # Shows all saved temporary changes
```

## 6. View change history
```bash
git log
git log --oneline  # Summarized version
```

## Typical Workflow Summary:
1. Make sure you are up to date: `git checkout main` -> `git pull`
2. Create a branch for your work: `git checkout -b my-new-feature`
3. Make your code changes.
4. See what changed: `git status`
5. Add changes: `git add .`
6. Commit changes: `git commit -m "My changes"`
7. Push to GitHub: `git push -u origin my-new-feature`
8. Go to GitHub.com and create a "Pull Request".
