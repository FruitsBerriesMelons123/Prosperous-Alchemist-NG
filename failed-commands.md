# Failed commands

- `python -c "... Select-Object -First 30"` (PowerShell pipeline syntax error when chaining PowerShell operators inside/after python commands).
- `python -c "..."` containing double quotes `\"` or `<` inside PowerShell command string without escaping or using a standalone `.py` script.
- Python script initially failed with `ModuleNotFoundError: No module named 'config'`; add the repository root to `sys.path` before importing project modules from `temp` or `scratch`.
