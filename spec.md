# Pathview+ Desktop GUI v1

## Full implementation specification

### 1. Mission

Implement a production-quality desktop GUI for the existing `raw-lab/pathview-plus` Python package.

The GUI must make the major existing Pathview+ functionality usable by a scientist without writing Python or CLI commands while preserving the underlying library's behavior.

This is not a prototype or dashboard. Build a coherent v1 desktop application suitable for release with the Python package.

The implementation must:

* use the existing Pathview+ Python API directly;
* remain fully compatible with the existing CLI and Python API;
* support KEGG and SBGN workflows;
* support gene-only, metabolite-only, combined multi-omics, and pathway-only rendering;
* provide data inspection before rendering;
* provide useful mapping diagnostics after rendering;
* remain responsive during network requests and rendering;
* support offline operation;
* support single and batch pathway rendering;
* preview PNG, SVG, and PDF results;
* provide standalone application packaging groundwork;
* include automated GUI/service tests;
* keep all existing project tests passing.

Do not implement the GUI as a subprocess wrapper around `pathview-plus`.

Do not parse CLI stdout to obtain results.

The GUI must call `pathview()`, `sbgnview()`, and related public library functions directly.

---

# 2. Technology decision

Use:

* Python 3.10+
* PySide6 / Qt 6 Widgets
* existing Polars data structures
* existing Pathview+ rendering stack
* `pytest`
* `pytest-qt` for GUI tests
* `pyside6-deploy` as the supported standalone packaging path

Use traditional Qt Widgets rather than QML for v1.

Rationale:

* Pathview+ is already a Python desktop-oriented computational library.
* Native filesystem interaction is central.
* Large pathway images need reliable zoom/pan.
* Background workers are needed.
* SVG/PDF preview is useful.
* Qt gives mature native widgets and cross-platform deployment.
* Avoid introducing a web server, browser runtime, JavaScript toolchain, or frontend/backend protocol.

Suggested GUI dependency:

```toml
[project.optional-dependencies]
gui = [
    "PySide6>=6.8,<7",
]

gui-dev = [
    "PySide6>=6.8,<7",
    "pytest-qt>=4.4",
]
```

The existing core installation must remain usable without PySide6:

```bash
pip install pathview-plus
```

GUI users install:

```bash
pip install "pathview-plus[gui]"
```

---

# 3. Entrypoints

Add:

```toml
[project.scripts]
pathview-plus = "pathview.cli:main"
pathview-cli = "pathview.cli:main"
pathview-plus-gui = "pathview.gui.app:main"
```

Also add a CLI convenience command:

```bash
pathview-plus gui
```

The GUI import must remain lazy.

If PySide6 is unavailable, display a concise actionable error:

```text
The Pathview+ GUI requires the optional GUI dependencies.

Install them with:

    pip install "pathview-plus[gui]"
```

The normal library and existing CLI must never import PySide6.

---

# 4. Package layout

Add a dedicated GUI subpackage.

```text
lib/
├── __init__.py
├── pathview.py
├── sbgnview.py
├── ...
└── gui/
    ├── __init__.py
    ├── app.py
    ├── main_window.py
    ├── models.py
    ├── settings.py
    ├── workers.py
    ├── services/
    │   ├── __init__.py
    │   ├── input_service.py
    │   ├── render_service.py
    │   ├── pathway_service.py
    │   └── project_service.py
    └── widgets/
        ├── __init__.py
        ├── data_input.py
        ├── pathway_selector.py
        ├── appearance_panel.py
        ├── advanced_panel.py
        ├── preview.py
        ├── diagnostics.py
        ├── results_table.py
        └── drop_line_edit.py
```

Update setuptools configuration so `pathview.gui` and its subpackages are included in the wheel.

Do not move or rename existing public modules unless strictly necessary.

---

# 5. Core architectural rule

The GUI must consist of three layers.

## 5.1 Qt presentation layer

Contains widgets and presentation logic only.

Responsibilities:

* collect inputs;
* display state;
* validation feedback;
* display results;
* user interaction.

It must not contain biological mapping logic.

## 5.2 GUI service layer

Converts GUI configuration into calls to Pathview+.

Responsibilities:

* input parsing;
* species lookup;
* pathway catalog lookup;
* translating GUI settings into `pathview()` / `sbgnview()` arguments;
* organizing batch runs;
* converting results into display models;
* project JSON serialization.

## 5.3 Existing Pathview+ core

Remains source of truth for:

* identifier mapping;
* organism resolution;
* downloading;
* SBGN collection;
* rendering;
* diagnostics;
* errors;
* color scales.

Do not reimplement these algorithms inside the GUI.

---

# 6. Main window

Use a `QMainWindow`.

Recommended layout:

```text
┌───────────────────────────────────────────────────────────────────┐
│ File  View  Tools  Help                         Offline: ○         │
├───────────────────┬───────────────────────────────────────────────┤
│                   │                                               │
│  INPUTS           │                                               │
│  PATHWAY          │             PATHWAY PREVIEW                   │
│  APPEARANCE       │                                               │
│  ADVANCED         │                                               │
│                   │                                               │
│                   │                                               │
│                   │                                               │
│  [ Render ]       │                                               │
│                   │                                               │
├───────────────────┴───────────────────────────────────────────────┤
│ Results | Diagnostics | Log                                      │
└───────────────────────────────────────────────────────────────────┘
```

