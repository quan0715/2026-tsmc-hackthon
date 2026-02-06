This file is maintained by the Agent during execution to preserve key context across iterations.
Role definition, workflow, tool instructions, etc. are handled by system prompts and are not repeated here.

## Project Context
- Source Language:
- Target Language:
- Test Command:
- Run Command:
- Special Notes:


## Working Directory (Strict Compliance)

```
/(Current Directory)/
├── repo/           # Source code (Read-only)
├── refactor-repo/  # Refactored code (Your workspace)
├── memory/         # Memory system files
│   ├── AGENTS.md      # Your role definition (Read-only reference)
│   ├── plan.md        # Detailed refactor plan (Must update every iteration)
│   └── learnings.md   # Error pattern knowledge base (Optional)
│   └── status.json    # Stores iteration and phase status
└── artifacts/      # Final outputs
```

## Memory Files

### 1. CHECKLIST.md (Rapid Dashboard)

Location: `./memory/CHECKLIST.md`


Format:
```markdown
# Refactoring Checklist

## Goal
[One sentence describing the refactoring goal]

## Environment
- Source Language: xxx
- Target Language: xxx
- Test Command: `xxx`
- Run Command: `xxx`

## Progress
- [x] Environment setup complete
- [x] Completed items
- [ ] Items to be completed

## Current Iteration
Completed: xxx
Issues: xxx (if any)
Next Steps: xxx
```

**NOT Required:**
- Time estimates
- Detailed schedule
- Architectural design documents
- Multiple analysis reports
- Documents other than the 3 mentioned above

## Tools

### bash
```
bash(command="go test ./...")
bash(command="cd ./refactor-repo && go run main.go")
```

### env-setup subagent
```
task(name="env-setup", task="Set up Go environment")
```

## Workflow

1. Read `./repo/` to understand the project
2. Set up environment (use env-setup)
3. Write code to `./refactor-repo/`
4. Run tests, fix bugs
5. Update CHECKLIST.md
6. Repeat until completed
