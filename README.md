# ArchLinux Logout

Personal fork of [ArchLinux Logout](https://github.com/arcolinux/archlinux-logout).
It provides a GTK logout menu for Awesome WM/X11 and Hyprland/Wayland, plus an
X11-only wallpaper selector for betterlockscreen.

Build and install from this checkout with:

```sh
makepkg --force --clean --syncdeps --install
```

Run `archlinux-logout` in either session.

The menu provides cancel, logout, restart, shutdown, suspend, hibernate and lock
actions. Buttons can be activated by mouse or their configured keyboard shortcuts;
Escape cancels the menu. Its settings popover controls the theme, opacity, icon
size and font size. Desktop launchers and keybindings are configured separately.

On Wayland, the menu uses GTK Layer Shell to cover the focused monitor, including
the panel, and receive keyboard shortcuts. It requires native GTK Wayland support
and a compositor implementing layer-shell; it does not use XWayland placement.
Themes, opacity, icon/font sizes, button selection and keyboard shortcuts work in
both sessions.

The menu reads `/etc/archlinux-logout.conf` followed by
`~/.config/archlinux-logout/archlinux-logout.conf`, with user values overriding
packaged values. Built-in Wayland lock/logout defaults also cover older system
configuration files preserved by pacman as it installs a `.pacnew`. Existing
user files are preserved. On first launch, the packaged
configuration is copied to the user path; the settings UI saves appearance changes
there.

`[commands]` defines the shared power commands and X11 lock/logout commands.
On Wayland, `[commands-wayland]` overrides matching commands after both files have
been read. To customize Wayland locking or logout, put those values in the user
file's `[commands-wayland]` section; an existing `[commands] lock` remains the X11
command. All six actions (`lock`, `logout`, `shutdown`, `restart`, `suspend`,
`hibernate`) can be overridden in either section.

The Wayland defaults are:

```ini
[commands-wayland]
lock=loginctl lock-session
logout=hyprctl dispatch 'hl.dsp.exit()'
```

The logout command targets Hyprland's Lua configuration. The lock command sends
a session-lock request through logind; it requires a separate service to handle
that request and start a screen locker. For example, hypridle can handle it with
`lock_cmd` configured to launch hyprlock. Alternatively, override the lock command
to launch a suitable locker directly.

Restart, shutdown, suspend and hibernate use systemctl by default. Locking before
sleep must be configured separately in the session's idle or lock service.
Hibernation requires a working system hibernation setup. On X11, logout runs
`pkill awesome` and locking uses betterlockscreen by default.

Configure the Wayland lockscreen in `~/.config/hypr/hyprlock.conf`; the bundled
`archlinux-betterlockscreen` picker continues to configure betterlockscreen on
X11 only. Betterlockscreen and its initial wallpaper caching remain unchanged
for the X11 menu.

Run the headless regression checks from this directory with:

```sh
python3 -m unittest discover -s tests -v
```

For manual verification, run `archlinux-logout` and check appearance, settings
popovers, Escape, focus restoration, repeated opening and monitor selection in
each supported desktop session.