Use `QSplitter` so the user can resize:

* left configuration pane;
* right preview pane;
* bottom results/diagnostics pane.

Persist splitter positions and window geometry with `QSettings`.

Recommended minimum window size:

```text
1100 × 700
```

Default:

```text
1400 × 900
```

---

# 7. Left workflow panel

The left pane is a `QTabWidget` or vertically stacked set of collapsible groups with these sections:

1. Data
2. Pathway
3. Appearance
4. Advanced

The primary Render button remains visible at the bottom regardless of selected section.

Do not put every library parameter on screen simultaneously.

---

# 8. Data input workflow

Provide two independent cards:

* Gene / protein data
* Compound / metabolite data

Each card contains:

* enable checkbox;
* file path field;
* Browse button;
* drag/drop support;
* identifier type selector;
* dataset summary;
* Preview Data button/table.

Supported files for v1:

```text
.csv
.tsv
.tab
.txt
```

Match existing CLI input semantics:

* first column is identifiers;
* all later columns are candidate data columns;
* first column is always treated as strings;
* later columns are cast to floating point;
* completely nonnumeric columns are omitted;
* at least one usable numeric column is required.

The GUI should show omitted columns as a nonfatal warning.

Example:

```text
Loaded rna.csv

1,942 rows
Identifier: gene
Conditions: Control, Treated
Ignored: description
```

Do not silently drop columns.

### Data preview

Provide a modal or embedded table showing:

* first 50 rows;
* all usable columns;
* identifier column highlighted visually;
* total row count;
* total condition count.

Use a `QAbstractTableModel` backed by Polars.

Do not convert entire large datasets to lists merely to populate a widget.

---

# 9. Identifier type selectors

Populate dynamically from the library.

Gene IDs:

```python
supported_gene_idtypes()
```

Compound IDs:

```python
supported_cpd_idtypes()
```

Do not hardcode the full option list.

Recommended defaults:

KEGG:

```text
Gene: ENTREZ
Compound: KEGG
```

SBGN:

```text
Gene: SYMBOL
Compound: KEGG
```

When switching pathway mode, preserve an explicit user selection, but update defaults if the field has never been changed.

For SBGN, display helper text:

```text
SYMBOL generally provides the densest offline gene coverage for SBGN maps.
```

---

# 10. No-data pathway rendering

Support rendering a pathway without omics data.

Add:

```text
☐ Render pathway without molecular data
```

If neither data card is enabled and this option is unchecked:

* disable Render;
* show validation message.

For KEGG, call with:

```python
map_null=True
```

For SBGN, pass both datasets as `None`.

---

# 11. Pathway mode

Use two explicit modes:

```text
KEGG
SBGN
```

Do not pretend they are identical workflows.

---

# 12. KEGG pathway selection

KEGG panel contains:

### Species selector

Use a searchable combo/autocomplete field.

Search must use:

```python
search_organisms()
```

Resolve final selection using:

```python
get_species_code()
```

Search should be debounced by roughly 200–300 ms.

Display search rows as:

```text
hsa   Homo sapiens (human)
mmu   Mus musculus (house mouse)
rno   Rattus norvegicus (Norway rat)
```

Species lookup must work offline.

Once selected, show the canonical KEGG code.

### Pathway ID input

Support one or multiple KEGG IDs.

Accept:

```text
04110
04010
00020
```

or:

```text
hsa04110
```

Allow separators:

* newline;
* comma;
* whitespace.

Convert these into an ordered unique list.

Display them as a small table:

```text
Pathway       Status
04110         Ready
04010         Ready
00020         Ready
```

Do only syntactic validation before rendering.

Do not make an unnecessary network request simply to validate every ID.

Runtime lookup/download remains authoritative.

### Optional v1 convenience

Maintain a session-local recent pathway list.

Do not build a new KEGG pathway-name database in v1.

---

# 13. SBGN pathway selection

SBGN mode must leverage the existing bundled collection.

Provide:

### Source filter

Options dynamically derived from:

```python
SBGN_SOURCES
```

Include:

```text
All
Reactome
SMPDB
PANTHER
MetaCyc
MetaCrop
```

### Search box

Search using:

```python
list_sbgn_pathways(source=..., query=..., limit=...)
```

Search should work offline.

### Results table

Columns:

```text
Pathway ID
Source
Filename
```

Allow:

* single selection;
* multiselect;
* Add to render queue.

Default maximum visible search results:

```text
100
```

Do not load thousands of rows into the widget unnecessarily.

### Local SBGN

Also provide:

```text
Open local .sbgn file…
```

Local paths may be added to the same render queue as collection IDs.

Show local files clearly:

```text
Local    /home/user/pathway.sbgn
```

The GUI service must pass collection IDs or paths directly to `sbgnview()`.

---

# 14. Render queue

Both KEGG and SBGN should ultimately produce an ordered render queue.

Example:

```text
☑ 04110
☑ 04010
☑ 00020
```

Support:

* remove;
* clear all;
* move up/down;
* select all.

The user must be able to batch-render without reopening dialogs.

---

# 15. Appearance panel

Expose the common settings scientists are likely to use.

### Theme

Options:

