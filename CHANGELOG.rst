0.3.1 - (not released yet)
==========================

Added
-----

* Images can now be stored JPG or PNG inside the bee file. By default,
  small images and images with an alpha channel will be stored as PNG,
  the rest as JPG. In the newly created settings dialog, this
  behaviour can be changed to always use PNG (the former behaviour) or
  always JPG. To apply this behaviour to your old bee files, you can
  save them as new files.
* Antialias/smoothing for displaying images. For images being
  displayed at a large zoom factor, smoothing will turn off to make
  sure that icons, pixel sprites etc can be viewed correctly.
* "Save as" will now open pre-select the folder of the currently opened file


Fixed
-----

* Fixed a bug where the binary data of deleted images would still hang
  around in the bee file.
* Fixed: The shortcut to move the BeeRef window (Ctrl + Alt + Drag)
  not working on an empty scene


0.3.0 - 2023-11-23
==================

Added
-----

* Image cropping (Go to "Transform -> Crop", or press Shift + C)
* Show list of recent files on welcome screen
* Keyboard shortcuts can now be configured via a settings file.
  Go to "Settings -> Open Settings Folder" and edit KeyboardSettings.ini
* Remember window geometry when closing (by David Andrs)

Fixed
-----

* Various typos (by luzpaz)
* Ensure that small items always have an area in the middle for
  moving/editing that doesn't trigger transform actions
* Ensure that the first click to select an item doesn't immediately trigger
  transform actions


0.2.0 - 2021-09-06
==================

Note that bee files from version 0.2.0 won't open in BeeRef 0.1.x.

Added
-----

* You can now add plain text notes and paste text from the clipboard
* You can now open bee files from finder on MacOS (by David Andrs)
* Dragging bee files onto an empty scene will now open them
* Adding the first image(s) to a new scene centers the view

Changed
-------

* Make debug log file less verbose
* The program is now bundled as a single executable file (issue #4)

Fixed
-----

* Hovering over the scale handles of very narrow items now displays
  correct cursor orientation
* Fix a rare crash while displaying selection handles


0.1.1 - 2021-07-18
==================

Changed
-------

* Flipping an image now happens on mouse press instead of mouse release
* About dialog points to new website beeref.org
* Menus and dialogs now have a dark style to match the optics of the canvas

Fixed
-----

* Double click to zoom an item and double-clicking again should now always
  correctly go back to the previous position
* The outline of the rubberband selection now stays the same size
  regardless of zoom


0.1.0 - 2021-07-10
==================

First release!
