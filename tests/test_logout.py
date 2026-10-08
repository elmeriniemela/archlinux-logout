"""Headless checks: no desktop connection or real session/power commands."""

import importlib.util
import io
import os
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "usr/share/archlinux-logout"


def load_functions(environment):
    spec = importlib.util.spec_from_file_location("logout_functions", SOURCE / "Functions.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(os.environ, environment, clear=True):
        spec.loader.exec_module(module)
    return module


class LogoutTests(unittest.TestCase):
    def setUp(self):
        self.fn = load_functions({"XDG_SESSION_TYPE": "wayland"})
        self.fn.root_config = str(ROOT / "etc/archlinux-logout.conf")
        self.gtk = Mock()
        self.gtk.Window = object
        self.layer = Mock()
        repository = SimpleNamespace(
            Gtk=self.gtk, Gdk=Mock(), GdkPixbuf=Mock(), GLib=Mock(),
            GtkLayerShell=self.layer,
        )
        self.modules = {
            "cairo": Mock(), "gi": Mock(), "gi.repository": repository,
            "Functions": self.fn, "GUI": Mock(),
        }
        with patch.dict("sys.modules", self.modules):
            app = runpy.run_path(str(SOURCE / "archlinux-logout.py"))
        self.window = object.__new__(app["TransparentWindow"])
        self.window.hide = Mock()
        self.window.display = Mock()
        self.window.binds = self.window.binds.copy()

    def configure(self, user_text="", wayland=True):
        self.fn.sessionw = wayland
        # Read the real packaged defaults, with an in-memory user file.
        original_open = open

        def read_config(filename, *args, **kwargs):
            if filename == "user.conf":
                return io.StringIO(user_text)
            return original_open(filename, *args, **kwargs)

        with patch("builtins.open", side_effect=read_config):
            self.fn.get_config(self.window, Mock(), self.gtk, "user.conf")

    def test_session_detection_without_environment(self):
        self.assertFalse(load_functions({}).sessionw)
        self.assertFalse(load_functions({"XDG_SESSION_TYPE": "x11"}).sessionw)
        self.assertTrue(load_functions({"WAYLAND_DISPLAY": "wayland-1"}).sessionw)

    def test_wayland_defaults_override_legacy_x11_lock(self):
        self.configure('[commands]\nlock=my-x11-lock\nlogout=my-x11-exit\n')
        self.assertEqual(self.window.cmd_lock, "loginctl lock-session")
        self.assertEqual(self.window.cmd_logout, "hyprctl dispatch 'hl.dsp.exit()'")

    def test_legacy_packaged_config_still_gets_wayland_defaults(self):
        legacy = "[commands]\nlock=betterlockscreen -l\n"
        with patch("builtins.open", side_effect=lambda *args, **kwargs: io.StringIO(legacy)):
            self.fn.get_config(self.window, Mock(), self.gtk, "user.conf")
        self.assertEqual(self.window.cmd_lock, "loginctl lock-session")
        self.assertEqual(self.window.cmd_logout, "hyprctl dispatch 'hl.dsp.exit()'")

    def test_x11_keeps_user_commands(self):
        self.configure('[commands]\nlock=my-x11-lock\nlogout=my-x11-exit\n', wayland=False)
        self.assertEqual(self.window.cmd_lock, "my-x11-lock")
        self.assertEqual(self.window.cmd_logout, "my-x11-exit")

    def test_x11_defaults(self):
        self.configure(wayland=False)
        self.assertTrue(self.window.cmd_lock.startswith("betterlockscreen"))
        self.assertEqual(self.window.cmd_logout, "pkill awesome")

    def test_user_wayland_overrides_and_shared_power_commands(self):
        self.configure(
            '[settings]\nopacity=42\n[commands]\nsuspend=shared-suspend\n'
            '[commands-wayland]\nlock=custom-lock\nlogout=custom-exit\nrestart=custom-restart\n'
        )
        self.assertEqual(self.window.opacity, 0.42)
        self.assertEqual(self.window.cmd_lock, "custom-lock")
        self.assertEqual(self.window.cmd_logout, "custom-exit")
        self.assertEqual(self.window.cmd_restart, "custom-restart")
        self.assertEqual(self.window.cmd_suspend, "shared-suspend")

    def test_actions_execute_selected_commands_without_caching_on_wayland(self):
        self.configure()
        with patch.object(self.fn, "button_toggled"), patch.object(self.fn, "button_active"), \
                patch.object(self.fn.os, "system") as execute, \
                patch.object(self.fn, "cache_bl") as cache:
            for action in ("lock", "logout", "restart", "shutdown", "suspend", "hibernate"):
                with self.subTest(action=action):
                    self.window.click_button(None, self.window.binds[action])
                    execute.assert_called_with(getattr(self.window, "cmd_" + action))
            self.assertEqual(execute.call_count, 6)
            cache.assert_not_called()
        self.assertEqual(self.window.hide.call_count, 6)

    def test_cancel_and_repeated_close_do_not_execute_commands(self):
        with patch.object(self.fn, "button_toggled"), patch.object(self.fn, "button_active"), \
                patch.object(self.fn.os, "system") as execute:
            self.window.click_button(None, self.window.binds["cancel"])
            self.window.on_close(None)
            self.window.on_close(None)
            execute.assert_not_called()

    def test_startup_failure_cleans_up_owned_lock_files(self):
        with patch.dict("sys.modules", self.modules), patch("builtins.open", Mock()), \
                patch("signal.signal"), patch.object(self.fn, "cleanup") as cleanup:
            # The headless Window base rejects construction, simulating startup failure.
            with self.assertRaises(TypeError):
                runpy.run_path(str(SOURCE / "archlinux-logout.py"), run_name="__main__")
            cleanup.assert_called_once_with()

    def test_second_launch_does_not_remove_first_launch_lock(self):
        with patch.dict("sys.modules", self.modules), \
                patch("builtins.open", side_effect=FileExistsError), \
                patch("signal.signal"), patch("builtins.print"), \
                patch.object(self.fn, "cleanup") as cleanup:
            runpy.run_path(str(SOURCE / "archlinux-logout.py"), run_name="__main__")
            cleanup.assert_not_called()

    def test_cleanup_tolerates_missing_files(self):
        with patch.object(self.fn, "Path") as path:
            self.fn.cleanup()
            self.fn.cleanup()
        self.assertEqual(path.call_args_list, [
            call("/tmp/archlinux-logout.lock"), call("/tmp/archlinux-logout.pid"),
            call("/tmp/archlinux-logout.lock"), call("/tmp/archlinux-logout.pid"),
        ])
        path.return_value.unlink.assert_called_with(missing_ok=True)

    def test_wayland_overlay_covers_monitor_and_receives_keyboard(self):
        self.window.configure_wayland()
        self.layer.init_for_window.assert_called_once_with(self.window)
        self.layer.set_layer.assert_called_once_with(self.window, self.layer.Layer.OVERLAY)
        self.assertEqual(self.layer.set_anchor.call_count, 4)
        self.layer.set_exclusive_zone.assert_called_once_with(self.window, -1)
        self.layer.set_keyboard_mode.assert_called_once_with(
            self.window, self.layer.KeyboardMode.EXCLUSIVE,
        )
        self.layer.set_monitor.assert_not_called()

    def test_unsupported_wayland_backend_fails_before_mapping(self):
        self.layer.is_supported.return_value = False
        with self.assertRaisesRegex(RuntimeError, "layer-shell"):
            self.window.configure_wayland()
        self.layer.init_for_window.assert_not_called()


if __name__ == "__main__":
    unittest.main()