```text
publication
slate
dark
```

Populate from the existing `THEMES` keys when practical.

### Output format

```text
PNG
PDF
SVG
```

### Title

Optional text field.

### Subtitle

Optional text field.

### Figure width

Floating point input.

Defaults:

KEGG:

```text
14.0
```

SBGN:

```text
15.0
```

### DPI

Integer control.

Default:

```text
220
```

Range:

```text
72–600
```

### Color key

```text
☑ Show color key
```

Maps to:

```python
plot_col_key
```

---

# 16. Gene color scale

Show only when gene data is enabled.

Fields:

```text
Palette
Limit
Bins
```

Populate palette choices dynamically from:

```python
list_palettes()
```

Show low/mid/high swatches beside every selected palette.

Default limit:

```text
1.0
```

Default bins:

```text
10
```

For KEGG advanced settings also provide:

```text
☑ Symmetric around zero
☐ Discrete values
```

Maps to:

```python
both_dirs
discrete
```

---

# 17. Metabolite color scale

Independent from the gene scale.

Never mirror one scale automatically onto the other.

Fields:

```text
Palette
Limit
Bins
```

The final `limit` argument for independent limits should be:

```python
{
    "gene": gene_limit,
    "cpd": cpd_limit,
}
```

The GUI must visibly reinforce that the scales are independent.

---

# 18. KEGG renderer settings

Show only in KEGG mode.

Render mode:

```text
Auto
Native
Vector
Graph
SVG
```

Maps exactly to:

```text
auto
native
vector
graph
svg
```

Default:

```text
auto
```

Include short tooltips:

Auto:

> Use native map when available, otherwise vector.

Native:

> Paint data over the KEGG map image.

Vector:

> Rebuild the pathway from KGML coordinates.

Graph:

> Network-style node-link rendering.

SVG:

> Standalone vector SVG renderer.

---

# 19. Advanced KEGG settings

Place these behind the Advanced tab/group.

### Node aggregation

Dropdown:

```text
sum
mean
median
max
min
max_abs
random
first
```

Default:

```text
sum
```

### Random seed

Visible/enabled only when:

```text
node_sum == random
```

### Structure

```text
☐ Split complexes into subunits
☐ Expand multi-gene nodes
```

Maps to:

```python
split_group
expand_node
```

### Labels

```text
☑ Map gene symbols
☑ Map compound names
```

Maps to:

```python
map_symbol
map_cpd_name
```

### Edges

```text
☑ Draw edges
☐ Include pathway-link edges
```

Maps to:

```python
draw_edges
show_link_edges
```

### Minimum positioned nodes

Integer input.

Default:

```text
3
```

Maps to:

```python
min_nnodes
```

---

# 20. Advanced SBGN settings

Show only in SBGN mode.

```text
☑ Show compartments
☑ Show process glyphs
☑ Draw edges
☑ Map compound names
☐ Re-download pathway file
```

Maps to:

```python
show_compartments
show_processes
draw_edges
map_cpd_name
overwrite
```

Also expose node aggregation and random seed.

Do not show KEGG-only controls such as:

* native mode;
* split group;
* expand node;
* link edges;
* min positioned nodes.

---

# 21. Storage settings

Add a Tools → Settings dialog.

Fields:

```text
KEGG files directory
SBGN files directory
Default output directory
```

Directory paths must use native folder choosers.

Persist using `QSettings`.

Suggested defaults:

* use the current Pathview+ cache area for downloaded material where possible;
* use user's last selected output directory for generated figures.

Do not default scientific output files into the Python installation directory.

---

# 22. Offline mode

Offline mode is an application-global state because the existing library uses a global offline switch.

Show it prominently in the main toolbar/status area:

```text
Offline ○
```

or:

```text
☐ Offline mode
```

When changed, call:

```python
set_offline(True/False)
```

Disable changing this setting while a render is running.

When offline:

* organism search still works;
* SBGN catalog search still works;
* cached KEGG/SBGN resources may work;
* uncached remote resources may fail.

Explain this behavior in a tooltip.

Do not incorrectly imply that all 5,206 SBGN files ship locally; only the catalog and crosswalk resources are bundled.

---

# 23. Cache management

Tools menu:

```text
Open Cache Folder
Clear HTTP Cache…
```

Use:

```python
cache_dir()
clear_cache()
```

Clear action requires confirmation:

```text
Delete all Pathview+ cached HTTP resources?
```

After completion:

```text
Removed N cached files.
```

Do not delete user-selected KEGG/SBGN/output directories when invoking `clear_cache()`.

---

# 24. Background execution

The Qt event loop must never perform a render or download synchronously.

Use one dedicated render worker thread or a `QThreadPool` constrained to:

```text
maxThreadCount = 1
```

Do not run multiple Pathview+ renders concurrently in v1.

Reasons:

* network/cache state is shared;
* offline state is global;
* Matplotlib-based rendering is safer serialized;
* output file handling becomes deterministic.

The render worker emits:

```text
started
pathway_started(index, total, pathway)
pathway_finished(result)
pathway_failed(pathway, exception)
progress(index, total)
finished
cancelled
```

---

# 25. Batch execution

Do not call the core's sequence/batch mode from the GUI worker.

Instead, iterate over selected pathways individually:

