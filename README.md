# Gutsy Git

Makes git usage extremely fast by making some gutsy assumptions.

### Assumptions

*   You work in a pull-request-based development environment, avoiding direct pushes to the main branch.
*   Commit messages are often squashed, so individual messages are less critical.
*   Your `.gitignore` is comprehensive, allowing you to safely add all untracked files.

## Installation

`gutsygit` is available on PyPI and can be installed with `uv` or `pip`.

To install it as a command-line tool available system-wide (recommended):
`uv tool install gutsygit`

## Usage

`gg <any number of single letter commands> [<arguments>]`

### Commands

| Command | Argument(s)     | Description                                                                                                                                                             |
| :------ | :-------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `b`     | `[<name>]`      | Create a new branch from `origin/main`. If `<name>` is not provided, 'patch' is used. Stashes and applies uncommitted changes if needed.                                |
| `s`     | `<name>`        | Switch to an existing branch.                                                                                                                                           |
| `c`     | `[<*message>]`  | Commit all changes, including untracked files. Creates a new branch if on a protected branch. If `<*message>` is omitted, a message is generated from the changes.      |
| `C`     | `[<*message>]`  | Same as `c`, but bypasses pre-commit hooks on the second try if the first one fails.                                                                                    |
| `p`     |                 | Push commits. Pulls from remote if needed and sets upstream tracking on the first push.                                                                                 |
| `P`     |                 | Same as `p`, but also opens a web browser to the pull request URL if provided by the remote (e.g., GitHub).                                                                |
| `l`     |                 | Pull changes from the remote.                                                                                                                                           |

## Examples

*   `gg cP`: Commit and push changes with a generated commit message, and open a pull request page if suggested by the remote.
*   `gg bcp newbranch some description`: Create a new branch named "newbranch", commit, and push any changes with the commit message "some description".
*   `gg Csl othertask`: Commit current changes regardless of pre-commit hooks, switch to the 'othertask' branch, and pull the latest changes.

## Settings

Settings are retrieved from `git config` with the `gutsygit.[setting]` key:

| Setting             | Default value   | Explanation                                                                                                                                  |
| :------------------ | :-------------- | :------------------------------------------------------------------------------------------------------------------------------------------- |
| `protectedbranches` | `"main,master"` | A comma-separated list of branch names to protect. This is used to prevent direct pushes and as the base for creating new branches. |
| `outputlevel`       | `"0"`           | Verbosity level (`-1`: debug, `0`: default, `1`: headers/warnings/errors only).                                                                |


