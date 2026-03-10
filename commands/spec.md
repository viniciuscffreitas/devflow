# /spec

Starts the spec-driven development workflow for a feature or bugfix.

## Usage

```
/spec "task description"
```

## What it does

Invokes `devflow:spec-driven-dev` with the provided description.
Auto-detects: feature (new functionality) vs bugfix (fix for existing broken behavior).

**Feature:** Plan -> Approve -> TDD -> Verify -> Done
**Bugfix:** Behavior Contract -> Approve -> TDD -> Verify -> Done

## Examples

```
/spec "add pagination to user list endpoint"
/spec "fix: profile photo not loading on iOS"
/spec "refactor auth middleware to support OAuth"
```

## Skill invoked

`devflow:spec-driven-dev`
