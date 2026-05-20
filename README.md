# Progressive Compression and Decoding of 3D Models

> Project completed at **ENSEEIHT** (2SN MM) in 2023 in pair
> Course: *Modélisation, Compression, Streaming, Interactions 3D*  
> Language: **Python 3**  
> Team: *2*

Implementation of progressive mesh compression for lossless streaming, based on the paper:

> *Progressive Compression for Lossless Transmission of Triangle Meshes* — Alliez & Desbrun, SIGGRAPH 2001 ([`docs/AlliezDesbrun01.pdf`](docs/4.AlliezDesbrun01.pdf))

---

## How it works

The pipeline takes a manifold `.obj` mesh and produces an `.obja` file that encodes the full reconstruction sequence — from a minimal low-resolution base mesh back to the original geometry, step by step.

```
models/*.obj  ──►  Decimation  ──►  base mesh  +  patch sequence
                                          │
                                          ▼
                                  Reconstruction  ──►  output/*.obja
```

**Decimation** (`valence_driven_decimater.py`) iteratively removes vertices using a valence-driven strategy: at each step it selects a gate (half-edge), removes the opposite vertex, and re-triangulates the resulting hole. The sequence of removed vertices and patches is recorded.

**Reconstruction** (`reconstruction.py`) replays those operations in reverse — starting from the base mesh and progressively re-inserting each vertex — and writes the result as an animated `.obja` file.

The output `.obja` can then be decoded/streamed and visualized progressively in the browser using the viewer (`viewer/`). 
Demo videos of the reconstruction in action are available in [`docs/video_result/`](docs/video_result/).

---

## Repository structure

```
├── decimate_and_recreate.py    # Main CLI entry point
├── valence_driven_decimater.py # Decimation algorithm
├── reconstruction.py           # Progressive reconstruction
├── obja.py                     # Mesh I/O and model primitives
├── utility.py                  # Shared helpers
├── color_generator.py          # Patch coloring for visualization
├── script.py                   # Batch processing of all models
│
├── models/                     # Input .obj meshes
│   ├── bunny_bis.obj           # (_bis = manually made watertight)
│   ├── cow.obj
│   ├── fandisk.obj
│   └── ...
│
├── output/                     # Pre-generated .obja reconstruction files
│   ├── bunny_bis_reset_color.obja
│   ├── cow_reset_color.obja
│   └── ...
│
├── viewer/                     # Browser-based .obja viewer (from tforgione/obja)
│   ├── server.py               # Local HTTP server with Range request support
│   ├── index.html              # Three.js viewer
│   ├── js/
│   └── src/
│
├── docs/                       # Reference material
│   ├── 4.AlliezDesbrun01.pdf   # Reference paper
│   ├── ProjetCSI2023.pdf       # Project brief
│   └── video_result/           # Demo videos of the reconstruction
│       ├── 4_reconstructions.mp4
│       └── Icosphere.mp4
│
└── .gitignore
```

---

## Installation

Python 3.8+ required. Install dependencies:

```bash
pip install numpy
```

Or with conda:

```bash
conda create -n 3d-compression python=3.10
conda activate 3d-compression
pip install numpy
```

---

## Usage

### Compress and reconstruct a model

```bash
python decimate_and_recreate.py -input models/bunny_bis.obj -outputRecreate output/bunny_bis_reset_color.obja
```

#### All options

| Argument | Default | Description |
|----------|---------|-------------|
| `-input` | *(required)* | Path to the input `.obj` model |
| `-outputRecreate` | `Output_Recreate.obja` | Path for the `.obja` reconstruction output |
| `-outputDecimate` | `None` | Path to save the low-res base mesh (omit to skip) |
| `-it` | `1000` | Maximum number of decimation iterations |
| `-minPts` | `4` | Minimum number of vertices in the base mesh |
| `-minProp` | `None` | Minimum vertex proportion relative to original (e.g. `0.1` = 10%) |
| `-colorintRecreating` | `True` | Color each patch during reconstruction |
| `-resetColor` | `True` | Reset patch colors at each step (shows patch evolution clearly) |

#### Example — decimate to 10% of original vertices

```bash
python decimate_and_recreate.py \
  -input models/cow.obj \
  -outputRecreate output/cow_reset_color.obja \
  -outputDecimate output/decimated/cow_base.obj \
  -minProp 0.1
```

## Visualization

Pre-generated results are available in `output/` and can be visualized immediately without running the pipeline.

**1. Start the viewer server** from the project root:

```bash
python viewer/server.py
```

**2. Open the viewer** — the `.obja` path is passed as a query string after `?`:

```
# Default (loads output/icosphere_reset_color.obja)
http://localhost:8000/viewer/

# Load a specific file
http://localhost:8000/viewer/?output/bunny_bis_reset_color.obja
http://localhost:8000/viewer/?output/cow_reset_color.obja
http://localhost:8000/viewer/?output/fandisk_reset_color.obja
```

Use the mouse to **rotate**, scroll to **zoom**. The progress bar at the bottom shows the loading percentage.

> The `_reset_color` variants color each patch differently to show the reconstruction steps. The `_pure` variants are colorless.

---

## Known limitations

- **Valence 1 or 2 vertices:** the algorithm requires all vertices to have valence ≥ 3. Models with lower valences must be repaired beforehand. Files with `_bis` suffix were manually made watertight.
- **Performance:** the Python implementation is not optimized for speed. Large meshes can be slow.
- **Code quality:** this is an academic prototype, not production-ready code. The implementation retains several rough edges: intermediate files are written to disk on every decimation iteration (useful for debugging but wasteful in normal use) and comments/variable names mix French and English. It works correctly for its intended purpose but has not been cleaned up beyond that.

---

## Credits

- Viewer (`viewer/`), `server.py`, and `obja.py` are based on [tforgione/obja](https://gitea.tforgione.fr/tforgione/obja).
- Reference paper: Alliez, P. & Desbrun, M. (2001). *Progressive Compression for Lossless Transmission of Triangle Meshes.* SIGGRAPH 2001.
