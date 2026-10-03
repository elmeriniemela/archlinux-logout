# ArchLinux Logout

Personal fork of [ArchLinux Logout](https://github.com/erikdubois/archlinux-logout).
It provides a GTK logout menu for Awesome WM and a wallpaper selector for
betterlockscreen.

Build and install from this checkout with:

```sh
makepkg --force --clean --syncdeps --install
```

The logout menu's defaults are in `etc/archlinux-logout.conf`. The menu writes
changes made in its settings UI to `~/.config/archlinux-logout/archlinux-logout.conf`.