```python
for pathway in pathways:
    result = pathview(...)
```

or:

```python
for pathway in pathways:
    result = sbgnview(...)
```

This gives the GUI:

* progress updates;
* per-pathway status;
* cancellation between pathways;
* immediate result display;
* partial failure handling.

Continue batch processing after a normal `PathviewError`.

One bad pathway must not abort all other pathways.

---

# 26. Cancellation

A render currently inside the underlying library call cannot be safely interrupted.

Therefore the UI semantics must be:

```text
Cancel after current pathway
```

For a one-pathway run, Cancel may simply disable future operations and wait for the current operation to finish.

Do not terminate Python threads.

Do not kill a worker thread asynchronously.

---

# 27. Busy state

While rendering:

Disable controls that would invalidate the active configuration:

* mode;
* input files;
* pathway queue;
* offline toggle;
* Render button.

Enable:

```text
Cancel after current
```

Display:

```text
Rendering 2 of 7 — 04010
```

Use an indeterminate progress bar while a single pathway is actively rendering and an overall determinate batch progress indicator.

---

# 28. Render service configuration

Create dataclasses rather than passing widgets around.

Example:

```python
@dataclass
class DataConfig:
    path: Path | None
    id_type: str
    enabled: bool


@dataclass
class ColorScaleConfig:
    palette: str
    limit: float
    bins: int
    both_dirs: bool = True
    discrete: bool = False


@dataclass
class RenderConfig:
    mode: Literal["kegg", "sbgn"]
    pathways: list[str | Path]

    gene: DataConfig
    compound: DataConfig

    species: str = "hsa"

    output_dir: Path = Path(".")
    output_format: str = "png"

    theme: str = "publication"
    title: str | None = None
    subtitle: str | None = None
    figure_width: float = 14.0
    dpi: int = 220

    gene_scale: ColorScaleConfig | None = None
    compound_scale: ColorScaleConfig | None = None

    # source-specific options...
```

All validation occurs before starting the worker.

---

# 29. Render service

Implement one service API:

```python
class RenderService:
    def render_one(
        self,
        config: RenderConfig,
        pathway: str | Path,
    ) -> PathwayResult:
        ...
```

Internally route to either:

```python
pathview(...)
```

or:

```python
sbgnview(...)
```

No Qt objects belong in this service.

This makes the service unit-testable without showing a window.

---

# 30. Input parsing service

Do not depend on the private CLI `_read_table()` function from GUI code.

Move the core parsing semantics into a reusable module or create a shared function consumed by both CLI and GUI.

Preferred refactor:

```text
lib/input_io.py
```

with:

```python
@dataclass
class TableLoadResult:
    data: pl.DataFrame
    ignored_columns: list[str]
    id_column: str
    value_columns: list[str]


def read_molecular_table(path: str | Path) -> TableLoadResult:
    ...
```

Then update the CLI `_read_table()` to delegate to it.

Maintain existing CLI behavior and messages.

This prevents the GUI and CLI from gradually accepting different file formats.

---

# 31. Structured mapping diagnostics enhancement

The existing core stores useful human-readable mapping summaries in `PathwayResult.diagnostics`, but the GUI should also receive structured data.

Add a backward-compatible method to `NodeMapResult`:

```python
def to_dict(self) -> dict:
    return {
        "n_nodes": self.n_nodes,
        "n_nodes_with_data": self.n_nodes_with_data,
        "n_ids_input": self.n_ids_input,
        "n_ids_mapped": self.n_ids_mapped,
        "mapped_fraction": self.mapped_fraction,
        "unmapped_ids": list(self.unmapped_ids),
        "value_columns": list(self.value_columns),
    }
```

Preserve existing diagnostic keys:

```python
diagnostics["gene"] = gres.summary()
diagnostics["cpd"] = cres.summary()
```

Add:

```python
diagnostics["gene_detail"] = gres.to_dict()
diagnostics["cpd_detail"] = cres.to_dict()
```

Implement this in both:

* `pathview()`
* `sbgnview()`

This must be additive and nonbreaking.

---

# 32. Diagnostics panel

After each render show:

## General

KEGG:

```text
Species
Pathway
Nodes
Edges
Renderer
Output file
```

SBGN:

```text
Pathway
Glyphs
Arcs
Compartments
SBGN language
Source file
Output file
```

## Genes

Example:

```text
Input identifiers      1,942
Identifiers used         186
Pathway gene nodes       115
Nodes carrying data       71
Mapping rate            9.6%
Conditions                3
```

## Compounds

Same pattern.

### Unmapped identifiers

If structured diagnostics are available, provide an expandable table of unmapped IDs.

Buttons:

```text
Copy
Save as CSV
```

Do not make a low mapping rate look like application failure if rendering succeeded.

---

# 33. Errors

Map the existing exception hierarchy into understandable dialogs.

### SpeciesNotFoundError

Title:

```text
Species not found
```

Display suggestions if present.

### PathwayNotFoundError

Title:

```text
Pathway not found
```

Show pathway ID and core message.

### NetworkError

Title:

```text
Network resource unavailable
```

Include:

```text
Try again, enable offline mode if resources are already cached,
or download the pathway while connected.
```

### MappingError

Title:

```text
No molecular data mapped
```

Suggest checking:

