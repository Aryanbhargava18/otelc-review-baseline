# Where each review rule comes from

Every rule in the draft `.github/copilot-instructions.md` and `.github/instructions/tool.instructions.md`
traces to tuning-set review comments or to repository docs and code. `M<i>` is entry `i` in
`labels.json` (maintainer comments); `C<i>` is entry `i` in `copilot_labels.json` (Copilot comments).
Only tuning data was used: maintainer comments on the 40 shared PRs and Copilot comments on the 56 PRs
Copilot commented on. No review comments on the 15 PRs in `heldout.json` were read; by construction
none of them has Copilot inline comments.

## `.github/copilot-instructions.md`

| Rule | Evidence |
|---|---|
| Behavior changes for users | #604 body truncation (C82–C91, fixed); #617 assert exits the build (M115); #759 exit code (C138) |
| Silent failures go to stderr or an error | #502 "write these warnings to stderr" (M173, M174); #617 maintainer wants the warning shown (reply to C77); #1390 load error only in debug.log (M82); #612 hard-fail (M47); #629 rule silently never matches (M50) |
| Tests that don't test the change | #629 (M53), #1362 (M78, M80), #1390 (M84), #617 (M114), #854 (M167), #1170 (M126), #470 (M5) |
| Documentation drift | #629 (M54), #612 (M48), #654 (M23–M25, M32, M33), #562 (M125), #1374 example cannot compile (M93), #617 (M113) |
| Nondeterminism | #1312 (M96), #604 (M107), #689 (M132, M138), #612 (C94, accepted) |
| Skip what CI enforces | maintainer lint comments (M89, M90, M123, M124); C137 (gofmt); `.tools/golangci.yml` (77 linters); workflows `check-consistency`, `check-typos`, `check-license-headers`, `check-conventional-commit`, `verify-bundle`, `lint-markdown`; `.github/codecov.yml` |
| No PR title/description comments | C18, C27, C43, C76 (noise) |
| No speculative hardening | #540 maintainer declined (C30, C31); #655 out of scope (C111) |
| Read the PR head first | #386 "already uses `!= nil`" (C44, C45, wrong) |
| Go version from `go.mod`; per-iteration loop vars | #561 (C46, wrong) |
| Check Go docs for platform claims | #655 `os.Rename` (C106, wrong); #759 `syscall.WaitStatus` (C141, wrong) |
| Semconv pinned, no deprecated names | #707 `rpc.system` (C130, wrong); `.semconv-version`; `docs/semantic-conventions.md` |
| Compatibility code is deliberate | #655 v0.5.0 tool path (C107–C109, wrong) |

## `.github/instructions/tool.instructions.md`

| Rule | Evidence |
|---|---|
| `packages.Load` gets the user's build flags | #1362 (M79, C170); #629 (C98); #1390 (C175); #483 `-ldflags` value (M11) |
| Reuse `-C` normalization; paths resolve against `-C` | #629 (M58, M59); `loadDirFromBuildFlags` in `tool/internal/pkgload/pkgload.go`; `go help build` (`-C`) |
| GOFLAGS: `-flag=value` only, `quoted.Split` semantics | #674 (M38, M39; C123, C124 wrong on `-toolexec <cmd>`); `tool/util/go.go` |
| `go test` flags and `--` | #562 "Missing flags from `go help testflags`" (M110) |
| Check `Package.Errors` | #1390 (C176); #612 (M47, M65); #617 (M112) |
| Apply the importcfg `importmap` | #1374 (M92) |
| Subprocess per item | #612 (M62); #629 (M57) |
| Invalid rule YAML fails at load time | #1394 (M85–M87); #629 (M50); #617 (M111, M119); #561 (C48, fixed) |
| Rule parsers agree | #1394 (M87, C172) |
| Rule not applied twice | #629 (M49) |
| Update `docs/rules.md` with rule changes | #629 (M54); #562 (M125); #1394 (M88); #617 (M113) |
| Generated identifiers valid at insertion point | #1312 (M95, M96); #729 (M156; C145) |
| Rewrite only rule-introduced code | #1312 (M94; C177–C182) |
| Cloned nodes lack positions | #1374 (M91; C184) |
| `ex` error conventions | #1211 redundant wrapping (M21); `tool/ex/error.go` package doc |
| No process exits on user input | #617 `util.Assert` exits (M115); #987 (C148); `tool/util/assert.go` |
| Golden fixtures describe what they test | #562 (C52–C54, C70–C74, fixed) |
| Fresh state per simulated run | #1362 (M78) |

## Deliberately left out of this repo

Hook and instrumentation guidance (span lifecycle across goroutines, unbounded buffers, GenAI
semconv, runtime enable/disable gate, restricted hook imports, `GetParam` on generic targets)
targets `instrumentation/`, which ADR-0007 moves to `opentelemetry-go-compile-contrib`. It is
drafted separately for that repository.
