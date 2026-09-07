# print_msee

Print a PDF to Purdue MSEE190 from your Mac. Double-sided by default.

```sh
print_msee paper.pdf          # double-sided
print_msee paper.pdf --single # single-sided
print_msee paper.pdf --double # double-sided
```

## Printer setup

Before submitting a PDF, the script checks that the Purdue_MSEE190 printer
has the correct server address and an installed PPD driver. If missing or
incomplete, it configures the printer using macOS's built-in **Generic
PostScript** driver, enables duplex printing, and sets up username/password
authentication. No third-party driver download is needed on a standard macOS
installation. An administrator permission dialog appears if macOS requires it.

You can also check and configure the printer without sending a document:

```sh
print_msee --setup
# From a cloned repository:
python3 print_msee --setup
```

If setup fails or permission is declined, no document is submitted. If the
built-in driver or SMB printing component is missing from macOS itself, the
script stops with a repair/update message rather than downloading an unverified
driver. It does not change your default printer or other printer queues.

Requires macOS, Python 3.8 or later, and Purdue network/VPN access for printing.
Credentials live in `~/.print_msee` (permissions `600`), never in Git. The
`--setup` check does not require these credentials; printing does.

## Tests

```sh
python3 -m unittest discover -v
```

Tests mock printer operations and do not print documents. Installation paths
are tested offline; `--setup` can verify the actual local printer configuration.