* species;
* gene identifier type;
* compound identifier type;
* pathway compatibility.

### ParseError

```text
Could not parse pathway file
```

### RenderError

```text
Rendering failed
```

### Unexpected exceptions

Display:

```text
Unexpected application error
```

Provide:

```text
Copy technical details
```

Technical details may contain the traceback.

Do not dump tracebacks directly into the main UI.

---

# 34. Python warnings

Wrap rendering with:

```python
warnings.catch_warnings(record=True)
```

Collect warnings and add them to the run's Diagnostics/Log panel.

Warnings should not interrupt a successful render.

---

# 35. Results table

Bottom pane Results tab.

Columns:

```text
Pathway
Source
Status
Output
Mapping
```

Status values:

```text
Queued
Rendering
Succeeded
Failed
Cancelled
```

Mapping can show concise summary:

```text
Gene 71/115 • Compound 12/43
```

Clicking a successful row loads that result into the preview.

Double-clicking output opens the file.

Context menu:

```text
Open
Open containing folder
Copy output path
```

---

# 36. Preview architecture

Create a reusable `PreviewWidget`.

It must support:

* PNG/raster;
* SVG;
* PDF.

Use a stacked preview implementation.

PNG:

* `QGraphicsScene`
* `QGraphicsPixmapItem`
* `QGraphicsView`

SVG:

* `QGraphicsSvgItem` or `QSvgRenderer`

PDF:

* Qt PDF classes (`QPdfDocument` / appropriate Qt PDF view)

Required interactions:

```text
Zoom in
Zoom out
Fit
100%
```

Mouse behavior:

* wheel zoom;
* click-drag pan.

Fit should maintain aspect ratio.

Display a neutral placeholder before first render:

```text
Render a pathway to preview it here.
```

---

# 37. Preview fidelity

Preview the actual generated output file whenever possible.

Do not substitute `PathwayResult.image_array` as the final figure preview because the core intentionally stores the map raster in pathway coordinates rather than the fully composed figure.

The preview should therefore load:

```python
result.output_path
```

This preserves:

* titles;
* subtitles;
* color keys;
* figure padding;
* requested theme.

---

# 38. Export behavior

The normal Render action writes to the selected output directory using the core renderer.

No separate image-processing export pipeline should exist.

Provide:

```text
Open output
Open output folder
```

Optionally provide:

```text
Render again as…
```

which changes output format and reruns the same configuration.

Do not convert a generated PNG into an SVG or PDF and call that equivalent to native Pathview+ vector output.

---

# 39. Output directory

A visible output directory selector belongs near the Render button.

The path must exist or be creatable before the worker starts.

If invalid:

```text
Cannot write to output directory.
```

Remember last directory with `QSettings`.

---

# 40. Run log

Provide a Log tab.

Capture GUI-level events:

```text
14:04:21 Loaded rna.tsv (1,942 rows)
14:04:33 Selected species hsa — Homo sapiens
14:04:40 Rendering hsa04110
14:04:43 Completed hsa04110
14:04:43 Output: /results/hsa04110.pathview.png
```

Do not rely on intercepting stdout.

Call core functions with:

```python
quiet=True
```

and generate GUI-level log entries yourself.

---

# 41. Project/session files

Implement project persistence in v1.

Extension:

```text
.pvp.json
```

Menu:

```text
File
  New Project
  Open Project…
  Save Project
  Save Project As…
```

Store configuration only, not large molecular datasets.

Example schema:

```json
{
  "schema_version": 1,
  "mode": "kegg",
  "gene": {
    "enabled": true,
    "path": "/data/rna.tsv",
    "id_type": "SYMBOL"
  },
  "compound": {
    "enabled": false,
    "path": null,
    "id_type": "KEGG"
  },
  "species": "hsa",
  "pathways": ["04110", "04010"],
  "appearance": {
    "theme": "publication",
    "output_format": "png",
    "dpi": 220
  }
}
```

On project load:

* validate schema version;
* validate referenced files;
* mark missing files visibly;
* do not crash if a referenced data file moved.

---

# 42. Application settings

Use `QSettings` for machine/user preferences, not project scientific settings.

Store:

* window geometry;
* splitter sizes;
* last input directory;
* last output directory;
* last project directory;
* KEGG directory;
* SBGN directory;
* recent project files.

Do not use `QSettings` to silently override project render settings.

---

# 43. Menu structure

Recommended:

```text
File
  New Project
  Open Project…
  Save Project
  Save Project As…
  —
  Exit

View
  Fit Preview
  Zoom In
  Zoom Out
  100%
  —
  Show Results
  Show Diagnostics
  Show Log

Tools
  Settings…
  Open Cache Folder
  Clear HTTP Cache…
  —
  Offline Mode

Help
  Pathview+ Documentation
  GitHub Repository
  About Pathview+
```

Use `QDesktopServices.openUrl()` for documentation/repository links.

---

# 44. About dialog

Display:

```text
Pathview+ <version>
KEGG and SBGN pathway visualization

Python package version: ...
GUI: PySide6 / Qt ...
Cache directory: ...

License: CC BY-NC 4.0
```

Version must come from:

```python
pathview.__version__
```

Do not duplicate the package version as another constant.

---

# 45. Validation

Create centralized preflight validation.

A render may start only when:

