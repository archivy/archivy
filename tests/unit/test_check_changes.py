import re

from archivy.check_changes import DATAOBJ_REGEX


def test_dataobj_regex():
    """
    Simple tests to verify the daemon that checks when an archivy file
    is edited validates the constraints
    """

    correct_filenames = ["1-04-01-20-test-1.md", "5-10-90-03-_*sdl.md", "1132141-01-04-05-sd)(.md"]
    invalid_filenames = ["-04-01-20-test1.md", "1-103-03-04-a.md", "1-10-013-04-a.md",
                         "1-10-03-044-a.md", "1-10-13-33-", "3-10-11-11.md"]

    for name in correct_filenames:
        assert re.match(DATAOBJ_REGEX, name)

    for name in invalid_filenames:
        assert not re.match(DATAOBJ_REGEX, name)
