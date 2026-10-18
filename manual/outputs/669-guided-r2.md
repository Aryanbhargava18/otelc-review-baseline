<!-- 669-guided-r2: Copilot CLI, model auto -> gpt-5.6-luna, 1.83 AI credits, session ac3588cf-8b26-4993-96de-85d8d87d333f -->
### Makefile:649

`make clean` now deletes every `test/apps/**/otel.instrumentation.go`. This also matches the tracked `test/apps/gincustom/otel.instrumentation.go` source file, so running the standard cleanup target removes a repository file and can break subsequent `gincustom` builds. Limit this cleanup to generated files or exclude the tracked `gincustom` file.
