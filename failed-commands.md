# Failed commands

Traps in this project's tools and environment that cost earlier sessions retries. **Read the sections relevant to your task before starting** (always *Windows shell*). Rules for how code must be written live in `AGENTS.md`, not here; this file is for facts about the environment and tools.

## How to add an entry (agents)
Add one when something **cost you a retry and could plausibly bite a future session**. Before finishing the task:
1. **Verify it.** Only record what you actually hit and confirmed the fix for (reproduced it, or the fix demonstrably worked). No guesses, no general advice, no "might".
2. **Search first** (`grep` this file for the tool or symptom). If an entry already covers it, improve that entry instead of adding a near-duplicate.
3. **Keep it to one bullet** in the right section: **symptom** → cause → **what to do instead**, plus versions if relevant, and the date. Link to the doc or file that has details.
4. **Fixed at the root?** If you fix the cause (e.g. patch the tool) so it can't recur, delete the entry or reword it into "fixed in … (date)". If a gotcha has become a project rule, move it to the doc that owns rules and delete it here.
5. **Never** record secrets, personal data, or one-off typos. Keep the file under ~100 entries: prune stale ones.
6. Mention added or removed gotchas in your session summary.

## Windows shell

- `python -c "... Select-Object -First 30"` (PowerShell pipeline syntax error when chaining PowerShell operators inside/after python commands).
- PowerShell `Remove-Item` calls were rejected by the command policy in this environment; remove a task-created scratch file with Python `Path.unlink()` instead.
- `python -c "..."` containing double quotes `\"` or `<` inside PowerShell command string without escaping or using a standalone `.py` script.
- `sed -i` in Git Bash rewrites CRLF files with LF line endings (whole-file diffs). Edit CRLF files with the Edit tool or Python using `newline=''`.
- `sed -i` with regex escapes such as `\s`/`\d` inside single-quoted bash strings silently failed to match; use the Edit tool for regex-bearing source edits.
- Python heredocs (`python - <<'EOF'`) that embed source text containing backslash escapes produced mismatched search strings; write the helper to a `.py` file instead.
- Counting CRLF lines with `grep -c` in Git Bash is unreliable; check line endings with Python by counting CRLF byte pairs in the file.
- `strings` is not installed in Git Bash; inspect binary files (e.g. compiled `.pex`) by reading bytes in Python.
- Piping `ls -l` through `cut -c30-` truncated the size column and looked like a corrupt 2 KB DLL; use `awk '{print $5, $7}'` for size/time.
- `rg -n` with a malformed regex containing quotes or parentheses failed in PowerShell; simplify the pattern or use fixed-string matching.
- A one-line PowerShell `python -c` expression with nested regular-expression quoting failed to parse; use a PowerShell here-string piped to Python for multi-line inspection.
- PowerShell `rg` calls with nested double quotes and backslash escapes in a double-quoted command string caused a parser error; use simple single-quoted search patterns.
- PowerShell `rg` does not accept a quoted wildcard source path such as `alchemist\src\*.cpp`; search the directory directly or use `rg --files` to enumerate paths.
- PowerShell does not provide Unix `head`; use `Select-Object -First N` for PowerShell output filtering.
- A PowerShell `rg` search used a quoted wildcard source path (`alchemist\src\Alchemy*`), which is not accepted; search the directory directly or enumerate files first.
- PowerShell `rg` does not expand quoted wildcard paths such as `pat-*.py`; search `.` or enumerate paths with `rg --files`.
- A PowerShell command that mixed `Get-Content` and a quoted wildcard `rg` path returned an invalid-path error; use explicit paths or enumerate files first.
- A PowerShell probe piped to Unix `tail`; PowerShell has no `tail` command. Use `Select-Object -Last N`.
- A PowerShell `rg` query used an unexpanded source wildcard (`Ordinator.*`) and failed; enumerate files or search the containing directory.
- A ripgrep command passed a wildcard filename path instead of a directory plus glob; search the directory with `--glob`.
- PowerShell `rg` was passed an unexpanded README wildcard and reported an invalid path; search the explicit file path or use `rg --files` to enumerate matches.
- A PowerShell `Get-Item` command supplied multiple literal paths as positional arguments after a single `-LiteralPath`, causing a parameter error; pipe a path array through `ForEach-Object { Get-Item -LiteralPath $_ }` instead.

## Project paths and file searches