* pathway queue is nonempty;
* output directory is writable;
* required enabled data files exist;
* at least one dataset is enabled OR map-only mode is checked;
* species resolves in KEGG mode;
* scale limits are valid positive finite numbers;
* DPI is valid;
* bins >= 1;
* random aggregation has a valid optional integer seed.

Show inline validation where possible.

Avoid modal dialogs for every trivial field error.

---

# 46. PathwayResult ownership

Keep successful `PathwayResult` instances in application state for the current run.

Suggested model:

```python
@dataclass
class RunResult:
    pathway: str
    source: str
    status: str
    result: PathwayResult | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
```

This allows diagnostics inspection without rereading output files.

---

# 47. Important behavior from the existing core

The implementation agent must preserve and design around these behaviors:

### KEGG

* species is resolved through the bundled organism table;
* pathway resources may be downloaded when missing;
* vector rendering can work from KGML without a KEGG PNG;
* `auto` picks native when a PNG exists, otherwise vector;
* native mode falls back to vector when necessary;
* gene and compound scales are independent;
* group splitting and node expansion modify pathway structure;
* batch failures should not discard successes.

### SBGN

* collection search is available offline;
* individual SBGN files are fetched on demand unless already local/cached;
* local `.sbgn` paths are valid inputs;
* gene-symbol mapping is generally the preferred SBGN default;
* compartment/process controls are SBGN-specific.

### Cache/offline

* offline state is process-global;
* stale cached HTTP resources may be usable;
* the bundled SBGN catalog is not the same as having every SBGN XML file locally.

---

# 48. Do not expose these in v1

Do not scope-creep into every public Pathview+ function.

Specifically leave these for later GUI versions unless trivial after everything else is complete:

* interactive graph node editing;
* drag/reposition pathway nodes;
* visual pathway editor;
* manual edge editing;
* arbitrary custom Python `trans_fun`;
* RData object browser;
* parity matrix UI;
* legend-only designer;
* identifier-conversion standalone UI;
* Reactome live name search;
* KEGG name search/database browser;
* interactive highlight/path annotation editor;
* plugin system;
* cloud execution;
* user accounts;
* collaboration;
* automatic updater.

The existing Python API for these features remains untouched.

---

# 49. Highlighting note

Do not implement post-hoc highlighting in v1.

Although the core exposes:

```python
highlight_nodes()
highlight_edges()
highlight_path()
change_labels()
```

the modification pipeline operates on the stored raster representation and has export semantics different from the composed vector/PDF figure.

A rushed GUI implementation would create confusing output inconsistencies.

Treat interactive annotations as a v1.1 feature requiring an explicit export design.

---

# 50. Performance requirements

The GUI should remain responsive with:

* 100,000-row expression tables;
* dozens of conditions;
* batch queues of at least 50 pathways.

Do not display entire molecular datasets by default.

Preview only first 50 rows.

Do not copy full Polars tables unnecessarily.

Do not perform organism or SBGN searches on every keystroke without debounce.

Do not render in the main thread.

---

# 51. Accessibility and desktop conventions

Use normal Qt widgets.

Requirements:

* every input has a label;
* tooltips for domain-specific settings;
* tab navigation works;
* keyboard shortcuts use normal OS conventions;
* no critical information conveyed only through color;
* errors use icon + text;
* successful/failed statuses use text in addition to any status color.

Avoid custom styling that breaks platform readability.

---

# 52. File drag-and-drop

Support dropping:

```text
.csv
.tsv
.tab
.txt
```

onto gene or metabolite path fields.

Support dropping:

```text
.sbgn
```

onto the SBGN pathway area.

Reject unsupported extensions with visible feedback.

---

# 53. Testing strategy

All existing project tests must remain green.

Add:

```text
tests/gui/
    test_input_service.py
    test_project_service.py
    test_render_service.py
    test_models.py
    test_main_window.py
    test_pathway_selector.py
    test_preview.py
    test_diagnostics.py
```

---

# 54. Unit tests — input

Test:

* CSV load;
* TSV load;
* identifier column remains string;
* numeric columns become Float64;
* stray text columns are ignored and reported;
* file with one column is rejected;
* file with no numeric value column is rejected;
* empty file is rejected cleanly.

Reuse semantics currently enforced by CLI tests.

---

# 55. Unit tests — species

Test:

```text
human -> hsa
mouse -> mmu
9606 -> hsa
Homo sapiens -> hsa
```

Test autocomplete results using bundled data only.

No network required.

---

# 56. Unit tests — SBGN browser

Test:

* catalog opens offline;
* source filtering;
* query filtering;
* row limit;
* multiselect queue;
* local file addition.

---

# 57. Unit tests — render service

Use existing offline fixtures such as:

```text
tests/fixtures/hsa00020.xml
tests/fixtures/hsa04010.xml
tests/fixtures/hsa04110.xml
tests/fixtures/hsa04110.png
tests/fixtures/P00001.namespaced.sbgn
```

Test a KEGG vector render completely offline.

Test a KEGG native render using fixture PNG.

Test a local SBGN render.

Verify:

* successful `PathwayResult`;
* output path exists;
* diagnostics populated.

---

# 58. Batch tests

Create a batch containing:

* one valid pathway;
* one invalid pathway;
* another valid pathway.

