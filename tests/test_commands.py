import sys
from unittest import mock

from gutsygit.main import run
from gutsygit.client import GitResult


@mock.patch("gutsygit.main.GutsyGit.git")
def test_call(git):
    sys.argv = ["test", "cp", "message"]
    # todo proper mock
    git.return_value = GitResult(0, "stdout", "stderr")
    run()
    print(git.mock_calls)
    git.assert_any_call("add", "--all")
    git.assert_any_call("commit", m="message", with_exceptions=False, no_verify=False)
    git.assert_any_call("push", "--verbose")
