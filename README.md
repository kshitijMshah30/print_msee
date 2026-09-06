# print_msee

Print one copy of a PDF to the macOS `Purdue_MSEE190` queue. Double-sided,
long-edge binding is the default.

```sh
print_msee /path/to/paper.pdf
print_msee /path/to/paper.pdf --single
print_msee /path/to/paper.pdf --double
```

Requires macOS, Python 3, a configured Purdue MSEE190 printer using the
PostScript queue, and access to Purdue's print server (campus network or VPN).
The queue must use `auth-info-required=username,password`.

Store credentials in `~/.print_msee` as JSON with `username` and `password`
string fields. Set its permissions to `600`. This file stays outside the
repository and must never be committed. Credentials are sent only to the local
macOS print service for printer authentication; they are not placed in process
arguments or printer URLs.

Install the executable into a directory on your PATH, such as `~/.local/bin`.
The script requests Letter paper, one copy, and the chosen duplex mode for each
job without changing other printers' defaults.

Exit codes: 0 means macOS reports completion, 1 means failure, 2 means the job
is still pending after two minutes. Completion indicates the print service
finished the job, not physical verification of the paper. Check Print Center
before retrying to avoid duplicates. Authentication is attempted once per job.
