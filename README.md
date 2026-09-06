# print_msee

Print a PDF to Purdue MSEE190 from your Mac. Double-sided by default.

```sh
print_msee paper.pdf          # double-sided
print_msee paper.pdf --single # single-sided
print_msee paper.pdf --double # double-sided
```

Requires Python 3, the configured printer, and Purdue network access.
Credentials live in `~/.print_msee` (permissions `600`), never in Git.
