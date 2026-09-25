[app]
# Run `pyside6-deploy` from the repository root.
title = Pathview+
project_dir = .
input_file = lib/gui/app.py
exec_directory = ./build/gui

[python]
# The GUI imports the installed package directly; keep the package and its
# bundled data visible to the freezer.
packages = pathview

[qt]
# No QML files are used by the Qt Widgets application.
qml_files =
excluded_qml_plugins =

[nuitka]
# Preserve the bundled offline tables in a frozen executable.  Nuitka's
# include-data-dir syntax is passed through by pyside6-deploy.
extra_args = "--include-data-dir=lib/data=pathview/data"
