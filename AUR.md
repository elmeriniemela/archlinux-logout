# Publishing archlinux-logout to the AUR

The current `PKGBUILD` builds from this local checkout using `$startdir/usr` and
`$startdir/etc`. An AUR user will not have those files. First make the package
download a versioned source archive from the GitHub repository.

## 1. Publish a versioned source archive

From this repository, commit the version you want to publish, including `usr/`,
`etc/`, and `LICENSE`. Tag that commit and push the tag to GitHub:

```sh
git tag v1.0.0
git push origin v1.0.0
```

Use another version number if appropriate. The tag must exist on GitHub before
you calculate the archive checksum.

## 2. Make the PKGBUILD self-contained

In `PKGBUILD`, set `pkgver=1.0.0` and `pkgrel=1`. Keep the existing package
metadata and dependencies, then add the source archive and its checksum and
replace `package()` with:

```bash
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('REPLACE_WITH_ARCHIVE_SHA256')

package() {
    install -d "$pkgdir"
    cp -a "$srcdir/$pkgname-$pkgver/usr" "$srcdir/$pkgname-$pkgver/etc" "$pkgdir/"
    install -Dm644 "$srcdir/$pkgname-$pkgver/LICENSE" \
        "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
```

Run `updpkgsums` to replace the checksum placeholder with the archive's actual
SHA-256 checksum (`updpkgsums` is provided by `pacman-contrib`). Test the build
from a clean working directory containing only the updated `PKGBUILD`:

```sh
updpkgsums
makepkg -Cfs
```

This checks that `makepkg` can fetch the application files without this local
checkout. Do not upload the built `.pkg.tar.zst` file to the AUR.

## 3. Submit the build recipe

Create an [AUR account](https://aur.archlinux.org/register) and add an SSH public
key to its account settings. Check that the
[`archlinux-logout` package name](https://aur.archlinux.org/packages/archlinux-logout)
is still available. Then clone its AUR repository into a separate directory:

```sh
git -c init.defaultBranch=master clone ssh://aur@aur.archlinux.org/archlinux-logout.git
cd archlinux-logout
cp /path/to/your/updated/PKGBUILD .
makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD .SRCINFO
git commit -m "Initial package"
git push
```

Replace `/path/to/your/updated/PKGBUILD` with the path to this repository's
updated `PKGBUILD`. The AUR Git repository needs `PKGBUILD` and `.SRCINFO`;
GitHub hosts the application source. Regenerate `.SRCINFO` whenever package
metadata changes, including `pkgver` or `pkgrel`.

References: [AUR submission guidelines](https://wiki.archlinux.org/title/AUR_submission_guidelines)
and [PKGBUILD documentation](https://wiki.archlinux.org/title/PKGBUILD).
