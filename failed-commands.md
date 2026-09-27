# Failed commands

- `python -c "... Select-Object -First 30"` (PowerShell pipeline syntax error when chaining PowerShell operators inside/after python commands).
- `python -c "..."` containing double quotes `\"` or `<` inside PowerShell command string without escaping or using a standalone `.py` script.
- Python script initially failed with `ModuleNotFoundError: No module named 'config'`; add the repository root to `sys.path` before importing project modules from `temp` or `scratch`.
- `sed -i` in Git Bash rewrites CRLF files with LF line endings (whole-file diffs). Edit CRLF files with the Edit tool or Python using `newline=''`.
- `sed -i` with regex escapes such as `\s`/`\d` inside single-quoted bash strings silently failed to match; use the Edit tool for regex-bearing source edits.
- Python heredocs (`python - <<'EOF'`) that embed source text containing backslash escapes produced mismatched search strings; write the helper to a `.py` file instead.
- Counting CRLF lines with `grep -c` in Git Bash is unreliable; check line endings with Python by counting CRLF byte pairs in the file.
- Importing a scratch module that runs work at import time (no `if __name__ == "__main__":` guard) executed it with the wrong `sys.argv`; guard scratch helpers.
- Importing the project config on a non-Windows host fails with `IndexError` (`Path(...).parents[2]` on Windows-style paths). Run the tools on Windows, or in a scratch copy only, alias `PureWindowsPath` as `Path`.
- Writing a file back to the computer from a staged output that reuses an earlier output's filename can write the earlier content. Give each revision a new staged filename and confirm the result by hash.
- `strings` is not installed in Git Bash; inspect binary files (e.g. compiled `.pex`) by reading bytes in Python.
- Piping `ls -l` through `cut -c30-` truncated the size column and looked like a corrupt 2 KB DLL; use `awk '{print $5, $7}'` for size/time.
