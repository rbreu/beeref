---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: default
---

BeeRef lets you quickly arrange your reference images and view them while you create. Its minimal interface is designed not to get in the way of your creative process.

![Screenshot of BeeRef]({{ site.baseurl}}/assets/images/screenshot.png)


## Installation

Get the zip file for your operating system (Windows, Linux, macOS) from the [latest release]({{ site.github.latest_release.html_url }}). Extract the zip file. Inside the extracted folder, you will find a BeeRef executable.

**Linux users** who want to have BeeRef appear in the app menu, save the desktop file from the [release section]({{ site.github.latest_release.html_url }}) in `~/.local/share/applications` and adjust the path names in the file to match the location of your BeeRef installation.

**MacOS X users**, look at [detailed instructions]({% link macosx-run.md %}) if you have problems running BeeRef.

## Features

* Move, scale, rotate and flip images
* Mass-scale images to the same width, height or size
* Mass-arrange images vertically, horizontally or for optimal usage of space
* Enable alaways-on-top-mode and disable the title bar to let the BeeRef window unobtrusively float above your art program:

![Screenshot of BeeRef over other program]({{ site.baseurl}}/assets/images/screenshot_float.png)


### Regarding the bee file format

Currently, all images are embedded into the bee file as png files. While png is a lossless format, it may also produce larger file sizes than compressed jpg files, so bee files may become bigger than the imported images on their own. More embedding options are to come later.

The bee file format is a sqlite database inside which the images are stored in an sqlar table—meaning they can be extracted with the [sqlite command line program](<https://www.sqlite.org/cli.html>):

```
sqlite3 myfile.bee -Axv
```

Options for exporting from inside BeeRef are planned, but the above always works independently of BeeRef.
