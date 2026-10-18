<!-- 1190-guided-r1: Copilot CLI, model auto -> gpt-5.6-luna, 1.19 AI credits, session e565ae59-1b08-4fb9-8660-b13eb500c0a7 -->
### .github/workflows.disabled/check-consistency.yaml:76

This workflow is stored under `.github/workflows.disabled`, which GitHub does not load as a workflow. Consequently, the new naming check will never run in CI unless this file is moved to `.github/workflows/` or the active workflow is updated instead.

### tool/cmd/check-test-names/main.go:112

The existence check can treat another test file as the production source. For example, `foo_test_test.go` passes when `foo_test.go` exists, even though `foo_test.go` is itself a test file and no `foo_test_test.go` source file exists. Require the expected path to be a non-test `.go` file (and ideally a regular file) so repeated `_test` suffixes are rejected.
