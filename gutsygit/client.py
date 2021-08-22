import os
import re
import webbrowser
from typing import List, Optional, Tuple, Union

import colorama
from git import Git, GitCommandError

from gutsygit.utils import removeprefix

colorama.init(autoreset=True)

LEVEL_DEBUG = -1
LEVEL_INFO = 0
LEVEL_HEADER = 1
LEVEL_WARNING = 2
LEVEL_ERROR = 3

OUTPUT_COLORS = {
    LEVEL_DEBUG: colorama.Style.DIM,
    LEVEL_INFO: "",
    LEVEL_HEADER: colorama.Fore.GREEN,
    LEVEL_WARNING: colorama.Fore.RED,
    LEVEL_ERROR: colorama.Fore.RED,
}


class Config:
    def __init__(self):  # all values are strings, since they can come from config
        self._protectedbranches = "main,master"
        self._outputlevel = f"{LEVEL_INFO}"

    def update(self, git_config: str):
        for line in git_config.split("\n"):
            try:
                line = line.strip()
                if line:
                    k, v = line.split(" ", 1)
                    setattr(self, "_" + k, str(v))
            except ValueError:
                pass

    @property
    def protected_branches(self) -> List[str]:
        return [b.strip() for b in self._protectedbranches.split(",")]

    @property
    def log_level(self) -> int:
        return int(self._outputlevel)


