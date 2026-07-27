# Implementation Plan — Refined Self-Healing CI Pipeline

We will refine the infinite loop guardrail in `ci-auto-fix-v3.py` to make the git-push-based self-healing pipeline extremely safe, while explaining the file-sharing limitations of separate GitHub Actions jobs.

## Technical Context: Separate Job Limitations in GitHub Actions
GitHub Actions runs each job on an isolated virtual machine. If `auto-fix` runs in a separate job and commits code locally, the subsequent `retry-test` job will not see those changes because it checks out code from the remote repository. Pushing the fixed code to the remote repository is the standard way to trigger a fresh test run.

## Proposed Changes

### CI/CD Scripts

#### [MODIFY] [.github/scripts/ci-auto-fix-v3.py](file:///.github/scripts/ci-auto-fix-v3.py)
- Refine the `check_infinite_loop()` function to check the Git log for consecutive AI Auto-Fix commits and abort if 2 consecutive fixes have failed, ensuring no infinite loop occurs.
- Ensure the commit message format is standardized so that the regex check is always accurate.

## Verification Plan

- Verify `check_infinite_loop()` logic by running it locally.
