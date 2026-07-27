# GitHub Actions Error Checker Scratchpad

## Plan
1. Get the DOM and screenshot of the GitHub Action run page.
2. Identify the status of the run (succeeded, failed, in progress).
3. If there are failed jobs, click on them to view the details.
4. For each failed job:
   - Identify which step failed.
   - Inspect the logs for that step.
   - Extract the error messages.
5. Report all found errors back to the user.

## Current State
- Page ID: `4977D952D30FC46FBBB8ECAE569FA1CE`
- URL: `https://github.com/paykaribazaronline/supremeai/actions/runs/30238794037/job/89891703410`

## Progress
- [ ] Inspect the main page of the run
- [ ] Find failed steps
- [ ] Extract errors
- [ ] Summarize and report