class GutsyGit:
    def __init__(self, path="."):
        self.git_cmd = Git()
        self.config = Config()
        try:
            self.config.update(self.git("config", "--get-regexp", "gutsygit.*", quiet=True))
        except GitCommandError as e:
            if e.stdout or e.stderr:
                self.log(f"Failed to get git config: {e}", level=LEVEL_ERROR)

    def log(self, *args, level=LEVEL_INFO):
        if any(args) and level >= self.config.log_level:
            print(f"{OUTPUT_COLORS[level]}{''.join(str(s) for s in args)}")

    def header(self, message):
        self.log(">>> ", message, level=LEVEL_HEADER)

    def git(
        self,
        command,
        *args,
        with_extended_output=False,
        with_exceptions=True,
        stdout_log_level=LEVEL_INFO,
        stderr_log_level=LEVEL_INFO,
        quiet=False,
        **kwargs,
    ) -> Union[str, Tuple[int, str, str]]:
        exitcode, stdout, stderr = getattr(self.git_cmd, command)(
            *args, **kwargs, with_extended_output=True, with_exceptions=with_exceptions
        )
        if exitcode == 0 and not quiet:
            self.log(stdout, level=stdout_log_level)
            self.log(stderr, level=stderr_log_level)
        elif not quiet:
            self.log(stdout, level=LEVEL_ERROR)
            self.log(stderr, level=LEVEL_ERROR)
        if with_extended_output:
            return exitcode, stdout, stderr
        else:
            return stdout + stderr

    # branch functions

    def current_branch(self, remote=False) -> Optional[str]:
        current = self.git("branch", show_current=True, quiet=True)
        if remote:
            try:
                remote_head = self.git("config", f"branch.{current}.merge", quiet=True).strip()
            except GitCommandError:  # exit code 1
                return None
            return removeprefix(remote_head, "refs/heads/")
        else:
            return current

    def all_branches(self, remote=False) -> List[str]:
        return [b.strip(" *") for b in self.git("branch", remotes=remote, quiet=True).split("\n")]

    def main_branch_names(self, remote=False) -> List[str]:
        remote_branches = set(self.all_branches(remote=remote))
        found_branches = [b for b in self.config.protected_branches if b in remote_branches]
        assert len(found_branches) > 0
        return found_branches

    def on_protected_branch(self, remote=False) -> bool:
        return self.current_branch(remote=remote) in self.config.protected_branches

    def create_branch(self, name):
        if name is None:
            name = self.create_name_from_diff(for_branch=True)
        return self.git("checkout", b=name, quiet=True)

    def is_dirty(self) -> bool:
        return self.git("status", porcelain=True, quiet=True, with_extended_output=True)[1].strip() != ""

    def ensure_branch(self):
        if self.on_protected_branch():
            self.header("Creating a new branch to avoid pushing to a protected branch")
            self.create_branch(name=None)

    def pull(self):
        return self.git("pull")

    # file adding
    def add_files(self, include_new_files):
        return self.git("add", "--all" if include_new_files else "")

    # diff functions
    def diff_stats(self):
        def parse_line(line):
            add, rem, *file = map(str.strip, line.split())
            return [
                int(add) if add.isdigit() else -1,
                int(rem) if rem.isdigit() else -1,
                " ".join(file),
            ]

        return sorted(
            [
                parse_line(line)
                for line in self.git("diff", "HEAD", numstat=True, quiet=True).strip().split("\n")
                if line
            ],
            key=lambda info: -(info[0] + info[1]),
        )

    def create_name_from_diff(self, for_branch=False):
        def single_desc(diffstat):
            add, rem, file = diffstat
            if not add and not rem and " => " in file:
                return f"rename {file}"
            elif not add and not os.path.isfile(file):
                return f"remove {file}"
            else:
                return f"edit {file}"

        diff = self.diff_stats()
        if not diff:
            name = "patch"
        else:
            if for_branch or len(diff) == 1:
                name = single_desc(diff[0])
            else:
                name = f"{single_desc(diff[0])}, {single_desc(diff[1])}"
                if len(diff) > 2:
                    name += f" and {len(diff) - 2} other changes"
        if for_branch:
            base_name = name.replace(" ", "-")
            branches = set(self.all_branches() + self.all_branches(remote=True))
            ix = 1
            while f"{base_name}-{ix}" in branches:
                ix += 1
            name = f"{base_name}-{ix}"
        return name

    # helpers for complex commands

    def add_and_commit(self, message, include_new_files=True, force=False):

        if self.is_dirty():
            self.ensure_branch()
            for retry in range(2):  # try twice to automatically deal with pre-commit hooks etc
                if retry == 0:
                    self.header(f"Adding all files and committing with message '{message}'")
                else:
                    self.header("Retrying commit" + (" without pre-commit hooks" if force else ""))

                self.add_files(include_new_files=include_new_files)
                if retry == 1 and not self.is_dirty():
                    self.log("Nothing to commit on retry.")
                    return
                code, out, err = self.git(
                    "commit",
                    m=message,
                    with_extended_output=True,
                    with_exceptions=(retry == 1),
                    no_verify=(retry == 1 and force),
                )
                if code == 0:
                    break
        else:
            self.log("Nothing to commit.")

    def ensure_push(self, try_pull=True, open_browser=False):
        current = self.current_branch()
        remote = self.current_branch(remote=True)
        try:
            args = ["--verbose"]
            if remote is None:
                args += ["--set-upstream", "origin", current]
            self.header(
                f"Pushing local branch '{current}' to remote branch '{remote or current}'",
            )
            status, out, err = self.git("push", *args, with_extended_output=True)
            url = re.search(r"https?://\S+", out + err)
            if status == 0 and open_browser and url:
                self.header(f"Opening {url[0]} in web browser")
                webbrowser.open(url[0])

        except GitCommandError as e:
            if try_pull and ("(fetch first)" in str(e) or "git pull" in str(e)):
                self.log(f">>> Push failed due to changes in remote, trying to pull", level=LEVEL_HEADER)
                self.pull()
                self.ensure_push(try_pull=False, open_browser=open_browser)
            else:
                raise

    def create_new_branch(self, branch_name, maybe_stash=True):
        curr_on_main = self.on_protected_branch()
        if maybe_stash and self.is_dirty() and not curr_on_main:
            self.git("stash", "push")
            try:
                return self.create_new_branch(branch_name=branch_name, maybe_stash=False)
            finally:
                self.git("stash", "pop")

        all_branches = self.all_branches()
        if branch_name:
            if branch_name in all_branches:
                i = 1
                while f"{branch_name}-{i}" in all_branches:
                    i += 1
                branch_name = f"{branch_name}-{i}"
        else:
            branch_name = self.create_name_from_diff(for_branch=True)

        main = self.main_branch_names()[0]
        self.header(f"Creating new branch {branch_name} from {main}")
        # avoids having to deal with a potentially dirty local main branch
        self.git("fetch", "origin", f"{main}:{branch_name}", quiet=True)
        self.git("checkout", branch_name)

    def switch_branch(self, branch_name):
        all_branches = self.all_branches()
        if branch_name not in all_branches:
            self.log("Branch name not found, fetching and trying again", level=LEVEL_WARNING)
            self.git("fetch")
            if self.all_branches():
                self.log("Branch name not found", level=LEVEL_ERROR)
                return

        self.header(f"Switching to branch {branch_name}")
        self.git("checkout", branch_name)
