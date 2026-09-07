"""Offline tests: no documents are sent to a printer."""
import contextlib
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

loader = importlib.machinery.SourceFileLoader("print_msee", str(Path(__file__).with_name("print_msee")))
spec = importlib.util.spec_from_loader(loader.name, loader)
app = importlib.util.module_from_spec(spec)
loader.exec_module(app)


class Tests(unittest.TestCase):
    def test_duplex_options(self):
        for single, duplex, sides in [(False, b"DuplexNoTumble", b"two-sided-long-edge"),
                                      (True, b"None", b"one-sided")]:
            class Library:
                def __init__(self): self.options = {}
                def cupsAddOption(self, key, value, count, options):
                    self.options[key] = value
                    return count + 1
                def cupsPrintFile(self, *args): return 42
                def cupsFreeOptions(self, *args): pass
            cups = object.__new__(app.Cups)
            cups.lib = Library()
            self.assertEqual(cups.submit(Path("paper.pdf"), single), 42)
            self.assertEqual(cups.lib.options[b"Duplex"], duplex)
            self.assertEqual(cups.lib.options[b"sides"], sides)
            self.assertEqual(cups.lib.options[b"Option1"], b"True")

    def test_modes_and_authentication(self):
        for flag, single in [([], False), (["--double"], False), (["--single"], True)]:
            with tempfile.TemporaryDirectory() as directory:
                pdf = Path(directory) / "paper.pdf"
                pdf.write_bytes(b"%PDF-1.4\n")
                with patch.object(app, "credentials", return_value={"username": "test", "password": "test"}), \
                     patch.object(app, "ensure_printer"), patch.object(app, "Cups") as factory, patch.object(app.time, "sleep"), \
                     patch.object(app.sys, "argv", ["print_msee", str(pdf)] + flag), \
                     contextlib.redirect_stdout(io.StringIO()):
                    cups = factory.return_value
                    cups.submit.return_value = 42
                    cups.status.side_effect = [(4, True), (9, False)]
                    self.assertEqual(app.main(), 0)
                    cups.submit.assert_called_once_with(pdf.resolve(), single)
                    cups.authenticate.assert_called_once()

    def test_credentials_permissions_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(app.Path, "home", return_value=Path(directory)):
            path = Path(directory) / ".print_msee"
            path.write_text('{"username":"test","password":"test"}')
            path.chmod(0o600)
            self.assertEqual(app.credentials()["username"], "test")
            path.chmod(0o644)
            with self.assertRaises(ValueError): app.credentials()
            path.rename(path.with_suffix(".other"))
            path.symlink_to(path.with_suffix(".other"))
            with self.assertRaises(OSError): app.credentials()

    def test_failed_auth_does_not_resubmit(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "paper.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            with patch.object(app, "credentials", return_value={"username":"test", "password":"test"}), \
                 patch.object(app, "ensure_printer"), patch.object(app, "Cups") as factory, patch.object(app.time, "sleep"), \
                 patch.object(app.sys, "argv", ["print_msee", str(pdf)]), \
                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                cups = factory.return_value
                cups.submit.return_value = 42
                cups.status.return_value = (4, True)
                self.assertEqual(app.main(), 1)
                cups.submit.assert_called_once()
                cups.authenticate.assert_called_once()


class SetupTests(unittest.TestCase):
    def test_existing_printer_requires_no_install(self):
        with patch.object(app.sys, "platform", "darwin"), \
             patch.object(app, "printer_ready", return_value=True), \
             patch.object(app.subprocess, "run") as run:
            app.ensure_printer()
            run.assert_not_called()

    def test_missing_printer_installs_builtin_driver(self):
        with patch.object(app.sys, "platform", "darwin"), \
             patch.object(app, "printer_ready", side_effect=[False, True]), \
             patch.object(app.Path, "is_file", return_value=True), \
             patch.object(app.subprocess, "run", side_effect=[
                 Mock(returncode=0, stdout=app.DRIVER + " Generic PostScript Printer"),
                 Mock(returncode=0)]) as run, contextlib.redirect_stdout(io.StringIO()):
            app.ensure_printer()
            command = run.call_args_list[1].args[0]
            self.assertIn(app.DRIVER, command)
            self.assertIn(app.PRINTER_URI, command)
            self.assertIn("auth-info-required=username,password", command)
            self.assertEqual(run.call_count, 2)

    def test_admin_permission_fallback(self):
        with patch.object(app.sys, "platform", "darwin"), \
             patch.object(app, "printer_ready", side_effect=[False, True]), \
             patch.object(app.Path, "is_file", return_value=True), \
             patch.object(app.subprocess, "run", side_effect=[
                 Mock(returncode=0, stdout=app.DRIVER + " Generic"),
                 Mock(returncode=1), Mock(returncode=0)]) as run, \
             contextlib.redirect_stdout(io.StringIO()):
            app.ensure_printer()
            self.assertEqual(run.call_args.args[0][0], "/usr/bin/osascript")
            self.assertIn("with administrator privileges", run.call_args.args[0][2])

    def test_missing_driver_stops_before_install(self):
        with patch.object(app.sys, "platform", "darwin"), \
             patch.object(app, "printer_ready", return_value=False), \
             patch.object(app.subprocess, "run", return_value=Mock(returncode=0, stdout="")) as run:
            with self.assertRaises(app.SetupError): app.ensure_printer()
            self.assertEqual(run.call_count, 1)

    def test_setup_failure_never_submits_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "test.pdf"
            pdf.write_bytes(b"%PDF-1.4")
            with patch.object(app.sys, "argv", ["print_msee", str(pdf)]), \
                 patch.object(app, "credentials", return_value={}), \
                 patch.object(app, "ensure_printer", side_effect=app.SetupError("setup failed")), \
                 patch.object(app, "Cups") as cups, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(app.main(), 1)
                cups.assert_not_called()

    def test_setup_only_needs_no_credentials_or_document(self):
        with patch.object(app.sys, "argv", ["print_msee", "--setup"]), \
             patch.object(app, "ensure_printer") as setup, \
             patch.object(app, "credentials") as credentials, \
             patch.object(app, "Cups") as cups, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(app.main(), 0)
            setup.assert_called_once()
            credentials.assert_not_called()
            cups.assert_not_called()


if __name__ == "__main__":
    unittest.main()
