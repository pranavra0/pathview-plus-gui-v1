# Pathview+ Desktop GUI

Pathview+ includes an optional Qt 6 Widgets application for scientists who
prefer a graphical workflow.  It uses the same public `pathview()` and
`sbgnview()` APIs as Python and the CLI; it does not invoke a subprocess or
parse command output.  The core package remains usable on servers and in
notebooks without Qt.

## Installation and launch

Install the headless package as usual:

```bash
pip install pathview-plus
```

Install the GUI extra only on a machine that needs the desktop application:

```bash
pip install "pathview-plus[gui]"
pathview-plus-gui
```

The equivalent convenience command is:

```bash
pathview-plus gui
```

`PySide6` is imported lazily.  If it is not installed, the launch command
prints:

```text
The Pathview+ GUI requires the optional GUI dependencies.

Install them with:

    pip install "pathview-plus[gui]"
```

This optional dependency is never imported by `import pathview` or by the
existing CLI commands.  For development, install the Qt test dependencies:

```bash
pip install "pathview-plus[gui-dev]"
QT_QPA_PLATFORM=offscreen pytest tests/gui
```

On CI or a headless Linux host, `QT_QPA_PLATFORM=offscreen` allows widget and
service tests to run without an X server.  A normal desktop session should
omit that variable.

## First run

The application opens directly to a new project.  It defaults to KEGG,
human (`hsa`), ENTREZ gene IDs, KEGG compound IDs, automatic rendering, PNG
output, and the publication theme.  The empty preview explains the three
steps: load one or both data files, choose a pathway, and render it.

The **Offline** control is global to the application.  Turning it on calls the
library's `set_offline(True)`.  Organism search, palette lists, the bundled
SBGN catalog, and vector rendering remain available offline.  A resource that
is not already cached cannot be downloaded in offline mode; the resulting
error is shown in the diagnostics panel instead of being hidden.

## KEGG workflow

1. In **Data**, enable the gene and/or compound card and choose a file.
2. In **Pathway**, search for an organism or choose **human**.  Search uses
   Pathview+'s bundled organism table and works without network access.
3. Enter one or more pathway IDs, separated by spaces, commas, or newlines.
   Both `04110` and `hsa04110` are accepted.  IDs are de-duplicated while
   preserving order and are checked syntactically before rendering.
4. In **Appearance**, choose PNG, PDF, or SVG, a theme, and the output
   directory.  Select a KEGG render mode when needed (`auto`, `native`,
   `vector`, `graph`, or `svg`).
5. Press **Render**.  Rendering and downloads run off the Qt event loop.  The
   queue reports each pathway separately, so a failed pathway does not hide
   successful results.  **Cancel after current** stops later queue items
   without terminating a Python thread.

`auto` uses the native KEGG map when its PNG is available and otherwise falls
back to vector rendering.  Native rendering needs the KEGG PNG; vector, SVG,
and graph modes can render from KGML alone.  Use vector or SVG for scalable
figures.

## SBGN workflow

Switch the pathway mode to **SBGN**.  The source and query controls search the
bundled SBGN index offline.  Filter by Reactome, SMPDB, PANTHER, MetaCyc, or
MetaCrop, select one or more rows, and add them to the render queue.  You can
also add a local `.sbgn` file; local paths and collection IDs use the same
queue.  The GUI passes the selected ID or path directly to `sbgnview()`.

For SBGN, SYMBOL is usually the most useful offline gene identifier type.  The
catalog and crosswalk tables are bundled, but the SBGN-ML document for every
catalog entry is not: uncached pathway documents are downloaded on first use
unless offline mode is enabled.

## Molecular input files

Supported extensions are `.csv`, `.tsv`, `.tab`, and `.txt`.  The first column
is always read as string identifiers.  Remaining columns are candidate numeric
conditions and are cast to floating point.  Completely nonnumeric columns are
omitted and listed as a nonfatal warning; they are never silently treated as
measurements.  At least one usable numeric column is required.

