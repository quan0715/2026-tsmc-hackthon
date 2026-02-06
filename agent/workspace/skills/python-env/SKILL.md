---
name: python-env-setup
description: Use this skill to set up Python development environment, install dependencies, and configure virtual environments. Use when user requests Python environment setup, pip package installation, or encounters missing module errors.
---

# Python Environment Setup Skill

## Overview

This skill guides you on how to set up and manage a Python development environment in the workspace.

## Environment Check

### 1. Check Python Version

First, use the `bash` tool to check the installed Python version:

```
bash(command="python3 --version")
```

Expected output similar to: `Python 3.11.x`

### 2. Check pip Version

```
bash(command="pip3 --version")
```

## Installing Dependencies

### Install from requirements.txt

If the project has a `requirements.txt` file:

```
bash(command="pip3 install -r requirements.txt")
```

### Install Single Package

```
bash(command="pip3 install <package_name>")
```

Common package examples:
- `pytest` - Testing framework
- `black` - Code formatter
- `flake8` - Code linter
- `mypy` - Type checker
- `requests` - HTTP library

### Install Specific Version

```
bash(command="pip3 install package_name==1.2.3")
```

## Virtual Environment (Optional)

If an isolated environment is needed:

### Create Virtual Environment

```
bash(command="python3 -m venv .venv")
```

### Activate Virtual Environment

Specify the virtual environment's Python when running commands:

```
bash(command=".venv/bin/pip install -r requirements.txt")
```

## Running Python Code

### Run Existing File

```
bash(command="python3 main.py")
```

### Run Code Snippet

First write to a file using `write_file`, then run it:

```
write_file("./repo/check_env.py", """
import sys
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")
""")
bash(command="python3 ./repo/check_env.py")
```

### Run Tests

```
bash(command="python3 -m pytest tests/ -v")
```

## Troubleshooting

### ModuleNotFoundError

When encountering a missing module error:

1. Confirm package name (pip package name might differ from import name)
2. Use `pip3 install <package>` to install the missing package
3. Check if `requirements.txt` contains the package

### Permission Issues

If you encounter permission issues, use the `--user` flag:

```
bash(command="pip3 install --user <package_name>")
```

## Best Practices

1. **Always check requirements.txt first** - Most projects list required dependencies
2. **Use pip freeze to record dependencies** - `pip3 freeze > requirements.txt`
3. **Install dependencies before running** - Avoid ImportError
4. **Use -v parameter for verbose output** - Facilitates debugging
