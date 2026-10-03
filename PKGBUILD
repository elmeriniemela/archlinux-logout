pkgname=archlinux-logout
pkgver=1
pkgrel=1
pkgdesc='GTK logout menu and betterlockscreen wallpaper selector'
arch=('any')
url='https://github.com/elmeriniemela/archlinux-logout'
license=('GPL-3.0-only')
depends=('python' 'python-cairo' 'python-distro' 'python-gobject' 'python-psutil' 'libwnck3' 'betterlockscreen')
backup=('etc/archlinux-logout.conf')

package() {
    install -d "$pkgdir"
    cp -R "$startdir/usr" "$startdir/etc" "$pkgdir/"
    install -Dm644 "$startdir/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