For example:

```text
entrez\tControl\tTreated\tdescription
1956\t2.31\t1.82\tEGFR
2099\t-1.14\t0.33\tother
```

Gene and metabolite cards are independent.  A gene-only, compound-only, or
combined run is valid, and each class keeps its own color scale and key.  To
render a pathway without data, select **Render pathway without molecular
data**; for KEGG this uses the core's `map_null=True` behavior.

The preview table shows the first rows, row count, identifier column, usable
conditions, and ignored columns.  Large files are loaded by the service and
are not copied wholesale into Qt widget objects.

## Batch results and diagnostics

The queue can be reordered, removed, or cleared before rendering.  Results
remain visible as success or failure rows.  Selecting a successful row loads
its actual output file into the preview; it does not substitute the core's
intermediate image array.  PNG, SVG, and PDF outputs have fit, 100%, zoom, and
pan controls where supported by the installed Qt version.

Diagnostics are structured information from the core, including input ID
count, mapped ID count, pathway node count, nodes carrying data, condition
names, and available unmapped IDs.  Mapping warnings and download/render
errors appear in the diagnostics and log tabs with the pathway ID and a
human-readable recovery hint.

Common errors and remedies:

* **No usable value column** — add at least one numeric condition after the
  identifier column.
* **Missing input file** — restore or reselect the file; project loading keeps
  the path and marks it missing rather than crashing.
* **Unknown species** — select a result from the organism search, such as
  `hsa`/human or `mmu`/mouse.
* **No mapped IDs** — check the selected gene/compound identifier type and
  inspect the unmapped-ID diagnostics.  Changing the type does not alter the
  source file.
* **Offline resource unavailable** — switch offline mode off to download an
  uncached KGML, PNG, or SBGN-ML file, or place the resource in the configured
  cache directory first.
* **Output directory not writable** — choose an existing writable directory
  or create it before rendering.

## Cache and settings

**Tools → Open Cache Folder** opens the library HTTP cache location.
**Tools → Clear HTTP Cache…** asks for confirmation and removes cached HTTP
resources only.  It does not delete configured KEGG, SBGN, input, or output
directories.  Cache management uses the core `cache_dir()` and
`clear_cache()` functions.

Machine preferences such as window geometry and splitter positions are stored
with Qt settings. Scientific render configuration is stored in project files
and is not silently overridden by those preferences. Recent projects and input
directory history are not part of the v1 settings store.

## Projects

Projects use the `.pvp.json` extension and store configuration (paths,
identifier types, pathway queue, appearance, and mode), not large molecular
tables.  **File → Save Project** and **Open Project…** support round trips and
write a schema version.  Relative and absolute paths are preserved as saved.
A missing referenced file is reported visibly, and unknown fields from a
newer schema are ignored where possible.  Keep the original data files with a
project when sharing it with collaborators.

## Packaging and distribution

The Python wheel includes `pathview.gui`, its service/widget subpackages, and
the bundled `lib/data/*.tsv.gz` resources.  Verify a wheel in a clean
environment with:

```bash
python -m build
python -m venv /tmp/pathview-gui-check
/tmp/pathview-gui-check/bin/pip install dist/pathview_plus-*.whl
/tmp/pathview-gui-check/bin/pathview-plus info
/tmp/pathview-gui-check/bin/pip install "pathview-plus[gui]"
/tmp/pathview-gui-check/bin/pathview-plus-gui
```

For a platform-native standalone application, use the checked-in
`pysidedeploy.spec` with `pyside6-deploy`:

```bash
pyside6-deploy
```

Build separately on Windows, macOS, and Linux; a frozen binary is not
portable across operating systems.  The deployment configuration keeps the
bundled organism, compound, crosswalk, and SBGN index tables.  The license and
upstream pathway-resource terms still apply to both wheel and standalone
installations.
