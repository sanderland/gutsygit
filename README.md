# Gutsy Git

Makes git usage extremely fast by making some gutsy assumptions.

### Assumptions:

You work in a development environment based on pull request, avoiding pushing to your main branch. 
Commit messages are not always very relevant due to squashing. Your .gitignore is set up well enough to routinely add all changes.

## Installation

`pip install gutsygit`

## Usage

`gg <any number of single letter commands> [<arguments>]`

### Commands:

* `b [<name>]`: Create a new branch from origin/main with generated or given name, stashing and applying uncommitted changes if needed. 
   * If the branch exists, adds a numeric suffix to the name.
* `s <name>`: Switch to existing branch.  
* `c [<*message>]`: Commit changes. 
   * Ensures you are not on your protected branches by creating a branch if needed.
   * Add all changes, including untracked files, and commit them with a generated or given commit message. 
   * If a `b` or `s` command remains after, argument(s) are assumed to be for the branch name, and the message is always generated.
   * Retries once on failure to automatically commit changes resulting from pre-commit hooks.
* `C [<*message>]`: Same as `c`, but bypasses pre-commit hooks on the second try using `--no-verify`.
* `p`: Push commits.
   * Potentially pulls from remote if needed.
   * Sets tracking for the remote branch with the same name on the first push. 
* `P`: same as `p`, but opens a web browser if an url is returned by git, as GitHub does for pull requests.
* `l`: Pull

## Examples

* `gg cP`: Commit and push changes with a generated commit message, and open a pull request page if suggested by the remote.
* `gg bcp newbranch some description`: Create a new branch named "newbranch", commit, and push any changes that were not committed before this with the commit message "some description".
* `gg Csl othertask`: Commit current changes regardless of commit hooks status, switch to 'othertask' branch and updates it.

## Settings
Settings are retrieved from `git config` with the `gutsygit.[setting]` key:


| Setting | Default value | Explanation |
|---------|---------|-------------|
|  protectedbranches | "main,master" | comma-separated list of branch names to avoid pushing to. Also used to branch from for a new clean branch, taking the first entry found that exists in the remote. |
|  outputlevel | "0" | verbosity level (-1: debug, 1: headers/warnings/errors only) |


