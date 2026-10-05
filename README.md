<div align="center">

<a href="https://github.com/asifverse4/ASIF_iAKv2026">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:020617,25:1e3a8a,50:2563eb,75:7c3aed,100:06b6d4&height=260&section=header&text=ASIF_iAKv2026&fontSize=62&fontColor=ffffff&fontAlignY=36&desc=Intelligent%20Automated%20Kluster-generator&descAlignY=61&descSize=21&animation=fadeIn" width="100%" alt="ASIF_iAKv2026 animated header" />
</a>

<a href="https://github.com/asifverse4/ASIF_iAKv2026">
  <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=18&duration=2800&pause=700&color=67E8F9&center=true&vCenter=true&width=900&lines=Research-grade+supramolecular+workflow+orchestration;Automated+xTB+%E2%86%92+CREST+%E2%86%92+ORCA+pipeline;Self-healing+computational+chemistry+automation;From+%24.xyz%24+structures+to+publication-ready+insights" alt="Animated tagline" />
</a>

<p>
  <img src="https://img.shields.io/badge/STATUS-ACTIVE-22c55e?style=for-the-badge&labelColor=0f172a" alt="Project status active" />
  <img src="https://img.shields.io/badge/RESEARCH-COMPUTATIONAL%20CHEMISTRY-06b6d4?style=for-the-badge&labelColor=0f172a" alt="Computational chemistry" />
  <img src="https://img.shields.io/badge/GUI-PYTHON-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python GUI" />
</p>

<p>
  <a href="https://github.com/asifverse4/ASIF_iAKv2026/stargazers"><img src="https://img.shields.io/github/stars/asifverse4/ASIF_iAKv2026?style=flat-square&logo=github&color=f59e0b" alt="GitHub stars" /></a>
  <a href="https://github.com/asifverse4/ASIF_iAKv2026/issues"><img src="https://img.shields.io/github/issues/asifverse4/ASIF_iAKv2026?style=flat-square&logo=github&color=ef4444" alt="GitHub issues" /></a>
  <a href="https://github.com/asifverse4/ASIF_iAKv2026/network/members"><img src="https://img.shields.io/github/forks/asifverse4/ASIF_iAKv2026?style=flat-square&logo=github&color=8b5cf6" alt="GitHub forks" /></a>
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.8+" />
</p>

<p><strong>A resilient desktop workflow orchestrator for supramolecular complexes, host–guest systems, and isolated molecules.</strong></p>

</div>

> [!IMPORTANT]
> ASIF_iAKv2026 automates computational workflows; it does not replace method validation, chemical interpretation, or experimental confirmation.

---

## 🌌 What is ASIF_iAKv2026?

ASIF_iAKv2026 transforms a demanding multi-stage computational chemistry workflow into a clear, observable, and recoverable pipeline. It helps researchers generate starting geometries, explore conformational space, refine promising structures, and compare energetic results without manually managing every intermediate file.

<div align="center">

```text
   MOLECULES          STRUCTURE SEARCH             REFINEMENT              INSIGHT
 ┌─────────────┐     ┌───────────────┐          ┌───────────────┐        ┌─────────────┐
 │ Anchor .xyz │ ──▶ │ xTB + CREST   │ ───────▶ │ ORCA 6+ / DFT │ ─────▶ │ CSV + Graphs│
 │ Guest  .xyz │     │ Conformers    │          │ Energy parser │        │ 3D Models   │
 └─────────────┘     └───────────────┘          └───────────────┘        └─────────────┘
```

</div>

## ⚡ Core Capabilities

<table>
<tr>
<td width="50%">

### 🧬 Intelligent Chemistry

- Multi-ratio queueing: `1:0`, `1:1`, `1:2`, `1:4`
- Single-molecule and host–guest modes
- Dynamic charge and multiplicity
- Custom functional, basis-set, and solvent settings
- Automated binding-energy bookkeeping

