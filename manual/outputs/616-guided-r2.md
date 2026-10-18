<!-- 616-guided-r2: Copilot CLI, model auto -> gpt-5.6-luna, 1.58 AI credits, session 7b64274f-7c5b-47e3-ac47-aaffe7f79730 -->
### tool/internal/setup/setup.go:491
The vendoring check only inspects `util.GetOtelcWorkDir()`, which is the process working directory and does not account for the effective directory selected by a `-C` build flag. For `otelc go build -C ./submodule` (or when invoked from a parent directory), this can miss `submodule/vendor/modules.txt` and leave the modified `go.mod` in vendor mode, causing the build to fail its vendor consistency check. It can also detect the wrong parent module and force `-mod=mod` for a different target.

### tool/internal/setup/setup.go:431
`findModuleRoot` cannot detect workspace vendoring. A Go workspace may have `go.work` at the workspace root and `vendor/modules.txt` there, with the build run from one of the workspace modules; this function finds that module’s `go.mod` and only checks `<module>/vendor/modules.txt`. In that valid configuration, the workaround is skipped and the build can fail after setup edits `go.mod` without updating the workspace vendor metadata.
