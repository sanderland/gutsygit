import os
import sys
from unittest import mock

from gutsygit.main import run


@mock.patch("gutsygit.main.GutsyGit.git")
def test_call(git):
    sys.argv = ["test", "cp", "message"]
    # todo proper mock
    git.side_effect = (
        lambda *args, **kwargs: (0, "stdout", "stderr") if kwargs.get("with_extended_output") else "stdout"
    )
    run()
    print(git.mock_calls)
    git.assert_any_call("add", "--all")
    git.assert_any_call("commit", m="message", with_extended_output=True, with_exceptions=False, no_verify=False)
    git.assert_any_call("push", "--verbose", with_extended_output=True)