</td>
<td width="50%">

### 🛡️ Self-Healing Execution

- Four-tier ORCA recovery strategy
- Linux `/tmp/` sandbox for safer execution
- Live `.out` log streaming
- Embedded coordinates in ORCA inputs
- Hardware-aware CPU and memory controls

</td>
</tr>
<tr>
<td width="50%">

### 📊 Interactive Analysis

- Trend Analysis & Graphs tab
- CREST versus ORCA comparisons
- Stoichiometric energy trends
- CSV report generation
- Global-minimum model organization

</td>
<td width="50%">

### 🖥️ Modern Research GUI

- Responsive split-pane interface
- Live pipeline terminal
- In-app `.xyz` 3D previews
- Dependency detection and setup
- Designed for Windows/WSL and Linux

</td>
</tr>
</table>

## 🔬 Animated Workflow Map

```mermaid
%%{init: {'theme':'dark','themeVariables': {'primaryColor':'#172554','primaryTextColor':'#ffffff','primaryBorderColor':'#60a5fa','lineColor':'#22d3ee','secondaryColor':'#312e81','tertiaryColor':'#064e3b'}}}%%
flowchart LR
    A[🧪 Anchor .xyz] --> W[⚙️ Workflow Builder]
    G[🧪 Guest .xyz] --> W
    W --> Q[📋 Ratio Queue]
    Q --> X[⚡ xTB\nPre-optimization]
    X --> C[🔎 CREST\nConformer search]
    C --> O[🧠 ORCA 6+\nDFT refinement]
    O --> S{✅ Converged?}
    S -- No --> H[🛡️ Recovery engine]
    H --> O
    S -- Yes --> R[📦 Results parser]
    R --> E[📈 Energies & CSV]
    R --> P[🧊 3D previews & plots]
```

## 🧭 Pipeline Stages

| Stage | Engine | Purpose | Output |
|:---:|:---|:---|:---|
| `01` | **xTB** | Rapid geometry pre-optimization | Relaxed starting geometries |
| `02` | **CREST** | Conformational exploration and filtering | Candidate conformer ensemble |
| `03` | **ORCA 6+** | DFT refinement and energy evaluation | Refined structures and energies |
| `04` | **ASIF parser** | Cross-series analysis and organization | Reports, plots, and top models |

## 🧰 Technology Stack

<div align="center">

<img src="https://skillicons.dev/icons?i=python,linux,git,github&theme=dark" alt="Technology icons" />

<br /><br />

<img src="https://img.shields.io/badge/NumPy- numerical%20analysis-013243?style=for-the-badge&logo=numpy" alt="NumPy" />
<img src="https://img.shields.io/badge/SciPy-scientific%20computing-0C55A5?style=for-the-badge&logo=scipy" alt="SciPy" />
<img src="https://img.shields.io/badge/Matplotlib-visualization-11557C?style=for-the-badge&logo=matplotlib" alt="Matplotlib" />
<img src="https://img.shields.io/badge/OpenMPI-parallel%20execution-3B82F6?style=for-the-badge" alt="OpenMPI" />

</div>

## ⚙️ Requirements

- Windows 10/11 with WSL + Ubuntu, **or** native Linux
- Python **3.8+**
- OpenMPI for parallel ORCA runs
- xTB, CREST, and ORCA 6+
- Sufficient disk space for conformer ensembles and ORCA scratch files

Install OpenMPI on Ubuntu/WSL:

```bash
sudo apt update
sudo apt install openmpi-bin libopenmpi-dev -y
```

> xTB and CREST can be installed through the application. ORCA must be obtained separately from the official ORCA Forum in accordance with its license.

## 🚀 Installation

```bash
git clone https://github.com/asifverse4/ASIF_iAKv2026.git
cd ASIF_iAKv2026

python -m pip install --upgrade pip
pip install numpy matplotlib scipy
python iak_pipeline.py
```

