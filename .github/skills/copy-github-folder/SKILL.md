# copy-github-folder

Portable PowerShell script for copying `.github/` folder from any source to the local directory. Use this skill when user wants to copy GitHub configuration files, hooks, scripts, or agents from a template/remote location to local workspace.

## When to Use

- User says "copy .github/" or "sync .github folder"
- User wants to use a template's GitHub config
- User asks to copy hooks, agents, or scripts from another project
- User wants to bootstrap .github/ from a source path

## How It Works

The script `Copy-GitHubFolder.ps1` is portable and can be run from anywhere. It copies the entire `.github/` folder contents from a source path to the current directory's `.github/` folder.

## Usage

### Basic Copy
```powershell
# Run from the target directory where you want .github/ to appear
.\Copy-GitHubFolder.ps1 -SourcePath D:\projects\tools\hook\.github
```

### From Relative Path
```powershell
# From a sibling directory
.\Copy-GitHubFolder.ps1 -SourcePath ..\template\.github
```

### Force Overwrite
```powershell
# Replace existing .github/ entirely
.\Copy-GitHubFolder.ps1 -SourcePath D:\path\to\source\.github -Force
```

### Interactive Mode
```powershell
# Just run without args to see usage
.\Copy-GitHubFolder.ps1
```

## Examples in Context

- "Copy hooks from my template" → Use script with template path
- "Sync .github from parent repo" → Use relative path
- "Reset .github to default" → Use -Force with clean source

## Script Location

The script is at the workspace root: `Copy-GitHubFolder.ps1`. It's portable and can be copied to any directory or added to PATH for global use.

## Key Features

- Accepts absolute or relative paths
- Interactive help with no args
- -Force flag to overwrite existing
- Shows copied contents after success
- Works from any PowerShell session

---
## Memory-Bank Reference
See .github/MEMORY-BANK-PATCH.md for repository memory-bank lifecycle and rules.

