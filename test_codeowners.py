import codeowners
import unittest


class TestNew(unittest.TestCase):

    def test_read_pattern(self):
        happy = [
            ("*.txt", 0, "*.txt", 5),
            ("!*.txt", 1, "*.txt", 6),
            ("/README.md @doc", 0, "/README.md", 10),
            ("/Cool\\ File.jpg @dev", 0, "/Cool File.jpg", 15),
        ]
        for s, i, expected_s, expected_i in happy:
            actual_s, actual_i = codeowners._read_pattern(s, i)
            self.assertEqual(expected_s, actual_s)
            self.assertEqual(expected_i, actual_i)
        sad = [
            ("*.txt\\", 0, "unclosed escape sequence"),
            ("*\\.jpg", 0, "only space may be escaped"),
        ]
        for s, i, expected_error in sad:
            try:
                codeowners._read_pattern(s, i)
                self.fail("expected ParseError %s" % expected_error)
            except codeowners.ParseError as e_actual:
                self.assertEqual(expected_error, str(e_actual))

    def test_read_brackets(self):
        happy = [
            ("*.txt", 0, None, 0),
            ("[Dev]", 0, "Dev", 5),
            ("[Dev] @dev", 0, "Dev", 5),
            ("[Dev][2]", 0, "Dev", 5),
            ("[Dev][2]", 5, "2", 8),
            ("[Dev][2] @dev", 5, "2", 8),
            ("[Dev] @dev", 5, None, 5),
        ]
        for s, i, expected_s, expected_i in happy:
            actual_s, actual_i = codeowners._read_brackets(s, i)
            self.assertEqual(expected_s, actual_s)
            self.assertEqual(expected_i, actual_i)
        sad = [
            ("[Dev", 0, "unclosed square brackets"),
        ]
        for s, i, expected_error in sad:
            try:
                codeowners._read_brackets(s, i)
                self.fail("expected ParseError %s" % expected_error)
            except codeowners.ParseError as e_actual:
                self.assertEqual(expected_error, str(e_actual))

    def test_read_owners(self):
        happy = [
            ("[Dev] @dev", 5, ["@dev"]),
            ("/README.md @doc @dev", 10, ["@doc", "@dev"]),
            ("*.txt      @doc", 5, ["@doc"]),
        ]
        for s, i, expected_owners in happy:
            actual_owners = codeowners._read_owners(s, i)
            self.assertEqual(expected_owners, actual_owners)
        sad = [
            ("[Dev]@dev", 5, "no space before first owner"),
            ("[Dev] @dev ", 5, "unexpected space after last owner"),
        ]
        for s, i, expected_error in sad:
            try:
                codeowners._read_owners(s, i)
                self.fail("expected ParseError %s" % expected_error)
            except codeowners.ParseError as e_actual:
                self.assertEqual(expected_error, str(e_actual))

    def test_parse_entry(self):
        happy = [
            ("*.txt", codeowners.Entry("*.txt", False, [])),
            ("!*.txt", codeowners.Entry("*.txt", True, [])),
            ("*.py @dev", codeowners.Entry("*.py", False, ["@dev"])),
            ("*.py   @dev", codeowners.Entry("*.py", False, ["@dev"])),
        ]
        for line, expected_entry in happy:
            actual_entry = codeowners.Entry.parse(line)
            self.assertEqual(expected_entry, actual_entry)
        bad = [
            (" @dev @qa", "pattern cannot be empty"),
            ("*.txt @dev @qa ", "unexpected space after last owner"),
        ]
        for line, expected_error in bad:
            try:
                codeowners.Entry.parse(line)
                self.fail("expected ParseError %s" % expected_error)
            except codeowners.ParseError as actual_error:
                self.assertEqual(expected_error, str(actual_error))

    def test_parse_section_header(self):
        happy = [
            ("[Dev]", codeowners.Header("Dev", False, 0, [])),
            ("[Dev] @dev", codeowners.Header("Dev", False, 0, ["@dev"])),
            ("^[QA] @qa", codeowners.Header("QA", True, 0, ["@qa"])),
            ("[Dev][3] @dev", codeowners.Header("Dev", False, 3, ["@dev"])),
        ]
        for line, expected_header in happy:
            actual_header = codeowners.Header.parse(line)
            self.assertEqual(expected_header, actual_header)
        bad = [
            ("*.txt @dev", "could not find section name"),
            ("[] @dev", "section name cannot be empty"),
            ("^[Dev @dev", "unclosed square brackets"),
            ("[Dev]@dev", "no space before first owner"),
            ("[Dev] @dev ", "unexpected space after last owner"),
            ("[Dev][0] @dev", "section count must be at least 1"),
            ("[Dev][xyz] @dev", "section count must be an integer"),
        ]
        for line, expected_error in bad:
            try:
                codeowners.Header.parse(line)
                self.fail("expected ParseError %s" % expected_error)
            except codeowners.ParseError as actual_error:
                self.assertEqual(expected_error, str(actual_error))

    def test_match(self):
        tests = [
            ("README.md", "README.md", True),
            ("index.html", "README.md", False),
            ("README.md", "*.md", True),
            ("index.html", "*.md", False),
            ("docs/README.md", "docs", True),
            ("docs/README.md", "/docs", True),
            ("project/docs/README.md", "docs", True),
            ("project/docs/README.md", "/docs", False),
            ("docs/x/y/z/README.md", "/docs/**/README.md", True),
            ("docs/README.md", "/docs/**/README.md", True),
            ("docs/x/README.md", "/docs/*/README.md", True),
            ("docs/README.md", "/docs/*/README.md", False),
            ("docs", "/docs/README.md", False),
        ]
        for path, pattern, expected in tests:
            actual = codeowners._match(path, pattern)
            self.assertEqual(expected, actual)
