class ParseError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Owners:
    """An entire CODEOWNERS file."""

    def __init__(self):
        self._keys = dict()
        self._sections = list()
        self.add_section(Section(Header("", False, 0, [])))

    def add_section(self, section):
        key = section._header._name.lower()
        assert key not in self._keys
        self._keys[key] = len(self._sections)
        self._sections.append(section)

    def has_section(self, name):
        return name.lower() in self._keys

    def section(self, name):
        assert self.has_section(name)
        index = self._keys[name.lower()]
        return self._sections[index]

    def __str__(self):
        sections = [str(s) for s in self._sections]
        sections = [s for s in sections if s != ""]
        return "\n\n".join(sections)

    @staticmethod
    def parse(s):
        """Parses the contents of a CODEOWNERS file."""
        lines = s.splitlines()
        owners = Owners()
        section_name = ""
        for i, line in enumerate(lines):
            try:
                # Empty line or comment
                if line == "" or line[0] == "#":
                    continue
                # Section header
                elif line[0] == "[" or line[:2] == "^[":
                    header = Header.parse(line)
                    section_name = header._name
                    if owners.has_section(section_name):
                        if header != owners.section(section_name)._header:
                            raise ParseError("mismatched repeated section")
                    else:
                        owners.add_section(Section(header))
                # Section entry
                else:
                    entry = Entry.parse(line)
                    owners.section(section_name).add_entry(entry)
            except ParseError as e:
                raise ParseError("line %d: %s" % (i + 1, str(e)))
        return owners


class Section:
    """A section in a CODEOWNERS file, including the unnamed section."""

    def __init__(self, header):
        self._header = header
        self._entries = list()

    def add_entry(self, entry):
        self._entries.append(entry)

    def __str__(self):
        header = str(self._header)
        lines = [header] if header != "" else []
        lines += [str(e) for e in self._entries]
        return "\n".join(lines)


class Header:
    """The header of a section."""

    def __init__(self, name, optional, count, owners):
        self._name = name
        self._optional = optional
        self._count = count
        self._owners = owners

    def __eq__(self, other):
        return (
            self._name.lower() == other._name.lower()
            and self._optional == other._optional
            and self._count == other._count
            and set(self._owners) == set(other._owners)
        )

    def __str__(self):
        if self._name == "":
            return ""
        optional = "^" if self._optional else ""
        name = "[%s]" % self._name
        count = "[%d]" % self._count if self._count != 0 else ""
        owners = " " + " ".join(self._owners) if len(self._owners) > 0 else ""
        return optional + name + count + owners

    @staticmethod
    def parse(line):
        """Parses a header line."""
        i = 0
        # Optional
        optional = False
        if line[i] == "^":
            optional = True
            i += 1
        # Name
        name, i = _read_brackets(line, i)
        if name is None:
            raise ParseError("could not find section name")
        if name == "":
            raise ParseError("section name cannot be empty")
        # Count
        count = 0
        if i < len(line):
            s, i = _read_brackets(line, i)
            if s is not None:
                try:
                    count = int(s)
                    if count < 1:
                        raise ParseError("section count must be at least 1")
                except ValueError:
                    raise ParseError("section count must be an integer")
        # Owners
        owners = list()
        if i < len(line):
            owners = _read_owners(line, i)
        return Header(name, optional, count, owners)


class Entry:
    """An entry in a section."""

    def __init__(self, pattern, excluded, owners):
        self._pattern = pattern
        self._excluded = excluded
        self._owners = owners

    def __eq__(self, other):
        return (
            self._pattern == other._pattern
            and self._excluded == other._excluded
            and set(self._owners) == set(other._owners)
        )

    def __str__(self):
        excluded = "!" if self._excluded else ""
        pattern = self._pattern.replace(" ", "\\ ")
        owners = " " + " ".join(self._owners) if len(self._owners) > 0 else ""
        return excluded + pattern + owners

    @staticmethod
    def parse(line):
        """Parses an entry line."""
        i = 0
        # Excluded
        excluded = False
        if line[i] == "!":
            excluded = True
            i += 1
        # Pattern
        pattern, i = _read_pattern(line, i)
        if pattern == "":
            raise ParseError("pattern cannot be empty")
        # Owners
        owners = list()
        if i < len(line):
            owners = _read_owners(line, i)
        return Entry(pattern, excluded, owners)


def _read_pattern(line, i=0):
    """Returns the contents of the line from the specified index
    until the first space character. Also returns the index of
    the next character. Spaces may be escaped with a backslash.
    """
    result = list()
    escaped = False
    while i < len(line):
        if escaped:
            escaped = False
            if line[i] != " ":
                raise ParseError("only space may be escaped")
            result.append(line[i])
        else:
            if line[i] == "\\":
                escaped = True
            else:
                if line[i] == " ":
                    break
                result.append(line[i])
        i += 1
    if escaped:
        raise ParseError("unclosed escape sequence")
    result = "".join(result)
    return result, i


def _read_brackets(line, i=0):
    """Returns the contents enclosed into the square brackets starting
    at the specificed index. Returns None if no square brackets start at
    that index. Also returns the index of the next character.
    """
    if line[i] != "[":
        return None, i
    try:
        j = line.index("]", i + 1)
    except ValueError:
        raise ParseError("unclosed square brackets")
    result = line[i + 1 : j]
    return result, j + 1


def _read_owners(line, i=0):
    """Returns the list of owners starting at the specified index
    and finishing at the end of the line. Multiple spaces before and
    between owners are tolerated for indentation.
    """
    if line[i] != " ":
        raise ParseError("no space before first owner")
    if line[-1] == " ":
        raise ParseError("unexpected space after last owner")
    owners = list()
    owner = list()
    while i < len(line):
        if line[i] == " ":
            if len(owner) > 0:
                owners.append("".join(owner))
                owner = list()
        else:
            owner.append(line[i])
        i += 1
    if len(owner) > 0:
        owners.append("".join(owner))
    return owners