On first launch, select **Auto-Install Missing Dependencies** for xTB and CREST. Configure the ORCA installation path when prompted.

## 🎛️ Quick Start

<details open>
<summary><strong>Run your first workflow</strong></summary>

<br />

1. **Select molecules** — choose an Anchor (A) `.xyz` file and optionally a Guest (B) `.xyz` file.
2. **Define ratios** — enter values such as `1:1, 1:2, 1:4`.
3. **Configure chemistry** — set charge, multiplicity, functional, basis set, and solvent model.
4. **Configure hardware** — provide the available cores and memory per core.
5. **Start the pipeline** — click **START BATCH PIPELINE**.
6. **Evaluate results** — inspect the live terminal, top models, CSV reports, and trend plots.

Example configuration:

```text
wB97X-D4 def2-TZVP CPCM(Water)
```

</details>

## 📁 Expected Results

```text
05_Top_Models_Comparison/
├── global_minimum_structures/
├── energy_comparison.csv
├── binding_energies.csv
├── trend_plots/
└── pipeline_logs/
```

## 📈 Research Workflow Dashboard

<div align="center">

```text
╭──────────────────────────────────────────────────────────────╮
│  ASIF_iAKv2026  •  WORKFLOW STATUS                          │
├──────────────────────────────────────────────────────────────┤
│  ● Inputs validated       ● Ratio queue prepared             │
│  ● xTB geometry relaxed   ● CREST ensemble generated         │
│  ◌ ORCA refinement        ◌ Binding energies pending         │
│  ◌ Trend plots            ◌ Top models exported              │
╰──────────────────────────────────────────────────────────────╯
```

</div>

## 🧪 Scientific Scope & Reproducibility

The structures reported by this workflow are local minima found within the selected sampling depth, RMSD filtering bounds, charge/multiplicity, and level of theory.

For defensible research conclusions:

- Validate representative structures using an appropriate higher-level method.
- Record software versions, computational settings, and hardware limits.
- Inspect suspicious geometries and convergence behavior manually.
- Treat binding energies as method-dependent quantities.
- Repeat sampling with additional seeds when the energy landscape is complex.

## 🗺️ Roadmap

- [x] Multi-ratio batch workflow
- [x] xTB → CREST → ORCA orchestration
- [x] Charge and multiplicity controls
- [x] Live output and recovery logic
- [x] Energy extraction and trend visualization
- [ ] Reproducible run manifests
- [ ] Automated benchmark datasets
- [ ] Expanded method and solvent presets
- [ ] Publication-ready report export

## 🤝 Contributing

Issues, suggestions, and feature requests are welcome.

1. Open an issue with a clear description.
2. Include your operating system, Python version, and engine versions.
3. Attach relevant logs or a minimal `.xyz` example when possible.
4. Keep pull requests focused and document changes to workflow behavior.

## 📬 Contact

- **Developer:** Asif Raza — `asifrazakne2005@gmail.com`
- **Project inspiration and guidance:** Dr. Imran A. Khan — `imranakhan@jamiahamdard.ac.in`
- **Issues:** [Open a GitHub Issue](https://github.com/asifverse4/ASIF_iAKv2026/issues)

## 📄 License

No license file is currently declared in the repository. Add a license before redistributing the project or incorporating it into another product.

<div align="center">

<a href="https://github.com/asifverse4/ASIF_iAKv2026">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:06b6d4,25:7c3aed,50:2563eb,75:1e3a8a,100:020617&height=150&section=footer&animation=twinkling" width="100%" alt="Animated footer" />
</a>

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=16&pause=1200&color=67E8F9&center=true&vCenter=true&width=620&lines=Built+with+%E2%9D%A4%EF%B8%8F+for+computational+chemistry;Automate.+Explore.+Refine.+Understand." alt="Animated footer message" />

<br />

<strong>ASIFVERSE4 · Turning complex workflows into reproducible science.</strong>

</div>