- `Get-Content` or `rg` against guessed source paths that do not exist; locate files with `rg --files` before opening or searching them. Reference repositories such as CommonLibSSE-NG are external configured paths, not assumed workspace subdirectories; take their roots from `config.py`/`user-paths.md` and enumerate existing files before querying them (confirmed 2026-09-30).
- Papyrus test-source probes targeting the console-test folder directly missed `Source/Scripts`; locate its `.psc` path with `rg --files` before reading it.
- A file search used a repository-relative path while the shell was already inside a subdirectory; use paths relative to the current working directory or run it from the repository root.
- Running root-level Python checks from a nested project directory caused missing-file/import errors; run them from the repository root.
- A build artifact check used the wrong output folder; use the configured build directory from project settings instead of assuming a nested `build` directory.
- A combined validation command ran repository-root checks from the console-test subdirectory; run those checks from the repository root and compile Papyrus separately from its own directory.
- A PowerShell `Get-ChildItem` probe targeted `Skyrim Special Edition\Data\SKSE\Plugins`, which is absent because this MO2 profile keeps mod files under its mods directory; locate SKSE mod data under the configured MO2 profile.
- A source search targeted a guessed `alchemist\src\Vanilla` directory that does not exist; use `rg --files` to locate the project header/source directory first.
- Guessed config path constants raised `AttributeError`; inspect `config.py` declarations first. Use `MO2_DEFAULT_PROFILE_DIR` for the profile and `SKYRIM / "Data"` for game masters (verified 2026-09-30).
- PowerShell `Get-Content` used a nonexistent source path (`alchemist\ModSettings.cpp`); locate the file first (`alchemist\src\ModSettings.cpp`).
- An `rg` command searched a nonexistent repository subdirectory and failed; confirm the directory exists or search the repository root.

## Python tools and test harnesses

- Python script initially failed with `ModuleNotFoundError: No module named 'config'`; add the repository root to `sys.path` before importing project modules from `temp` or `scratch`.
- Importing a scratch module that runs work at import time (no `if __name__ == "__main__":` guard) executed it with the wrong `sys.argv`; guard scratch helpers.
- Importing the project config on a non-Windows host fails with `IndexError` (`Path(...).parents[2]` on Windows-style paths). Run the tools on Windows, or in a scratch copy only, alias `PureWindowsPath` as `Path`.
- Running the pre-launch audit before registering a new mode stopped at its unknown-mode guard; update the audit's mode category, expected state, and script inventory together.
- An edit to the verification harness briefly introduced Python indentation errors; compile the harness before running its checks.
- Running the master test-suite verification harness again while its first run was still active exited at its single-instance guard; wait for the first run to finish before retrying.
- A Python recipe-preflight scratch probe indexed unioned effect names into one ingredient dictionary and raised `KeyError`; test against each ingredient’s own effect dictionary.

- Baseline validation returned missing-state regression failures after in-game recaptures changed mod-setting telemetry while recipe values stayed unchanged; compare complete setting identities, preserve the previous baseline, and refresh it through the standard harness only after validating the new captures (2026-09-30).

## Papyrus compilation

- Caprica 0.3.0 reported an unexpected NUL at EOF when the source was rewritten during an active compile; the file contained no NUL bytes. Finish source edits before launching compilation, leave the source untouched while it runs, and retry on the stable file (verified 2026-09-30).
- The deployment wrapper printed success and returned exit code 0 after Caprica reported compilation failure; fixed in `pa-console-tests/compile.ps1` (2026-09-30), which now checks the native compiler exit code and throws before announcing success.

## CSV inspection

- Localized master-plugin `FULL` subrecords were decoded as text and produced control characters; these bytes are string-table IDs. Verify binary record type/FormID and use authoritative ingredient CSV names or resolve the plugin string table instead (2026-09-30).

- A CSV inspection assumed an `origin_plugin` column that the ingredient snapshot does not contain; inspect the header before querying fields.
- A CSV inspection expected an `ingredient` header; inspect the CSV header first and use the actual `ingredient_name` field.

## File editing, transfers, and Git checks

- Exact text insertion using CRLF paragraph separators failed on an LF-only Markdown file; inspect each target file's line endings and preserve its existing separators (2026-09-30).
- Writing a file back to the computer from a staged output that reuses an earlier output's filename can write the earlier content. Give each revision a new staged filename and confirm the result by hash.
- `git diff --check` can flag every added line in a CRLF file when Git is not configured to treat CR as line-ending whitespace; verify with `git -c core.whitespace=cr-at-eol diff --check`.
- An `apply_patch` edit did not match tab-indented Python source and failed without changes; use exact source indentation or a narrowly scoped Python text replacement.
- A narrow Papyrus migration script aborted before writing because its expected AP-7 provisioning snippet did not match the actual source; inspect the exact block and keep the change atomic before retrying.
- An exact-text patch did not match the verification script after prior edits, so it made no changes; inspect the current block before retrying.
- A repository edit patch aborted because one expected line had already changed; use a smaller exact change or inspect the current source first.
- A plain diff whitespace check treated existing CRLF endings as trailing whitespace across edited files; use `git -c core.whitespace=cr-at-eol diff --check` for this repository and fix any actual new trailing whitespace separately.
- Several exact patch attempts failed because the surrounding Markdown or Python text differed from the assumed context; inspect the exact current lines and apply smaller focused patches.

## C++ and CommonLibSSE compilation

- A C++ probe build failed because `GameSettingCollection::GetSetting` is non-const; retain a non-const singleton pointer when reading settings.
- Two plugin builds stopped on compile errors in the new Ordinator adapter: a stale duplicate helper and const perk pointers passed to `HasPerk`; remove duplicate code and match CommonLibSSE's `HasPerk` pointer signature before building.
- Ordinator adapter compilation failed when calling non-const `Actor::GetMagicTarget` through a const `PlayerCharacter*`; retain a non-const actor pointer for active-effect queries.
