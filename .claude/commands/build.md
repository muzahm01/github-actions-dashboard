---
description: Run TDD-first implementation for a feature within the current directory.
allowed-tools: [Bash, Edit, View]
---
# TDD Feature Implementation: $ARGUMENTS

You are working in the **current directory**. You must act as a Senior Engineer implementing the following feature: **$ARGUMENTS**.

## Phase 1: Blueprint & Success Criteria
Before writing implementation code, define:
1. **Testing Suite Architecture:** Describe the unit and integration test structure.
2. **Security Benchmarks:** Define input validation, auth checks, and data sanitization needs.
3. **Performance Benchmarks:** Define acceptable latency or resource usage for this feature.
4. **Agent Internal Notes:** [Write your initial strategy and hidden constraints here].

## Phase 2: Test-Driven Development (Red/Green)
1. **Red:** Write Unit and Integration tests first. Run them to confirm failure.
2. **Green:** Write the minimal implementation code to pass the tests.
3. **Agent Internal Notes:** [Note any edge cases or "lessons learned" during this implementation].

## Phase 3: Regression & Quality Control
1. **Full Suite:** Run ALL existing tests in the project to ensure no regressions.
2. **Refactor:** Clean up the implementation code without breaking tests.
3. **Verification:** Re-verify against the Security and Performance benchmarks from Phase 1.

## Phase 4: Atomic Commit
1. Upon successful verification, execute: `git add .` and `git commit -m "feat: implement $ARGUMENTS with full TDD coverage"`.
2. **Agent Internal Notes:** [Final summary of state to reference for the next feature].

---
### AGENT SCRATCHPAD (DO NOT OVERWRITE)
(Use this space to leave comments to yourself. Reference these notes before starting any new phase.)
