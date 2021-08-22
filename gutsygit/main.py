import sys

from gutsygit.client import LEVEL_ERROR, GitCommandError, GutsyGit
from gutsygit.utils import removeprefix


def run():
    if len(sys.argv) == 1:
        print("Usage: gg <any number of single letter commands>")
        print(
            "b [<name>]: create a new branch from origin/main with generated or given name, stashing current changes if needed"
        )
        print("c [<*message>]: add all changes and commit them with a generated or given commit message")
        print("l: pull")
        print(
            "p: push commits, potentially pulling and setting upstream if needed. Opens a webbrowser if an url is returned by git."
        )
        exit(0)

    gg = GutsyGit()
    if sys.argv[1] == "wp":
        exit("Thanks for the game. Well played.")
    commands = list(sys.argv[1])
    args = sys.argv[2:]

    while commands:
        cmd = commands.pop(0)
        try:
            if cmd == "b":
                gg.create_new_branch(branch_name=args.pop(0) if args else None)
            elif cmd == "s":
                if not args:
                    gg.log("s(witch) command expects a branch name, but no arguments left")
                    return
                gg.switch_branch(branch_name=args.pop(0))
            elif cmd in ["c", "C"]:
                if args and "b" not in commands and "s" not in commands:
                    message = " ".join(args)
                else:
                    message = gg.create_name_from_diff()
                gg.add_and_commit(message=message, force=(cmd == "C"))
            elif cmd == "l":
                gg.pull()
            elif cmd in ["p", "P"]:
                gg.ensure_push(try_pull=True, open_browser=(cmd == "P"))
            else:
                exit(f"Unrecognized command '{cmd}'")
        except GitCommandError as e:
            gg.log(
                f"!!! Fatal git error while executing '{cmd}':\n",
                removeprefix(e.stdout.strip(), "stdout: ").strip("'"),  # refactor exc
                removeprefix(e.stderr.strip(), "stderr: ").strip("'"),
                level=LEVEL_ERROR,
            )
            break


if __name__ == "__main__":
    run()
