Appimage : Explanations for including/excluding libraries
=========================================================


GTK/Gnome
---------

By default, in a Gnome session BeeRef pulls a couple of gtk/gdg libs. When opening a native Gnome/GTK file dialog, more gtk/gdl libs are loaded from the system, which might be incompatable.

https://github.com/rbreu/beeref/discussions/103

Current workaround: Exclude the following libs::

  "libgvfsdbus.so"
  "libcanberra-gtk-module.so"
  "libgvfscommon.so"
  "libcanberra-gtk3.so.0"
  "libgdk-3.so.0"
  "libgdk_pixbuf-2.0.so.0"
  "libgio-2.0.so.0"
