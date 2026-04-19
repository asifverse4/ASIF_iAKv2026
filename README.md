🧪 ASIF_iAKv2026 (Intelligent Automated Kluster-generator)

The Ultimate Research-Grade Supramolecular Workflow Orchestrator

ASIF_iAKv2026 is a highly robust, fully automated Python GUI application designed to streamline computational chemistry workflows for supramolecular complexes, host-guest systems, and isolated molecules.

By automating the generation of starting geometries and orchestrating an unbreakable xTB ➔ CREST ➔ ORCA pipeline, this software eliminates days of manual file manipulation, battles through Out-Of-Memory (OOM) crashes, and guarantees mathematically sound starting points for high-level Density Functional Theory (DFT) calculations.

✨ Key Features

🧬 Intelligent Chemistry & Queuing

Multi-Ratio Batch Queuing: Input multiple stoichiometric ratios (e.g., 1:1, 1:2, 1:4) and the software will seamlessly build, optimize, and organize each complex sequentially while you step away.

Single-Molecule Mode: Skip the clustering algorithms completely and run isolated molecules/anchors (Ratio 1:0) straight through the pipeline.

Dynamic Charge & Multiplicity: Natively supports ionic and radical systems directly from the GUI.

Automated Binding Energy ($\Delta G_{bind}$): Input your isolated monomer energies, and the software automatically calculates and exports the absolute binding affinities in kcal/mol.

🛡️ Battle-Tested Architecture (The "Self-Healing" Engine)

Running heavy computational chemistry on Windows/WSL is notoriously unstable. This software was engineered to be unbreakable:

4-Tier Self-Healing ORCA Runner: If ORCA crashes due to massive memory requirements or OpenMPI failures, the pipeline automatically intercepts the crash, downgrades the computational constraints (stripping Freq or dropping to Serial execution), and restarts the job seamlessly.

Pure Linux Sandbox: Teleports calculations into a hidden /tmp/ Linux sandbox to bypass Windows NTFS synchronization delays and "Space-in-Path" OpenMPI fatal errors.

Direct-to-Windows I/O Piping: Saves .out logs line-by-line in real-time, ensuring data survives even if the WSL shell is violently killed by the OS.

Embedded Coordinates: Translates .xyz outputs into raw coordinate strings embedded directly into the .inp ORCA file, completely obliterating "input.xyz not found" read errors.

📊 Modern & Interactive GUI

Responsive Split-Pane UI: Freely drag and resize the Workflow Setup menus and the Live Pipeline Terminal to fit your screen.

Trend Analysis & Graphing Tab: Automatically extracts cross-series energies and plots interactive graphs (e.g., CREST vs ORCA accuracy, Stoichiometric Energy Trends).

Hardware Scaling: Dynamically unlock 32+ cores and massive RAM limits for heavy workstation/server environments.

In-App 3D Previews: Hover over any generated .xyz file in the application to instantly view an interactive 3D model.

⚙️ Prerequisites & Dependencies

System Requirements

Windows 10/11 (with WSL / Ubuntu installed) OR native Linux.

Python 3.8+

OpenMPI (Required for parallel ORCA runs).

To install on WSL/Ubuntu, simply run: sudo apt update && sudo apt install openmpi-bin libopenmpi-dev -y

Computational Engines

The pipeline orchestrates three external engines:

xTB (Geometry Pre-Optimization)

CREST (Conformational Search)

ORCA 6+ (DFT Refinement)

(Note: xTB and CREST can be auto-downloaded by the app itself. ORCA must be downloaded manually from the ORCA Forum due to licensing).

🚀 Installation & Setup

Clone the Repository:

git clone [https://github.com/asifverse4/ASIF_iAKv2026.git](https://github.com/asifverse4/ASIF_iAKv2026.git)
cd ASIF_iAKv2026


Install Python Libraries:

pip install numpy matplotlib scipy


Launch the Application:

python iak_pipeline.py


(Note: Run the main python script present in your repository).

Sideload Engines: Upon first launch, click "Auto-Install Missing Dependencies" to let the app web-scrape and extract xTB and CREST automatically. For ORCA, download the Linux .tar.xz archive and use the "LOAD LOCAL ENGINE" button inside the app to seamlessly link it to the WSL bridge.

📖 How to Use

Select Molecules: Browse and select your Anchor (A) and Guest (B) .xyz files. Leave Guest (B) blank for single-molecule runs.

Define Ratios: Type in your desired stoichiometric ratios separated by commas (e.g., 1:1, 1:2, 1:4).

Configure Chemistry: Set Charge, Multiplicity, and your desired custom ORCA DFT Functional/Basis set (e.g., wB97X-D4 def2-TZVP CPCM(Water)).

Configure Hardware: Tell the software how powerful your machine is (e.g., 32 Cores, 4000 MB RAM/Core).

Run Batch Pipeline: Click START BATCH PIPELINE.

Evaluate: Once finished, navigate to the Trend Analysis & Graphs tab to instantly plot your results, or check the 05_Top_Models_Comparison folder for the isolated global minimums and CSV reports.

📝 Scientific Disclaimer

The structures reported by this workflow represent local minima found within the defined sampling depth, RMSD filtering bounds, and selected level of theory. While this pipeline forces 350-iteration rigorous convergence, it does not guarantee absolute global minima. Always manually review Transition States and near-degenerate ensembles using the provided output logs.

🧑‍💻 Author

Engineered and developed by Asif Raza. ( asifrazakne2005@gmail.com)

Project Inspiration and Guidance - Dr. Imran A. Khan ( imranakhan@jamiahamdard.ac.in)

Feel free to reach us if you have any issue, recommendations, or suggestions we will highly appreciate that.
 or  If you encounter any bugs or have feature requests, feel free to open an Issue.

 THANK YOU FOR USING THE APP--(LAAL DIL LAAL DIL)
