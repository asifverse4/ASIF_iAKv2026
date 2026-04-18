🧪 IAK: Intelligent Automated Kluster-generator v4.1.20

The Ultimate Research-Grade Supramolecular Workflow Orchestrator

IAK is a highly robust, fully automated Python GUI application designed to streamline computational chemistry workflows for supramolecular complexes (e.g., host-guest systems, co-crystals).

By automating the generation of starting geometries and orchestrating an unbreakable xTB ➔ CREST ➔ ORCA pipeline, IAK eliminates days of manual file manipulation and guarantees mathematically sound starting points for high-level Density Functional Theory (DFT) calculations.

✨ Key Features

🧬 Intelligent Chemistry Logic

Smart Docking: Uses hydrogen-bond donor/acceptor geometric heuristics to place multiple guest molecules around an anchor (e.g., 1:2, 1:4 ratios) rather than relying on random scattering.

Steric & RMSD Screening: Automatically penalizes steric clashes and utilizes Kabsch RMSD clustering to drop duplicate geometries before wasting CPU time.

Thermodynamic Ranking: Parses final ORCA outputs to rank structures by Gibbs Free Energy (ΔG), detects near-degenerate ensembles, and validates true minima by parsing imaginary frequencies.

🛡️ Battle-Tested Architecture (The "Self-Healing" Engine)

Running heavy computational chemistry on Windows/WSL is notoriously unstable. IAK was engineered to be unbreakable:

4-Tier Self-Healing ORCA Runner: If ORCA crashes due to Out-Of-Memory (OOM) kills or OpenMPI failures on massive clusters, IAK automatically catches the crash, downgrades the computational constraints (stripping Freq or dropping to Serial execution), and restarts the job seamlessly.

Pure Linux Sandbox: IAK teleports calculations into a hidden /tmp/ Linux sandbox to bypass Windows NTFS synchronization delays and "Space-in-Path" OpenMPI fatal errors.

Embedded Coordinates: Translates .xyz outputs into raw coordinate strings embedded directly into the .inp ORCA file, obliterating "File Not Found" read errors forever.

Sub-Shell Escape: Dynamically wraps mpirun to bypass ORCA 6's aggressive environment/path scrubbing.

🖥️ Modern & Interactive GUI

Hardware Scaling: Dynamically unlock 32+ cores and massive RAM limits straight from the GUI for heavy workstation/server environments.

In-App Results Browser: View your raw clusters, xTB, CREST, and ORCA results in a beautifully tabbed 5-panel interface.

Instant 3D Preview: Hover over any generated .xyz file in the application to instantly view an interactive 3D model of the molecule.

One-Click Avogadro: Route any file directly into Avogadro for deep inspection with a single click.

⚙️ Prerequisites & Dependencies

System Requirements

Windows 10/11 (with WSL / Ubuntu installed) OR native Linux.

Python 3.8+

OpenMPI (Required for parallel ORCA runs).

To install on WSL/Ubuntu, simply run: sudo apt update && sudo apt install openmpi-bin libopenmpi-dev -y

Computational Engines

IAK relies on three external engines.

xTB (Geometry Pre-Optimization)

CREST (Conformational Search)

ORCA 6+ (DFT Refinement)

(Note: xTB and CREST can be auto-downloaded by the IAK app itself. ORCA must be downloaded manually from the ORCA Forum due to licensing).

🚀 Installation & Setup

Clone the Repository:




Install Python Libraries:

pip install numpy matplotlib scipy


Launch the Application:

python iak_pipeline.py


Sideload Engines: Upon first launch, click "Auto-Install Missing Dependencies" to let the app web-scrape and extract xTB and CREST automatically. For ORCA, download the Linux .tar.xz archive from their forum and use the "LOAD LOCAL ENGINE" button inside IAK to seamlessly link it.

📖 How to Use

Select Molecules: Browse and select your Anchor (e.g., Citric Acid) and Guest (e.g., Urea) .xyz files.

Define Ratio: Set the stoichiometric ratio (e.g., 1:4).

Configure Hardware: Tell IAK how powerful your machine is (e.g., 32 Cores, 4000 MB RAM/Core).

Run Pipeline: Click START RESEARCH PIPELINE.

Relax: IAK will isolate jobs, generate conformers, optimize in xTB, explore in CREST, refine in ORCA, extract the lowest energy structures, and output a Thesis-ready Markdown report and CSV comparison.

Evaluate: Go to the Generated Results tab and look inside 05_Top_Models_Comparison for your global minimum.

(IAK is perfectly resumable! If your power goes out, simply run the script again and it will pick up exactly where it left off).

📝 Scientific Disclaimer

The structures reported by this workflow represent local minima found within the defined sampling depth, RMSD filtering bounds, and selected level of theory. While this pipeline is highly rigorous, it does not guarantee absolute global minima. Always manually review Transition States and near-degenerate ensembles using the provided output logs.

🧑‍💻 Author

Engineered and developed by Asif Raza.

Thank you for using this app! If you encounter any bugs, feel free to open an Issue.

For further queries, you may contact:

Asif Raza — asifrazakne2005@gmail.com

Dr. Imran A. Khan — imranakhan@jamiahamdard.ac.in  ~Project inspiration and guidance

License

This project is licensed under the MIT License - see the LICENSE file for details.
