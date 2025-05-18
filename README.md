# GitLab CODEOWNERS

This project is a learning prototype of a GitLab CODEOWNERS parser.

It does not aim to mimic the exact GitLab behaviour. Instead it implements the
specification provided in the GitLab docs.

- https://docs.gitlab.com/user/project/codeowners/reference/
- https://docs.gitlab.com/user/project/codeowners/advanced/

In some cases, it may raise parse errors when encountering CODEOWNERS syntax
that GitLab does accept. For instance when encountering [unparsable sections].
This is a deliberate decision to avoid silently ignoring user errors.

[unparsable sections]: https://docs.gitlab.com/user/project/codeowners/advanced/#unparsable-sections

The following shows how to iterate over the owners of a target file.

```python
import codeowners

codeowners_path = "CODEOWNERS"
target_path = "cmd/main.go"

with open(codeowners_path) as f:
    s = f.read()
owners = codeowners.Owners.parse(s)

for section, users in owners.iter_owners(target_path):
    name = section._header._name
    if name == "":
        name = "unnamed"
    print("-", name, users)
```