Verify:

* first succeeds;
* invalid entry is Failed;
* third still runs;
* successful output files remain available.

---

# 59. Worker tests

Verify:

* render does not execute on GUI thread;
* progress signals arrive;
* exceptions become failure signals;
* cancel-after-current prevents subsequent queue items;
* worker cleans up correctly.

---

# 60. Main-window smoke test

Using:

```text
QT_QPA_PLATFORM=offscreen
```

Test:

1. open app;
2. select KEGG mode;
3. choose human;
4. select fixture data;
5. queue pathway;
6. render;
7. wait for completion;
8. verify result row;
9. verify preview loaded;
10. verify diagnostics populated.

---

# 61. Diagnostics tests

After mapping, verify GUI presents:

* input ID count;
* mapped ID count;
* pathway node count;
* nodes carrying data;
* conditions;
* unmapped IDs when available.

Do not parse the human-readable summary string when structured detail exists.

---

# 62. Project-file tests

Verify:

* save/load round trip;
* schema version written;
* relative/absolute paths preserved intentionally;
* missing input file handled;
* invalid JSON produces understandable error;
* future unknown fields do not crash loader.

---

# 63. Core regression requirement

Before GUI work is considered complete:

```bash
pytest
```

must pass for the existing suite.

Then:

```bash
pytest tests/gui
```

must also pass.

GUI code must not change output defaults for users who never install or launch the GUI.

---

# 64. Packaging

Support wheel installation first.

Verify:

```bash
python -m build
pip install dist/pathview_plus-*.whl
pathview-plus info
pathview-plus-gui
```

both work.

Then provide a deployment configuration for:

```bash
pyside6-deploy
```

The configuration must include Pathview+ bundled data:

```text
lib/data/*.tsv.gz
```

and any GUI assets.

Standalone build smoke tests should verify that these still work after freezing:

* organism search;
* palette list;
* SBGN catalog search;
* offline fixture render.

---

# 65. Cross-platform target

v1 targets:

```text
Windows 10/11 x64
macOS supported by current Python/PySide6
Linux x86_64
```

Do not promise one binary built on one OS will run on another.

Build the application separately on each target platform.

---

# 66. Licensing/distribution

Do not alter the Pathview+ license.

Include existing project license/citation material in distributions.

Include required notices for bundled dependencies as appropriate.

Keep commercial/licensing implications of external pathway resources separate from GUI behavior.

The GUI should not attempt to bypass licensing restrictions of upstream databases.

---

# 67. CI

Extend CI with a GUI test job.

At minimum:

```text
Python 3.10
Python latest supported
Linux / offscreen Qt
```

Install:

```bash
pip install -e ".[gui-dev]"
```

Set:

```bash
QT_QPA_PLATFORM=offscreen
PATHVIEW_OFFLINE=1
```

Run:

```bash
pytest
```

Packaging can initially be a separate/manual workflow if signing credentials are unavailable.

---

# 68. Documentation

Add:

```text
docs/gui.md
```

Cover:

* installation;
* launching;
* KEGG workflow;
* SBGN workflow;
* gene input;
* metabolite input;
* combined input;
* batch rendering;
* offline mode;
* cache;
* output formats;
* common mapping errors.

Add a short README section:

```text
## Desktop GUI

pip install "pathview-plus[gui]"
pathview-plus-gui
```

Do not let GUI documentation replace existing Python API documentation.

---

# 69. First-run experience

On first launch:

* do not display a wizard;
* open directly to the main application;
* default to KEGG;
* species defaults to human;
* gene identifier type defaults to ENTREZ;
* compound identifier type defaults to KEGG;
* render mode defaults to Auto;
* output format defaults to PNG;
* theme defaults to publication;
* show a small empty-state explanation.

Example:

```text
1. Load gene and/or metabolite data.
2. Choose a pathway.
3. Render.
```

Provide a button:

```text
Load demo data
```

This may use:

```python
demo_gene_data()
demo_cpd_data()
```

and a known pathway such as `00020`.

Demo behavior must not require the user to manually create files.

---

# 70. Demo mode

The demo should configure:

```text
KEGG
Human
00020
Vector
PNG
```

with demo gene/metabolite data if those datasets map sensibly.

If the pathway resource is absent and offline mode prevents retrieval, explain the limitation rather than failing silently.

Do not automatically disable offline mode.

---

# 71. UX rule for advanced parameters

Every control exposed in the GUI must have one of:

* clear human-readable label;
* tooltip explaining the corresponding Pathview+ parameter.

Do not present Python parameter names like:

```text
map_null
plot_col_key
both_dirs
```

as the main user-facing labels.

Internally they may retain those names.

---

# 72. Source-aware settings synchronization

When switching KEGG ↔ SBGN:

Preserve:

* loaded data;
* output directory;
* theme;
* format;
* title;
* color settings where valid.

Change only source-specific defaultsettings.

Do not clear the user's datasets just because the source changed.

Maintain independent pathway queues for KEGG and SBGN so switching tabs does not destroy work.

---

# 73. Application state model

Use a central state/config object rather than treating widgets as state.

Example:

```python
@dataclass
class AppState:
    project_path: Path | None
    kegg_config: RenderConfig
    sbgn_config: RenderConfig
    current_mode: str
    current_results: list[RunResult]
    dirty: bool
```

