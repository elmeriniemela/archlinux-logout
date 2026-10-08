# =====================================================
#        Authors Brad Heffernan, Fennec and Erik Dubois
# =====================================================

import cairo
import gi
import shutil
import GUI
import Functions as fn
import threading
import signal

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk, GdkPixbuf, Gdk, GLib  # noqa

if fn.sessionw:
    gi.require_version("GtkLayerShell", "0.1")
    from gi.repository import GtkLayerShell


class TransparentWindow(Gtk.Window):
    cmd_shutdown = "systemctl poweroff"
    cmd_restart = "systemctl reboot"
    cmd_suspend = "systemctl suspend"
    cmd_hibernate = "systemctl hibernate"

    cmd_logout = "pkill awesome"
    cmd_lock = 'betterlockscreen -l dim -- --time-str="%H:%M"'
    wallpaper = "/usr/share/archlinux-betterlockscreen/wallpapers/wallpaper.jpg"
    d_buttons = [
        "cancel",
        "shutdown",
        "restart",
        "suspend",
        "hibernate",
        "lock",
        "logout",
    ]
    binds = {
        "lock": "K",
        "restart": "R",
        "shutdown": "S",
        "suspend": "U",
        "hibernate": "H",
        "logout": "L",
        "cancel": "Escape",
        "settings": "P",
    }
    theme = "white"
    hover = "#ffffff"
    icon = 64
    font = 11
    buttons = None
    active = False
    opacity = 0.8

    def __init__(self):
        super(TransparentWindow, self).__init__(
            type=Gtk.WindowType.TOPLEVEL, title="ArchLinux Logout"
        )
        if fn.sessionw:
            self.configure_wayland()
        else:
            self.set_keep_above(True)
            self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.connect("delete-event", self.on_close)
        self.connect("destroy", self.on_close)
        self.connect("draw", self.draw)
        self.connect("key-press-event", self.on_keypress)
        self.connect("window-state-event", self.on_window_state_event)
        self.set_decorated(False)

        if not fn.os.path.isdir(fn.home + "/.config/archlinux-logout"):
            fn.os.mkdir(fn.home + "/.config/archlinux-logout")

        if not fn.os.path.isfile(
            fn.home + "/.config/archlinux-logout/archlinux-logout.conf"
        ):
            shutil.copy(
                fn.root_config,
                fn.home + "/.config/archlinux-logout/archlinux-logout.conf",
            )

        self.width = 0
        self.screen = self.get_screen()

        self.display = Gdk.Display.get_default()

        seat = self.display.get_default_seat()

        self.pointer = Gdk.Seat.get_pointer(seat)

        visual = self.screen.get_rgba_visual()
        if visual and self.screen.is_composited():
            self.set_visual(visual)

        fn.get_config(self, Gdk, Gtk, fn.config)

        if not fn.sessionw:
            self.display_on_monitor()

        if self.buttons is None or self.buttons == [""]:
            self.buttons = self.d_buttons

        self.set_app_paintable(True)

        GUI.GUI(self, Gtk, GdkPixbuf, fn.working_dir, fn.os, Gdk, fn)

    def configure_wayland(self):
        if not GtkLayerShell.is_supported():
            raise RuntimeError("Wayland logout menu requires a compositor with layer-shell support")
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "archlinux-logout")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_exclusive_zone(self, -1)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)

    def display_on_monitor(self):
        print("#### Archlinux Logout ####")
        try:
            # test to see this device is a mouse
            if self.pointer.get_has_cursor():
                screen = None
                x = 0
                y = 0
                display = None

                screen, x, y = self.pointer.get_position()

                if screen is not None and x != 0 and y != 0:
                    print(f"[DEBUG]: Mouse position x={x} y={y}")

                    # Returns the GdkDisplay to which device is connected
                    display = self.pointer.get_display()

                    if display is not None:
                        # use the mouse cursor x,y coordinates
                        monitor = display.get_monitor_at_point(x, y)
                        print(
                            f"[DEBUG]: Monitor: Primary={monitor.is_primary()}, Height={monitor.get_height_mm()}, Width={monitor.get_width_mm()}"
                        )
                        geometry = monitor.get_geometry()
                        print(
                            f"[DEBUG]: Monitor: Dimension={geometry.width}x{geometry.height}"
                        )
                        self.set_size_request(geometry.width, geometry.height)
                        # move the window using the mouse pointer x,y coordinates
                        self.move(x, y)
                        self.fullscreen()
                else:
                    # default show on first monitor
                    self.display_on_default()

            else:
                # default show on first monitor
                self.display_on_default()
        except Exception as e:
            print(f"[ERROR]: Exception in display_on_monitor(): {e}")

    # X11 fallback when the mouse position cannot be captured.
    def display_on_default(self):
        # default show on first monitor
        monitor = self.display.get_monitor(0)
        geometry = monitor.get_geometry()
        print("[DEBUG]: Showing on first monitor")
        print(f"[DEBUG]: Dimension: {geometry.width}x{geometry.height}")
        self.set_size_request(geometry.width, geometry.height)
        self.fullscreen_on_monitor(self.screen, 0)

    def on_save_clicked(self, widget):
        config_path = fn.home + "/.config/archlinux-logout/archlinux-logout.conf"
        with open(config_path) as f:
            lines = f.readlines()

        lines[fn._get_position(lines, "opacity")] = "opacity=" + str(int(self.hscale.get_value())) + "\n"
        lines[fn._get_position(lines, "icon_size")] = "icon_size=" + str(int(self.icons.get_value())) + "\n"
        lines[fn._get_position(lines, "theme=")] = "theme=" + self.themes.get_active_text() + "\n"
        lines[fn._get_position(lines, "font_size=")] = "font_size=" + str(int(self.fonts.get_value())) + "\n"

        with open(config_path, "w") as f:
            f.writelines(lines)
        self.popover.popdown()

    def on_mouse_in(self, widget, event, data):
        if data == self.binds.get("shutdown"):
            psh = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/shutdown_blur.svg"
                ),
                self.icon,
                self.icon,
            )
            self.imagesh.set_from_pixbuf(psh)
            self.lbl1.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">Shutdown ({data})</span>'
            )
        elif data == self.binds.get("restart"):
            pr = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/restart_blur.svg"
                ),
                self.icon,
                self.icon,
            )
            self.imager.set_from_pixbuf(pr)
            self.lbl2.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">Reboot ({data})</span>'
            )
        elif data == self.binds.get("suspend"):
            ps = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/suspend_blur.svg"
                ),
                self.icon,
                self.icon,
            )
            self.images.set_from_pixbuf(ps)
            self.lbl3.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">Suspend ({data})</span>'
            )
        elif data == self.binds.get("lock"):
            plk = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/lock_blur.svg"
                ),
                self.icon,
                self.icon,
            )
            self.imagelk.set_from_pixbuf(plk)
            self.lbl4.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">Lock ({data})</span>'
            )
        elif data == self.binds.get("logout"):
            plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/logout_blur.svg"
                ),
                self.icon,
                self.icon,
            )
            self.imagelo.set_from_pixbuf(plo)
            self.lbl5.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">Logout ({data})</span>'
            )
        elif data == self.binds.get("cancel"):
            plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/cancel_blur.svg"
                ),
                self.icon,
                self.icon,
            )
            self.imagec.set_from_pixbuf(plo)
            self.lbl6.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">Cancel ({data})</span>'
            )
        elif data == self.binds.get("hibernate"):
            plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/hibernate_blur.svg"
                ),
                self.icon,
                self.icon,
            )
            self.imageh.set_from_pixbuf(plo)
            self.lbl7.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">Hibernate ({data})</span>'
            )
        elif data == self.binds.get("settings"):
            pset = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(fn.working_dir, "configure_blur.svg"), 48, 48
            )
            self.imageset.set_from_pixbuf(pset)
        elif data == "light":
            pset = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(fn.working_dir, "light_blur.svg"), 48, 48
            )
            self.imagelig.set_from_pixbuf(pset)
        event.window.set_cursor(Gdk.Cursor(Gdk.CursorType.HAND2))

    def on_mouse_out(self, widget, event, data):
        if not self.active:
            if data == self.binds.get("shutdown"):
                psh = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/shutdown.svg"
                    ),
                    self.icon,
                    self.icon,
                )
                self.imagesh.set_from_pixbuf(psh)
                self.lbl1.set_markup(
                    f'<span size="{str(self.font)}000">Shutdown ({data})</span>'
                )
            elif data == self.binds.get("restart"):
                pr = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/restart.svg"
                    ),
                    self.icon,
                    self.icon,
                )
                self.imager.set_from_pixbuf(pr)
                self.lbl2.set_markup(
                    f'<span size="{str(self.font)}000">Reboot ({data})</span>'
                )
            elif data == self.binds.get("suspend"):
                ps = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/suspend.svg"
                    ),
                    self.icon,
                    self.icon,
                )
                self.images.set_from_pixbuf(ps)
                self.lbl3.set_markup(
                    f'<span size="{str(self.font)}000">Suspend ({data})</span>'
                )
            elif data == self.binds.get("lock"):
                plk = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/lock.svg"
                    ),
                    self.icon,
                    self.icon,
                )
                self.imagelk.set_from_pixbuf(plk)
                self.lbl4.set_markup(
                    f'<span size="{str(self.font)}000">Lock ({data})</span>'
                )
            elif data == self.binds.get("logout"):
                plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/logout.svg"
                    ),
                    self.icon,
                    self.icon,
                )
                self.imagelo.set_from_pixbuf(plo)
                self.lbl5.set_markup(
                    f'<span size="{str(self.font)}000">Logout ({data})</span>'
                )
            elif data == self.binds.get("cancel"):
                plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/cancel.svg"
                    ),
                    self.icon,
                    self.icon,
                )
                self.imagec.set_from_pixbuf(plo)
                self.lbl6.set_markup(
                    f'<span size="{str(self.font)}000">Cancel ({data})</span>'
                )
            elif data == self.binds.get("hibernate"):
                plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/hibernate.svg"
                    ),
                    self.icon,
                    self.icon,
                )
                self.imageh.set_from_pixbuf(plo)
                self.lbl7.set_markup(
                    f'<span size="{str(self.font)}000">Hibernate ({data})</span>'
                )
            elif data == self.binds.get("settings"):
                pset = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(fn.working_dir, "configure.svg"), 48, 48
                )
                self.imageset.set_from_pixbuf(pset)
            elif data == "light":
                pset = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(fn.working_dir, "light.svg"), 48, 48
                )
                self.imagelig.set_from_pixbuf(pset)

    def on_click(self, widget, event, data):
        self.click_button(widget, data)

    def on_window_state_event(self, widget, ev):
        self.__is_fullscreen = bool(
            ev.new_window_state & Gdk.WindowState.FULLSCREEN
        )  # noqa

    def draw(self, widget, context):
        context.set_source_rgba(0, 0, 0, self.opacity)
        context.set_operator(cairo.OPERATOR_SOURCE)
        context.paint()
        context.set_operator(cairo.OPERATOR_OVER)

    def on_keypress(self, widget=None, event=None, data=None):
        self.shortcut_keys = [
            self.binds.get("cancel"),
            self.binds.get("shutdown"),
            self.binds.get("restart"),
            self.binds.get("suspend"),
            self.binds.get("logout"),
            self.binds.get("lock"),
            self.binds.get("hibernate"),
            self.binds.get("settings"),
        ]

        for key in self.shortcut_keys:
            if event.keyval == Gdk.keyval_to_lower(Gdk.keyval_from_name(key)):
                self.click_button(widget, key)

    def click_button(self, widget, data=None):
        if not data == self.binds.get("settings") and not data == "light":
            self.active = True
            fn.button_toggled(self, data)
            fn.button_active(self, data, GdkPixbuf)

        if data == self.binds.get("logout"):
            self.execute_command(self.cmd_logout)
        elif data == self.binds.get("restart"):
            self.execute_command(self.cmd_restart)
        elif data == self.binds.get("shutdown"):
            self.execute_command(self.cmd_shutdown)
        elif data == self.binds.get("suspend"):
            self.execute_command(self.cmd_suspend)
        elif data == self.binds.get("hibernate"):
            self.execute_command(self.cmd_hibernate)

        elif data == self.binds.get("lock"):
            if self.cmd_lock.startswith("betterlockscreen") and not fn.os.path.isdir(
                fn.home + "/.cache/betterlockscreen"
            ):
                if fn.os.path.isfile(self.wallpaper):
                    self.lbl_stat.set_markup(
                        '<span size="x-large"><b>Caching lockscreen images for a faster locking next time</b></span>'
                    )  # noqa
                    t = threading.Thread(
                        target=fn.cache_bl,
                        args=(
                            self,
                            GLib,
                            Gtk,
                        ),
                    )
                    t.daemon = True
                    t.start()
                else:
                    self.lbl_stat.set_markup(
                        '<span size="x-large"><b>Choose a wallpaper with archlinux-betterlockscreen</b></span>'
                    )  # noqa
                    self.Ec.set_sensitive(True)
                    self.active = False
            else:
                self.execute_command(self.cmd_lock)
        elif data == self.binds.get("settings"):
            self.themes.grab_focus()
            self.popover.set_relative_to(self.Eset)
            self.popover.show_all()
            self.popover.popup()
        elif data == "light":
            self.popover2.set_relative_to(self.Elig)
            self.popover2.show_all()
            self.popover2.popup()
        else:
            self.on_close(widget)

    def execute_command(self, cmdline):
        self.hide()
        self.display.flush()
        fn.os.system(cmdline)
        Gtk.main_quit()

    def on_close(self, widget, data=None):
        Gtk.main_quit()

    def message_box(self, message, title):
        md = Gtk.MessageDialog(
            parent=self,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.YES_NO,
            text=title,
        )
        md.format_secondary_markup(message)  # noqa

        result = md.run()
        md.destroy()

        if result in (Gtk.ResponseType.OK, Gtk.ResponseType.YES):
            return True
        else:
            return False


def signal_handler(sig, frame):
    print("\nArchLinux-Logout is Closing.")
    Gtk.main_quit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        lock = open("/tmp/archlinux-logout.lock", "x")
    except FileExistsError:
        print("ArchLinux Logout is already open, or /tmp/archlinux-logout.lock is stale.")
    else:
        lock.close()
        try:
            with open("/tmp/archlinux-logout.pid", "w") as f:
                f.write(str(fn.os.getpid()))
            w = TransparentWindow()
            w.show_all()
            Gtk.main()
        finally:
            fn.cleanup()
