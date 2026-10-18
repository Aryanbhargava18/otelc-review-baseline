<!-- 1190-baseline-r1: Copilot CLI, model auto -> gpt-5.6-luna, 0.88 AI credits, session 85370441-fbb8-45f8-8ac3-80c22a27e912 -->
### .github/workflows.disabled/check-consistency.yaml:76
The new check is only added to a workflow under `.github/workflows.disabled/`, so GitHub Actions will not execute it. There is no active `.github/workflows/check-consistency.yaml` containing this job, meaning the test-file naming rule is not enforced in CI.