Widgets update state.

Render worker receives a deep/copied immutable snapshot.

Changes made by the user after a run must not mutate the configuration recorded for the completed result.

---

# 74. Dirty project handling

When scientific configuration changes:

```text
dirty = True
```

On New/Open/Exit with unsaved changes:

```text
Save changes to this project?
Save / Don't Save / Cancel
```

Standard desktop behavior.

---

# 75. Logging configuration

Use Python's `logging` package for GUI internals.

Create logger:

```python
logging.getLogger("pathview.gui")
```

Do not globally reconfigure logging for library users.

GUI log messages may feed both:

* in-app log model;
* optional rotating file log.

If persistent logs are used, put them in a user-writable cache/config location.

---

# 76. Security/reliability rules

Treat all loaded files as untrusted input.

Do not:

* execute expressions from project files;
* use `eval`;
* dynamically import modules based on project-file content;
* execute shell commands from file names;
* interpolate file paths into shell commands.

All configuration files are JSON parsed as data.

Use Python/Qt filesystem APIs directly.

---

# 77. Definition of done

The GUI v1 is complete only when all of the following work from a clean installation.

### Installation

```bash
pip install "pathview-plus[gui]"
pathview-plus-gui
```

opens the desktop application.

### KEGG gene workflow

A user can:

1. load a gene CSV/TSV;
2. select identifier type;
3. select human;
4. enter `04110`;
5. render;
6. inspect mapping diagnostics;
7. zoom preview;
8. open generated output.

### Metabolite-only workflow

A user can:

1. load metabolite data;
2. leave gene input disabled;
3. select compound identifier type;
4. render a metabolic pathway successfully.

### Multi-omics workflow

Gene and metabolite data can be loaded simultaneously with independent color scales.

### SBGN workflow

A user can:

1. switch to SBGN;
2. search bundled catalog offline;
3. filter by source;
4. choose a pathway;
5. render it if its SBGN file is local/cached or network is available.

### Local SBGN workflow

A user can select a local `.sbgn` file and render it without collection lookup.

### Batch workflow

A user can queue multiple pathways and receive per-pathway success/failure results.

### Offline workflow

With:

```text
PATHVIEW_OFFLINE=1
```

or Offline Mode enabled:

* app launches;
* organism search works;
* SBGN collection search works;
* fixture/local pathways render;
* missing network resources generate understandable errors rather than hangs.

### Persistence

Project save/load restores configuration.

### Responsiveness

Window remains responsive while rendering.

### Regression

Existing Pathview+ CLI and Python API tests still pass.

---

# 78. Implementation order

Implement in this order.

## Phase 1 — foundations

1. Add optional PySide6 dependencies.
2. Create GUI package.
3. Create dataclass configuration/state models.
4. Refactor shared molecular-table input loader.
5. Add structured `NodeMapResult.to_dict`.
6. Add structured diagnostics to KEGG and SBGN results.
7. Tests for those core additions.

## Phase 2 — services

8. Input service.
9. Organism/pathway service.
10. Render service.
11. Project persistence service.
12. Service-level tests.

## Phase 3 — shell

13. `QApplication`.
14. Main window.
15. menus.
16. settings persistence.
17. splitter layout.
18. log/results/diagnostics tabs.

## Phase 4 — scientific workflow

19. Data panels.
20. species autocomplete.
21. KEGG pathway queue.
22. SBGN cabrowser.
23. appearance controls.
24. advanced source-specific controls.
25. validation.

## Phase 5 — execution

26. render worker;
27. serialized jobs;
28. progress;
29. cancellation;
30. error mapping;
31. warning collection.

## Phase 6 — output

32. PNG preview.
33. SVG preview.
34. PDF preview.
35. zoom/pan/fit.
36. result selection.
37. open file/folder.

## Phase 7 — persistence/polish

38. project save/load;
39. drag/drop;
40. recent projects;
41. demo data;
42. tooltips;
43. keyboard shortcu. about dialog.

## Phase 8 — release

45. GUI tests.
46. full existing test suite.
47. docs.
48. wheel test.
49. `pyside6-deploy` config.
50. standalone smoke test.

Do not begin custom visual polish until the complete scientific workflow works.

---

# 79. Coding standards

Match the existing project:

* type hints;
* Python 3.10 syntax;
* line length around existing Ruff configuration;
* no unnecessary abstractions;
* no hidden network requests from presentation widgets;
* no duplicated biological algothms;
* typed dataclasses for application state;
* docstrings on service APIs;
* deterministic tests;
* offline-first tests.

Run:

```bash
ruff check .
pytest
```

before declaring completion.

---

# 80. Final implementation directive

Implement the full v1 described above.

Make reasonable UI decisions where dimensions or minor visual details are unspecified.

Do not stop after creating scaffolding or a mock interface.

Do not replace real rendering with placeholders.

Do not defer KEGG, SBGN, batch processing, diagnostics, offline behavior, preview, tests, or project persistence.

When finished, provide:

1. summary of architecture;
2. complete list of changed files;
3. commands to install and run;
4. commands to run tests;
5. known limitations;
6. screenshots or a description of each major UI state;
7. packaging instructions;
8. confirmation that the pre-existing test suite passes.

