#!/bin/bash
# Bundle Qt's XKB/XCB helpers that Nuitka excludes as system libraries.
# Keep graphics drivers, glibc and the core X11 client libraries on the host.
set -euo pipefail

APPDIR=$(realpath "${1:?Usage: bundle_appimage_x11.sh AppDir}")
PLUGIN="$APPDIR/usr/bin/PySide6/qt-plugins/platforms/libqxcb.so"
test -f "$PLUGIN"
DEPENDENCIES=$(ldd "$PLUGIN")
if grep -q 'not found' <<< "$DEPENDENCIES" ; then
  printf '%s\n' "$DEPENDENCIES" >&2
  echo 'Missing Qt X11 dependencies on the build host' >&2
  exit 1
fi

# ldd includes indirect dependencies, e.g. cursor -> image/render-util -> util.
mapfile -t LIBRARIES < <(awk '$1 ~ /^lib(xkbcommon|xcb-)/ && $2 == "=>" && $3 ~ /^\// {print $3}' <<< "$DEPENDENCIES" | sort -u)
if [ "${#LIBRARIES[@]}" -eq 0 ] ; then
  echo 'No Qt X11 helper libraries found; check the plugin layout' >&2
  exit 1
fi
for LIBRARY in "${LIBRARIES[@]}" ; do
  DESTINATION="$APPDIR/usr/bin/$(basename "$LIBRARY")"
  if [ "$(realpath "$LIBRARY")" != "$DESTINATION" ] ; then
    cp -L "$LIBRARY" "$DESTINATION"
  fi
  printf 'Bundled X11 helper: %s\n' "$(basename "$LIBRARY")"
done
