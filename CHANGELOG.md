# Changelog

## Bugfixes (2025-05-10)

### Core Functionality
- **Fixed anchored gitignore patterns on Windows**: Root-anchored patterns in .gitignore files (e.g., `/file.txt`) now correctly ignore files at the root directory on all platforms, including Windows.
- **Fixed YAML writer problems with special filenames**: Filenames that would be interpreted as special YAML values (like `true`, `false`, numbers, or names with special characters) are now properly escaped and quoted in the output YAML.
- **Fixed gitignore negation logic**: Implemented proper hierarchical application of gitignore rules that better matches Git's behavior with respect to parent/child directory pattern interactions.
- **Improved default ignore patterns**: Added common Python-specific patterns (`.pyc`, `__pycache__`, etc.) to default ignores and fixed directory traversal to avoid scanning ignored directories.

### Environment and Configuration
- **Fixed incorrect Black version in setup.cfg**: Changed the Black version from `black>=25.1.0` (which doesn't exist) to `black>=23.0.0`, ensuring that `pip install .[dev]` works correctly.

### CI/CD Improvements
- **Improved version bumping in CD workflow**: Replaced brittle sed command with more robust Python script to ensure reliable version updates regardless of formatting changes.
- **Fixed ambiguous git push in CD workflow**: Changed the git push command to explicitly use the current branch name instead of HEAD, preventing version bumps from happening on arbitrary branches.

### Reliability Improvements
- **Enhanced file permission handling**: Improved handling of permission-related errors for unreadable files and directories.
- **Added WSL compatibility**: Added special handling for permission-related tests in Windows Subsystem for Linux (WSL) environments.
- **Reduced verbosity**: Changed default verbosity level from INFO to ERROR to minimize console output unless errors occur.
