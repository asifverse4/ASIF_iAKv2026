#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IAK - Intelligent Automated Kluster-generator Pipeline v4.1.20
==============================================================
The Ultimate Research-Grade Supramolecular Workflow Orchestrator

Integrated Features:
- Professional Startup Sequence (Capabilities Workflow & Usage Guidelines Popups).
- Clickable Hyperlinks (Direct web routing for xTB, CREST, and ORCA downloads).
- Hardware Scaling GUI (Dynamically unlock 32+ cores and massive RAM for Workstations).
- 4-Tier Self-Healing ORCA Engine (Dynamically strips Freq & MPI constraints to fight through memory/OOM crashes).
- Direct-to-Windows I/O Piping (Saves .out logs line-by-line to survive total WSL shell kills).
- Embedded XYZ Coordinates (Bypasses all ORCA "input.xyz not found" file-read crashes).
- Fork-Bomb Prevention (Fixes infinite loop memory crashes in mpirun wrapper).
- HWLOC Policy Unbinding (Prevents WSL OpenMPI core-locking crashes).
- Memory Stabilizers (Limits %maxcore to prevent WSL Out-of-Memory kills).
- Forced Convergence Boosters (Injects MaxIter 350 to prevent large-cluster optimization failures).
- Pure Linux Sandbox Architecture (Bypasses all OpenMPI "space-in-path" execution crashes).
- ORCA Crash Diagnostic Logger (Dumps exact .out crash traces to GUI).
- Deep Binary Permission Enforcer (chmod +x orca* for all MPI sub-modules).
- Absolute Path Forcer (Permanently fixes relative path WSL crashes).
- Universal UTF-8 Encoding (Fixes 'charmap' UnicodeEncodeError crashes).
- Advanced Post-CREST Logic (Conformer pooling, RMSD deduplication).
- Gibbs Free Energy (ΔG) Ranking & Near-Degeneracy Analysis.
- Top 3 Models Extraction (Isolates 1 xTB, 1 CREST, 1 ORCA best file).
"""

import argparse
import dataclasses
import json
import logging
import math
import os
import queue
import random
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import threading
import time
import urllib.request
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Graceful Thread-Safe Matplotlib Import
try:
    import matplotlib
    matplotlib.use('Agg') # Force non-GUI backend
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

EH2KCAL = 627.509  # Hartree to kcal/mol conversion factor

# =============================================================================
# 0. GUI COLOR CONFIGURATION
# =============================================================================
_C = {
    "bg": "#0d1117", "panel": "#161b22", "border": "#30363d", "text": "#e6edf3",
    "muted": "#8b949e", "dim": "#484f58", "accent": "#388bfd", "green": "#3fb950",
    "yellow": "#d29922", "red": "#f85149", "entry": "#21262d", "run": "#238636",
    "stop": "#b62324", "hdr_bg": "#010409", "tab_act": "#0d1117", "tab_bg": "#161b22",
}

# =============================================================================
# 1. LOGGING INFRASTRUCTURE
# =============================================================================
class _QueueHandler(logging.Handler):
    def __init__(self, q: queue.Queue):
        super().__init__()
        self._q = q
    def emit(self, record: logging.LogRecord):
        self._q.put(self.format(record))

class SafeStreamHandler(logging.StreamHandler):
    """Safely handles unicode characters in environments with restricted charmaps."""
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            msg = self.format(record)
            safe_msg = msg.encode(sys.stdout.encoding or 'ascii', 'replace').decode(sys.stdout.encoding or 'ascii')
            try:
                self.stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                pass
        except Exception:
            self.handleError(record)

def setup_logging(verbose: bool = False, gui_queue: Optional[queue.Queue] = None):
    level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger("IAK")
    logger.setLevel(level)
    logger.handlers.clear()
    ch = SafeStreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s | %(levelname)-7s | %(message)s', datefmt='%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if gui_queue is not None:
        qh = _QueueHandler(gui_queue)
        qh.setFormatter(formatter)
        logger.addHandler(qh)
    return logger

# =============================================================================
# 2. EMBEDDED ENGINE MANAGER & WSL BRIDGE
# =============================================================================
ENGINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "iak_engine")

XTB_DIR = None
CREST_DIR = None
ORCA_DIR = None
ORCA_IS_WINDOWS = False
_WSL_ORCA_EXISTS = None

def is_tool_available(tool_name):
    global _WSL_ORCA_EXISTS
    if tool_name == "xtb": return XTB_DIR is not None or shutil.which("xtb") is not None
    if tool_name == "crest": return CREST_DIR is not None or shutil.which("crest") is not None
    if tool_name == "orca": 
        if ORCA_DIR is not None or shutil.which("orca") is not None or shutil.which("orca.exe") is not None:
            return True
        if sys.platform == "win32":
            if _WSL_ORCA_EXISTS is None:
                try:
                    proc = subprocess.run("wsl -e bash -c 'export PATH=\"/usr/bin:/bin:/usr/local/bin:$PATH\"; which orca'", shell=True, capture_output=True, timeout=3)
                    _WSL_ORCA_EXISTS = (proc.returncode == 0)
                except subprocess.TimeoutExpired:
                    _WSL_ORCA_EXISTS = False
                except Exception:
                    _WSL_ORCA_EXISTS = False
            return _WSL_ORCA_EXISTS
        return False
    return False

def get_wsl_path(win_path):
    drive, tail = os.path.splitdrive(win_path)
    if drive: return f"/mnt/{drive[0].lower()}{tail.replace(os.sep, '/')}"
    return win_path.replace(os.sep, '/')

def inject_embedded_engines():
    global XTB_DIR, CREST_DIR, ORCA_DIR, ORCA_IS_WINDOWS
    if os.path.exists(ENGINE_DIR):
        for root, dirs, files in os.walk(ENGINE_DIR):
            try:
                if "xtb" in files and os.path.basename(root) == "bin": 
                    if os.path.isfile(os.path.join(root, "xtb")):
                        XTB_DIR = root
                        if sys.platform == "win32":
                            subprocess.run(f"wsl chmod +x \"{get_wsl_path(os.path.join(root, 'xtb'))}\"", shell=True, capture_output=True)
                
                if "crest" in files and CREST_DIR is None: 
                    if os.path.isfile(os.path.join(root, "crest")):
                        CREST_DIR = root
                        if sys.platform == "win32":
                            subprocess.run(f"wsl chmod +x \"{get_wsl_path(os.path.join(root, 'crest'))}\"", shell=True, capture_output=True)
                
                if ORCA_DIR is None:
                    if "orca.exe" in files and os.path.isfile(os.path.join(root, "orca.exe")):
                        ORCA_DIR = root
                        ORCA_IS_WINDOWS = True
                    elif "orca" in files and os.path.isfile(os.path.join(root, "orca")):
                        ORCA_DIR = root
                        ORCA_IS_WINDOWS = False
                        if sys.platform == "win32":
                            subprocess.run(f"wsl chmod +x \"{get_wsl_path(os.path.join(root, 'orca'))}\"", shell=True, capture_output=True)
                            subprocess.run(f"wsl chmod +x \"{get_wsl_path(root)}/orca_\"* 2>/dev/null", shell=True, capture_output=True)
            except OSError:
                continue

inject_embedded_engines()

# =============================================================================
# 3. CONFIGURATION & CORE DATA STRUCTURES
# =============================================================================
class RunMode(Enum):
    FAST = "fast"
    BALANCED = "balanced"
    THOROUGH = "thorough"

@dataclasses.dataclass
class Config:
    n_generate: int = 200
    n_keep_scored: int = 50
    n_keep_clustered: int = 40
    n_run_xtb: int = 20
    n_run_crest: int = 5
    
    rmsd_cutoff: float = 0.5
    clash_cutoff: float = 1.2
    
    xtb_method: str = "--gfn2"
    crest_method: str = "--gfn2"
    orca_method: str = "B97-3c Opt Freq" 
    
    xtb_ewin_kcal: float = 5.0    
    crest_ewin_kcal: float = 3.0  
    
    random_seed: int = 42
    max_placement_attempts: int = 50
    preopt_inputs: bool = True

    cores: int = 4
    maxcore: int = 2000

    @classmethod
    def from_mode(cls, mode: RunMode):
        if mode == RunMode.FAST:
            return cls(n_generate=50, n_keep_scored=20, n_keep_clustered=10, n_run_xtb=5, n_run_crest=1)
        if mode == RunMode.THOROUGH:
            return cls(n_generate=1000, n_keep_scored=300, n_keep_clustered=100, n_run_xtb=50, n_run_crest=10, xtb_ewin_kcal=10.0, crest_ewin_kcal=5.0)
        return cls()

class Atom:
    __slots__ = ("symbol", "x", "y", "z")
    def __init__(self, s, x, y, z): self.symbol, self.x, self.y, self.z = s, x, y, z
    @property
    def coords(self): return np.array([self.x, self.y, self.z], dtype=float)
    @coords.setter
    def coords(self, v): self.x, self.y, self.z = float(v[0]), float(v[1]), float(v[2])

class Molecule:
    def __init__(self, atoms: List[Atom], name: str = "mol"):
        self.atoms = atoms
        self.name = name
        self.score = 0.0
        self.energy_eh = 0.0
        self.gibbs_eh = 0.0
        self.imag_freqs = 0
        self.lineage = []

    @classmethod
    def from_xyz(cls, path: str):
        with open(path, 'r', encoding='utf-8', errors='replace') as f: 
            lines = [l.strip() for l in f.readlines() if l.strip()]
            
        try: n = int(lines[0])
        except (ValueError, IndexError): raise ValueError(f"Invalid XYZ format in {path}")
            
        atoms = []
        for line in lines[2:2+n]:
            p = line.split()
            if len(p) >= 4:
                try: atoms.append(Atom(p[0], float(p[1]), float(p[2]), float(p[3])))
                except ValueError: continue
        return cls(atoms, lines[1] if len(lines)>1 else "mol")

    def to_xyz(self, path, comment=""):
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(f"{len(self.atoms)}\n{comment}\n")
            for a in self.atoms: f.write(f"{a.symbol:<4} {a.x:15.6f} {a.y:15.6f} {a.z:15.6f}\n")

    def coords_array(self): return np.array([a.coords for a in self.atoms])
    def centroid(self): return np.mean(self.coords_array(), axis=0)
    def translate(self, v): 
        for a in self.atoms: a.coords += v
    def rotate(self, R):
        for a in self.atoms: a.coords = R @ a.coords
    def merge(self, other): self.atoms.extend([Atom(a.symbol, a.x, a.y, a.z) for a in other.atoms])
    def n_atoms(self): return len(self.atoms)

def read_multi_xyz(path: str) -> List[Molecule]:
    mols = []
    if not os.path.exists(path): return mols
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        while True:
            line = f.readline()
            if not line: break
            line = line.strip()
            if not line: continue
            try: n = int(line)
            except ValueError: continue
            comment = f.readline().strip()
            atoms = []
            for _ in range(n):
                p = f.readline().split()
                if len(p) >= 4: atoms.append(Atom(p[0], float(p[1]), float(p[2]), float(p[3])))
            m = Molecule(atoms, name=comment)
            try: m.energy_eh = float(comment.split()[0])
            except: pass
            mols.append(m)
    return mols

# =============================================================================
# 4. CHEMISTRY LOGIC & PLACEMENT
# =============================================================================
def find_hbond_acceptors(mol): return [i for i, a in enumerate(mol.atoms) if a.symbol in ["O", "N", "F"]]
def find_hbond_donors(mol):
    donors = []
    heavy = {i: a for i, a in enumerate(mol.atoms) if a.symbol in ["N", "O", "S", "F"]}
    for i, a in enumerate(mol.atoms):
        if a.symbol == "H":
            for hj, ha in heavy.items():
                if np.linalg.norm(a.coords - ha.coords) < 1.2:
                    donors.append((i, hj))
                    break
    return donors

def kabsch_rmsd(c1, c2):
    c1_c, c2_c = c1 - np.mean(c1, axis=0), c2 - np.mean(c2, axis=0)
    H = c1_c.T @ c2_c
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return float(np.sqrt(np.mean(np.sum((c1_c - c2_c @ R.T)**2, axis=1))))

def score_geometry(mol):
    score = 0.0
    c = mol.coords_array()
    acc = find_hbond_acceptors(mol)
    don = [d[0] for d in find_hbond_donors(mol)]
    for d_idx in don:
        for a_idx in acc:
            dist = np.linalg.norm(c[d_idx] - c[a_idx])
            if 1.6 < dist < 2.3: score += 5.0 * np.exp(-0.5 * ((dist - 1.9) / 0.2)**2)
            elif dist < 1.3: score -= 25.0
    score -= np.max(np.linalg.norm(c - mol.centroid(), axis=1)) * 0.5
    mol.score = score
    return score

def _align_vectors(v_from, v_to):
    v_from, v_to = v_from / (np.linalg.norm(v_from) + 1e-12), v_to / (np.linalg.norm(v_to) + 1e-12)
    cross, dot = np.cross(v_from, v_to), np.dot(v_from, v_to)
    if np.linalg.norm(cross) < 1e-6:
        perp = np.array([1, 0, 0]) if abs(v_from[0]) < 0.9 else np.array([0, 1, 0])
        return _axis_angle_matrix(np.cross(v_from, perp), math.pi) if dot < 0 else np.eye(3)
    return _axis_angle_matrix(cross, math.acos(np.clip(dot, -1.0, 1.0)))

def _axis_angle_matrix(axis, angle):
    axis = axis / (np.linalg.norm(axis) + 1e-12)
    c, s = math.cos(angle), math.sin(angle)
    x, y, z = axis
    return np.array([[c+x*x*(1-c), x*y*(1-c)-z*s, x*z*(1-c)+y*s], [y*x*(1-c)+z*s, c+y*y*(1-c), y*z*(1-c)-x*s], [z*x*(1-c)-y*s, z*y*(1-c)+x*s, c+z*z*(1-c)]])

def generate_cluster(anchor_in, guest_in, n_guests, rng, max_att=50):
    cluster = Molecule([Atom(a.symbol, a.x, a.y, a.z) for a in anchor_in.atoms])
    placed_guests = []
    for _ in range(n_guests):
        success = False
        for _ in range(max_att):
            g = Molecule([Atom(a.symbol, a.x, a.y, a.z) for a in guest_in.atoms])
            g.translate(-g.centroid())
            target_mol = random.choice([cluster] + placed_guests) if placed_guests and rng.random() > 0.4 else cluster
            accs = find_hbond_acceptors(target_mol)
            if not accs: accs = list(range(target_mol.n_atoms()))
            acc_idx = rng.choice(accs)
            donors = find_hbond_donors(g)
            if donors:
                d_h, d_hv = rng.choice(donors)
                d_vec = g.atoms[d_h].coords - g.atoms[d_hv].coords
                out_vec = target_mol.atoms[acc_idx].coords - target_mol.centroid()
                if np.linalg.norm(out_vec) < 0.1: out_vec = np.array([0,0,1])
                g.rotate(_align_vectors(d_vec, -out_vec))
                g.rotate(_axis_angle_matrix(out_vec, rng.uniform(0, 2*math.pi)))
                target_pos = target_mol.atoms[acc_idx].coords + (out_vec/np.linalg.norm(out_vec)) * rng.uniform(1.8, 2.2)
                g.translate(target_pos - g.atoms[d_h].coords)
            else:
                g.translate(target_mol.atoms[acc_idx].coords + np.array([rng.uniform(-3,3) for _ in range(3)]))
            clash = False
            for existing in [cluster] + placed_guests:
                c1, c2 = existing.coords_array(), g.coords_array()
                for p in c1:
                    if np.min(np.linalg.norm(c2 - p, axis=1)) < 1.25: clash = True; break
                if clash: break
            if not clash: placed_guests.append(g); success = True; break
        if not success: return None
    for pg in placed_guests: cluster.merge(pg)
    return cluster

# =============================================================================
# 5. WORKFLOW PIPELINE
# =============================================================================
class Pipeline:
    def __init__(self, fragA_path, fragB_path, n_guests, config, out_dir):
        self.fragA = Molecule.from_xyz(fragA_path)
        self.fragB = Molecule.from_xyz(fragB_path)
        self.n_guests, self.config = n_guests, config
        
        self.out_dir = os.path.abspath(out_dir)
        self.ratio_str = f"1_{self.n_guests}"
        
        self.dirs = {
            "inputs": os.path.join(self.out_dir, "01_Inputs_and_Clusters"),
            "xtb": os.path.join(self.out_dir, "02_xTB_Results"),
            "crest": os.path.join(self.out_dir, "03_CREST_Results"),
            "orca": os.path.join(self.out_dir, "04_ORCA_Refinement"),
            "comparison": os.path.join(self.out_dir, "05_Top_Models_Comparison"),
            "logs": os.path.join(self.out_dir, "logs")
        }
        for d in self.dirs.values(): os.makedirs(d, exist_ok=True)
        
        shutil.copy2(fragA_path, os.path.join(self.dirs["inputs"], "raw_input_anchor.xyz"))
        shutil.copy2(fragB_path, os.path.join(self.dirs["inputs"], "raw_input_guest.xyz"))

        self.state_file = os.path.join(self.out_dir, "state.json")
        self.prov_file = os.path.join(self.out_dir, "provenance_manifest.json")
        self.state = json.load(open(self.state_file, 'r', encoding='utf-8')) if os.path.exists(self.state_file) else {"gen": [], "filt": [], "xtb": {}, "crest": {}, "orca": {}}
        self.provenance = json.load(open(self.prov_file, 'r', encoding='utf-8')) if os.path.exists(self.prov_file) else []

    def save(self): 
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=4)
        with open(self.prov_file, 'w', encoding='utf-8') as f:
            json.dump(self.provenance, f, indent=4)

    def log_provenance(self, stage, structure_id, parent_id, energy, gibbs, imag_freqs, status, rationale):
        record = {
            "stage": stage,
            "structure_id": structure_id,
            "parent_id": parent_id,
            "energy_eh": energy,
            "gibbs_eh": gibbs,
            "imag_freqs": imag_freqs,
            "status": status,
            "rationale": rationale,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.provenance.append(record)
        self.save()

    def run(self, run_xtb=False, run_crest=False, run_orca=False, log_cb=None, status_cb=None):
        def _log(m): 
            logging.getLogger("IAK").info(m)
            if log_cb: log_cb(m + "\n")

        if run_orca and not is_tool_available("orca"):
            raise RuntimeError("Run ORCA DFT is checked, but ORCA is not installed or detected!\nPlease install it using the LOAD LOCAL ENGINE button.")

        if ORCA_DIR and " " in os.path.abspath(ORCA_DIR):
            _log("\n[CRITICAL WARNING] Your ORCA installation folder ('iak_engine') is inside a path with SPACES. OpenMPI is known to fundamentally crash if its installation path has spaces! If the parallel runs fail, IAK will automatically self-heal and fall back to Serial Mode.\n")

        _log("\nSCIENTIFIC NOTICE: Structures produced by this workflow are the lowest found under the current sampling settings. They are NOT guaranteed to be global minima.")

        # --- 1. Generation & PreOpt ---
        if run_xtb and self.config.preopt_inputs and not self.state.get("preopt_done"):
            _log("Stabilizing input geometries using xTB before clustering...")
            for role, mol, name in [("anchor", self.fragA, "Anchor"), ("guest", self.fragB, "Guest")]:
                p = os.path.join(self.dirs["inputs"], f"preopt_{role}_start.xyz")
                mol.to_xyz(p)
                res = self._run_engine_via_wrapper(p, "xtb", f"{self.config.xtb_method} --opt", log_cb, status_cb)
                if res["status"] == "success":
                    if role == "anchor": self.fragA = Molecule.from_xyz(res["path"])
                    else: self.fragB = Molecule.from_xyz(res["path"])
                    shutil.copy2(res["path"], os.path.join(self.dirs["inputs"], f"stabilized_{role}.xyz"))
                    _log(f"-> {name} geometry stabilized.")
            self.state["preopt_done"] = True; self.save()

        if not self.state["gen"]:
            _log(f"Generating {self.config.n_generate} H-bonded seeds...")
            mols = []
            for i in range(self.config.n_generate):
                m = generate_cluster(self.fragA, self.fragB, self.n_guests, random.Random(self.config.random_seed + i))
                if m:
                    p = os.path.join(self.dirs["inputs"], f"cluster_{self.ratio_str}_raw_{i:03d}.xyz")
                    m.to_xyz(p)
                    mols.append(p)
            self.state["gen"] = mols; self.save()

        if not self.state["filt"]:
            _log("Scoring geometries and filtering out RMSD duplicates...")
            mols = [Molecule.from_xyz(p) for p in self.state["gen"]]
            for m in mols: score_geometry(m)
            mols.sort(key=lambda x: x.score, reverse=True)
            unique = []
            for m in mols[:self.config.n_keep_scored]:
                if not any(kabsch_rmsd(m.coords_array(), u.coords_array()) < self.config.rmsd_cutoff for u in unique): unique.append(m)
            for i, m in enumerate(unique[:self.config.n_keep_clustered]):
                p = os.path.join(self.dirs["inputs"], f"cluster_{self.ratio_str}_filt_{i:03d}.xyz")
                m.to_xyz(p, f"Score: {m.score:.2f}")
                self.state["filt"].append(p)
            self.save()

        # --- 2. xTB Optimization ---
        if run_xtb:
            _log(f"\n=======================================================")
            _log(f"Running xTB Optimization on top {self.config.n_run_xtb} clustered geometries...")
            _log(f"=======================================================")
            targets = self.state["filt"][:self.config.n_run_xtb]
            for p in targets:
                stem = Path(p).stem
                if stem not in self.state["xtb"] or self.state["xtb"][stem].get("status") != "success":
                    res = self._run_engine_via_wrapper(p, "xtb", f"{self.config.xtb_method} --opt", log_cb, status_cb)
                    if res["status"] == "success":
                        final_name = os.path.join(self.dirs["xtb"], f"xtbopt_{stem}.xyz")
                        shutil.copy2(res["path"], final_name)
                        res["path"] = final_name
                    self.state["xtb"][stem] = res
                    self.save()

        # --- 3. CREST Exploration ---
        if run_crest:
            _log(f"\n=======================================================")
            _log(f"Filtering xTB results and promoting to CREST...")
            xtb_success = [(k, v) for k, v in self.state["xtb"].items() if v.get("status") == "success"]
            if not xtb_success:
                _log("[ERROR] No successful xTB runs available for CREST. Did xTB fail?")
            else:
                xtb_success.sort(key=lambda x: x[1].get("energy", 0))
                min_e = xtb_success[0][1].get("energy", 0)
                
                promoted_xtb = [(k, v) for k, v in xtb_success if (v["energy"] - min_e) * EH2KCAL <= self.config.xtb_ewin_kcal][:self.config.n_run_crest]
                _log(f"Promoted {len(promoted_xtb)} xTB structures within {self.config.xtb_ewin_kcal} kcal/mol of minimum.")
                
                for k, v in promoted_xtb:
                    if k not in self.state["crest"] or self.state["crest"][k].get("status") != "success": 
                        res = self._run_engine_via_wrapper(v["path"], "crest", f"{self.config.crest_method} -T 4", log_cb, status_cb)
                        if res["status"] == "success":
                            final_conf = os.path.join(self.dirs["crest"], f"crest_conformers_{k}.xyz")
                            shutil.copy2(res["path"], final_conf)
                            res["path"] = final_conf
                            
                            if "best_path" in res and os.path.exists(res["best_path"]):
                                final_best = os.path.join(self.dirs["crest"], f"crest_best_{k}.xyz")
                                shutil.copy2(res["best_path"], final_best)
                                res["best_path"] = final_best
                        self.state["crest"][k] = res
                        self.save()

        # --- 4. ORCA Refinement ---
        if run_orca:
            _log(f"\n=======================================================")
            _log(f"Aggregating CREST conformers and promoting to ORCA DFT...")
            all_confs = []
            for k, v in self.state["crest"].items():
                if v.get("status") == "success" and "path" in v and os.path.exists(v["path"]):
                    mols = read_multi_xyz(v["path"])
                    for i, m in enumerate(mols):
                        m.lineage = [k, f"conf_{i}"]
                        all_confs.append(m)
            
            if not all_confs:
                _log("[WARNING] No CREST conformers found! ORCA cannot proceed.")
            else:
                all_confs.sort(key=lambda x: x.energy_eh)
                min_crest_e = all_confs[0].energy_eh
                
                unique_promoted = []
                for m in all_confs:
                    rel_e = (m.energy_eh - min_crest_e) * EH2KCAL
                    if rel_e > self.config.crest_ewin_kcal: continue
                    is_dup = any(kabsch_rmsd(m.coords_array(), u.coords_array()) < 0.25 for u in unique_promoted)
                    if not is_dup and len(unique_promoted) < 10: unique_promoted.append(m)
                
                _log(f"Promoted top {len(unique_promoted)} highly unique conformers to ORCA.")
                
                for i, m in enumerate(unique_promoted):
                    stem = f"orca_target_{i:03d}"
                    if stem not in self.state["orca"] or self.state["orca"][stem].get("status") != "success":
                        inp_path = os.path.join(self.dirs["inputs"], f"{stem}.xyz")
                        m.to_xyz(inp_path)
                        res = self._run_orca_via_sandbox(inp_path, stem, log_cb, status_cb)
                        
                        if res["status"] == "success":
                            res["lineage"] = " -> ".join(m.lineage)
                            if res["imag"] == 0:
                                best_name = os.path.join(self.dirs["orca"], f"ORCA_MINIMUM_{stem}.xyz")
                                shutil.copy2(res["path"], best_name)
                                res["best_path"] = best_name
                                _log(f"-> True Local Minimum Confirmed!")

                        self.state["orca"][stem] = res
                        self.save()
                        
        self._extract_top_models(log_cb)
        self._generate_graphs()
        self._generate_markdown_report()
        _log("\nPipeline Complete. Check the '5. TOP 3 COMPARE' tab for your final best structures.")

    def _run_engine_via_wrapper(self, xyz_path, engine, flags, log_cb, status_cb):
        fname = os.path.basename(xyz_path)
        stem = Path(xyz_path).stem
        wd = os.path.abspath(os.path.join(self.dirs.get(engine, self.dirs["inputs"]), f"job_{stem}"))
        os.makedirs(wd, exist_ok=True)
        shutil.copy2(xyz_path, os.path.join(wd, fname))
        
        if sys.platform == "win32":
            sh_path = os.path.abspath(os.path.join(wd, f"run_{engine}.sh"))
            with open(sh_path, "w", newline="\n", encoding="utf-8") as f:
                f.write("#!/bin/bash\n")
                
                wsl_wd = get_wsl_path(wd).replace("'", "'\\''")
                f.write(f"SANDBOX=\"/tmp/iak_{engine}_{stem}_$RANDOM\"\n")
                f.write(f"mkdir -p \"$SANDBOX\"\n")
                f.write(f"cp '{wsl_wd}/{fname}' \"$SANDBOX/\"\n")
                f.write(f"cd \"$SANDBOX\"\n")

                if engine == "xtb" and XTB_DIR:
                    wsl_xtb = get_wsl_path(os.path.abspath(XTB_DIR))
                    f.write(f"export PATH='{wsl_xtb}:/usr/bin:/bin:/usr/local/bin:$PATH'\n")
                    f.write(f"export XTBPATH='{get_wsl_path(os.path.abspath(os.path.join(XTB_DIR, '..', 'share', 'xtb')))}'\n")
                    exec_cmd = f"'{wsl_xtb}/xtb'"
                elif engine == "crest" and CREST_DIR:
                    wsl_crest = get_wsl_path(os.path.abspath(CREST_DIR))
                    f.write(f"export PATH='{wsl_crest}:/usr/bin:/bin:/usr/local/bin:$PATH'\n")
                    exec_cmd = f"'{wsl_crest}/crest'"
                else:
                    f.write("source ~/.bashrc 2>/dev/null\n")
                    f.write("source ~/.profile 2>/dev/null\n")
                    f.write("export PATH='/usr/bin:/bin:/usr/local/bin:$PATH'\n")
                    exec_cmd = engine

                f.write(f"export OMP_STACKSIZE=1G\nexport OMP_NUM_THREADS={self.config.cores}\nulimit -s unlimited\n")
                
                f.write(f"{exec_cmd} '{fname}' {flags}\n")
                
                f.write(f"cp -r * '{wsl_wd}/' 2>/dev/null\n")
                f.write(f"cd /tmp\n")
                f.write(f"rm -rf \"$SANDBOX\"\n")
                
            cmd = f"wsl -e bash \"{get_wsl_path(sh_path)}\""
        else:
            cmd = f"cd '{wd}' && {engine} '{fname}' {flags}"
            
        if status_cb: status_cb(engine, 1)
        if log_cb: log_cb(f"\n>>> Executing Sandbox Engine: {engine} {flags}\n")
        
        try:
            proc = subprocess.Popen(cmd, shell=True, cwd=wd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1)
            output = []
            for line in iter(proc.stdout.readline, ''):
                output.append(line); log_cb(line) if log_cb else None
            proc.wait()
            
            if engine == "xtb":
                opt_file = os.path.join(wd, "xtbopt.xyz")
                if not os.path.exists(opt_file): opt_file = os.path.join(wd, fname)
                energy, success = 0.0, False
                for l in reversed(output):
                    if "total energy" in l.lower(): 
                        try:
                            parts = l.split()
                            energy = float(parts[parts.index("Eh")-1]) if "Eh" in parts else float(parts[-2])
                            success = True; break
                        except: pass
                if success or os.path.exists(os.path.join(wd, "xtbopt.xyz")): return {"status": "success", "energy": energy, "path": opt_file}
                return {"status": "failed"}
                
            if engine == "crest":
                conf_file = os.path.join(wd, "crest_conformers.xyz")
                best_file = os.path.join(wd, "crest_best.xyz")
                if os.path.exists(conf_file):
                    return {"status": "success", "path": conf_file, "best_path": best_file if os.path.exists(best_file) else conf_file}
                return {"status": "failed"}
        except Exception as e:
            if log_cb: log_cb(f"\n[Python Error] {e}\n")
        finally:
            if status_cb: status_cb(engine, -1)
        return {"status": "failed"}

    def _run_orca_via_sandbox(self, xyz_path, stem, log_cb, status_cb):
        """The Ultimate 4-Tier ORCA Self-Healing Execution Method with Direct-To-Windows output piping."""
        wd = os.path.abspath(os.path.join(self.dirs["orca"], f"job_{stem}"))
        os.makedirs(wd, exist_ok=True)
        wsl_wd = get_wsl_path(wd).replace("'", "'\\''")
        
        # Load CREST-optimized coordinates directly into Python memory for EMBEDDING
        mol = Molecule.from_xyz(xyz_path)
        
        has_mpi = False
        if sys.platform == "win32" and not ORCA_IS_WINDOWS:
            has_mpi = subprocess.run("wsl -e bash -c 'export PATH=\"/usr/bin:/bin:/usr/local/bin:$PATH\"; which mpirun'", shell=True, capture_output=True).returncode == 0
        else:
            has_mpi = shutil.which("mpirun") is not None

        def _execute_orca(use_mpi: bool, skip_freq: bool):
            inp_file = os.path.join(wd, f"{stem}.inp")
            with open(inp_file, 'w', encoding="utf-8", newline='\n') as f:
                # Strip out Freq and Opt strings if we are falling back
                base_method = self.config.orca_method.replace("Opt Freq", "").replace("TightOpt", "").replace("Opt", "").strip()
                task = "Opt" if skip_freq else "Opt Freq"
                
                f.write(f"! {base_method} {task}\n")
                
                f.write(f"%maxcore {self.config.maxcore}\n")
                
                if use_mpi:
                    f.write(f"%pal nprocs {self.config.cores} end\n")
                
                f.write("%geom\n  MaxIter 350\nend\n")
                f.write("%scf\n  MaxIter 350\nend\n")
                
                # NATIVE XYZ EMBEDDING (Bypasses all "input.xyz not found" errors)
                f.write("* xyz 0 1\n") 
                for a in mol.atoms:
                    f.write(f"{a.symbol:<4} {a.x:15.6f} {a.y:15.6f} {a.z:15.6f}\n")
                f.write("*\n")
                
            if sys.platform == "win32" and not ORCA_IS_WINDOWS:
                sh_path = os.path.abspath(os.path.join(wd, "run_orca.sh"))
                with open(sh_path, "w", newline="\n", encoding="utf-8") as f:
                    f.write("#!/bin/bash\n")
                    f.write(f"SANDBOX=\"/tmp/iak_orca_{stem}_$RANDOM\"\n")
                    f.write(f"mkdir -p \"$SANDBOX\"\n")
                    f.write(f"cp '{wsl_wd}/{stem}.inp' \"$SANDBOX/\"\n")
                    f.write(f"cd \"$SANDBOX\"\n")
                    
                    f.write("export PATH='/usr/bin:/bin:/usr/local/bin:$PATH'\n")
                    f.write("ulimit -s unlimited 2>/dev/null\n")
                    f.write("export OMP_NUM_THREADS=1\n")
                    f.write("export OMP_STACKSIZE=1G\n")
                    
                    if ORCA_DIR:
                        wsl_orca = get_wsl_path(os.path.abspath(ORCA_DIR))
                        f.write(f"export PATH='{wsl_orca}:$PATH'\n")
                        f.write(f"export LD_LIBRARY_PATH='{wsl_orca}:/usr/lib/x86_64-linux-gnu:/usr/lib:$LD_LIBRARY_PATH'\n")
                        exec_cmd = f"'{wsl_orca}/orca'"
                    else:
                        f.write("source ~/.bashrc 2>/dev/null\n")
                        f.write("source ~/.profile 2>/dev/null\n")
                        exec_cmd = "orca"

                    if use_mpi:
                        f.write("REAL_MPI=$(which mpirun)\n")
                        f.write("if [ -z \"$REAL_MPI\" ]; then REAL_MPI=\"/usr/bin/mpirun\"; fi\n")
                        f.write("echo '#!/bin/bash' > ./mpirun\n")
                        f.write("echo \"$REAL_MPI \\\"\\$@\\\"\" >> ./mpirun\n")
                        f.write("chmod +x ./mpirun\n")
                        f.write("export PATH=\".:$PATH\"\n")

                    f.write("export OMPI_ALLOW_RUN_AS_ROOT=1\n")
                    f.write("export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1\n")
                    f.write("export OMPI_MCA_btl_vader_single_copy_mechanism=none\n")
                    f.write("export OMPI_MCA_btl=\"^openib\"\n")
                    f.write("export OMPI_MCA_rmaps_base_oversubscribe=1\n")
                    f.write("export OMPI_MCA_hwloc_base_binding_policy=none\n")
                    
                    # DIRECT-TO-WINDOWS OUTPUT PIPING
                    f.write(f"{exec_cmd} {stem}.inp > '{wsl_wd}/{stem}.out' 2>&1\n")
                    
                    f.write(f"cp {stem}_trj.xyz '{wsl_wd}/' 2>/dev/null\n")
                    f.write(f"cp *xyz '{wsl_wd}/' 2>/dev/null\n")
                    
                    f.write("cd /tmp\n")
                    f.write(f"rm -rf \"$SANDBOX\"\n")
                    
                cmd = f"wsl -e bash \"{get_wsl_path(sh_path)}\""
            elif sys.platform == "win32" and ORCA_IS_WINDOWS:
                cmd = f"cd /d \"{wd}\" && \"{os.path.join(os.path.abspath(ORCA_DIR), 'orca.exe')}\" {stem}.inp > {stem}.out 2>&1"
            else:
                cmd = f"cd '{wd}' && {ORCA_CMD} {stem}.inp > {stem}.out 2>&1"
                
            try:
                proc = subprocess.Popen(cmd, shell=True, cwd=wd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
                for line in iter(proc.stdout.readline, ''):
                    if log_cb: log_cb(line)
                proc.wait()
                
                out_file = os.path.join(wd, f"{stem}.out")
                trj_file = os.path.join(wd, f"{stem}_trj.xyz")
                energy, gibbs, imag, success = 0.0, 0.0, 0, False
                mpirun_crashed, scf_crashed = False, False
                
                time.sleep(1.5)
                
                if os.path.exists(out_file):
                    with open(out_file, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                        if "FINAL SINGLE POINT ENERGY" in content:
                            for line in content.split('\n'):
                                if "FINAL SINGLE POINT ENERGY" in line: energy = float(line.split()[-1])
                                if "Final Gibbs free energy" in line: gibbs = float(line.split()[-2])
                                if "*** imaginary mode ***" in line: imag += 1
                                if "ORCA TERMINATED NORMALLY" in line: success = True
                        
                        content_lower = content.lower()
                        if "mpirun: not found" in content_lower or "aborting the run" in content_lower or "mpi" in content_lower or "hwloc" in content_lower:
                            mpirun_crashed = True
                        if "scf not converged" in content_lower or "optimization did not converge" in content_lower or "std::bad_alloc" in content_lower or "command not found" in content_lower:
                            scf_crashed = True
                            
                        if not success and not mpirun_crashed:
                            scf_crashed = True
                else:
                    if log_cb: log_cb(f"\n[FATAL] Output file {stem}.out was completely lost. ORCA shell was abruptly terminated (OOM kill).\n")
                    scf_crashed = True

                if success and energy != 0.0:
                    opt_path = trj_file if os.path.exists(trj_file) else os.path.join(wd, f"{stem}.xyz")
                    return True, {"status": "success", "energy": energy, "gibbs": gibbs, "imag": imag, "path": opt_path}, False, False
                
                if os.path.exists(out_file) and log_cb:
                    with open(out_file, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                        if lines:
                            last_lines = "".join(lines[-25:])
                            log_cb(f"\n[ORCA CRASH TRACE] {stem}.out:\n{'-'*50}\n{last_lines}{'-'*50}\n")
                
                return False, {"status": "failed"}, mpirun_crashed, scf_crashed
            except Exception as e:
                return False, {"status": "failed"}, True, True

        if status_cb: status_cb("orca", 1)
        
        try:
            # TIER 1: Parallel (4-Core) Opt Freq
            if log_cb: log_cb(f"\n>>> [Tier 1] Executing ORCA (Parallel {self.config.cores}-Core, Opt Freq): {stem}\n")
            success, res, mpi_crash, scf_crash = _execute_orca(use_mpi=has_mpi, skip_freq=False)
            
            if not success:
                # TIER 2: Serial (1-Core) Opt Freq
                if mpi_crash and has_mpi:
                    if log_cb: log_cb(f"\n>>> [Tier 2] MPI Failed! Restarting in Serial Mode (1-Core, Opt Freq): {stem}\n")
                    success, res, mpi_crash, scf_crash = _execute_orca(use_mpi=False, skip_freq=False)
                    
                if not success:
                    # TIER 3: Parallel (4-Core) Opt Only
                    use_mpi_for_opt = has_mpi and not mpi_crash
                    cores = f"{self.config.cores}-Core" if use_mpi_for_opt else "1-Core"
                    if log_cb: log_cb(f"\n>>> [Tier 3] Math/Memory Failed! Stripping Freq, forcing Opt-Only ({cores}): {stem}\n")
                    success, res, mpi_crash, scf_crash = _execute_orca(use_mpi=use_mpi_for_opt, skip_freq=True)
                    
                    # TIER 4: Serial (1-Core) Opt Only
                    if not success and use_mpi_for_opt:
                        if log_cb: log_cb(f"\n>>> [Tier 4] Ultimate Fallback: Serial Mode Opt-Only (1-Core): {stem}\n")
                        success, res, mpi_crash, scf_crash = _execute_orca(use_mpi=False, skip_freq=True)
                    
            return res
        finally:
            if status_cb: status_cb("orca", -1)

    def _extract_top_models(self, log_cb):
        comp_dir = self.dirs["comparison"]
        report = []
        
        # 1. xTB
        best_xtb_k, best_xtb_e, best_xtb_path = None, float('inf'), None
        for k, v in self.state["xtb"].items():
            if v.get("status") == "success" and "energy" in v:
                if v["energy"] < best_xtb_e: best_xtb_e, best_xtb_k, best_xtb_path = v["energy"], k, v["path"]
        if best_xtb_path and os.path.exists(best_xtb_path):
            shutil.copy2(best_xtb_path, os.path.join(comp_dir, "1_BEST_xTB.xyz"))
            report.append(f"xTB,{best_xtb_k},{best_xtb_e:.6f},N/A")

        # 2. CREST
        best_crest_e, best_crest_path = float('inf'), None
        for k, v in self.state["crest"].items():
            if v.get("status") == "success" and "best_path" in v and os.path.exists(v["best_path"]):
                mols = read_multi_xyz(v["best_path"])
                if mols and mols[0].energy_eh < best_crest_e: best_crest_e, best_crest_path = mols[0].energy_eh, v["best_path"]
        if best_crest_path:
            shutil.copy2(best_crest_path, os.path.join(comp_dir, "2_BEST_CREST.xyz"))
            report.append(f"CREST,-,{best_crest_e:.6f},N/A")

        # 3. ORCA
        best_orca_k, best_orca_e, best_orca_g, best_orca_path = None, float('inf'), 0.0, None
        
        # Pass 1: Try to find a True Minimum (imag == 0)
        for k, v in self.state["orca"].items():
            if v.get("status") == "success" and v.get("imag") == 0 and "energy" in v:
                rank_metric = v.get("gibbs") if v.get("gibbs", 0) != 0.0 else v["energy"]
                if rank_metric < best_orca_e:
                    best_orca_e, best_orca_g, best_orca_k, best_orca_path = rank_metric, v.get("gibbs", 0.0), k, v.get("best_path", v["path"])
        
        # Pass 2 (FALLBACK): If no true minima found, just grab the best structure regardless of imag freqs
        if best_orca_path is None:
            for k, v in self.state["orca"].items():
                if v.get("status") == "success" and "energy" in v:
                    rank_metric = v.get("gibbs") if v.get("gibbs", 0) != 0.0 else v["energy"]
                    if rank_metric < best_orca_e:
                        best_orca_e, best_orca_g, best_orca_k, best_orca_path = rank_metric, v.get("gibbs", 0.0), k, v.get("best_path", v["path"])

        if best_orca_path and os.path.exists(best_orca_path):
            shutil.copy2(best_orca_path, os.path.join(comp_dir, "3_BEST_ORCA.xyz"))
            report.append(f"ORCA,{best_orca_k},{best_orca_e:.6f},{best_orca_g:.6f}")
            
        if report:
            with open(os.path.join(comp_dir, "Energy_Comparison.csv"), "w", encoding="utf-8") as f:
                f.write("Level_of_Theory,Source_ID,Total_Energy_Eh,Gibbs_Free_Energy_Eh\n")
                for line in report: f.write(line + "\n")
            if log_cb: log_cb(f"\n-> Extracted Top Models into 05_Top_Models_Comparison\n")

    def _generate_markdown_report(self):
        report_path = os.path.join(self.dirs["comparison"], "Post_CREST_Report.md")
        with open(report_path, 'w', encoding="utf-8") as f:
            f.write(f"# Workflow Analysis Report: Ratio {self.ratio_str.replace('_', ':')}\n\n")
            f.write("## Scientific Disclaimer\n")
            f.write("> The structures reported herein represent local minima found within the defined sampling depth and selected level of theory. They are **not guaranteed global minima**.\n\n")
            
            all_orca = self.state.get("orca", {})
            valid_orca = [(k, v) for k, v in all_orca.items() if v.get("status") == "success"]
            true_minima = [(k, v) for k, v in valid_orca if v.get("imag") == 0]
            
            f.write("## 1. Summary Metrics\n")
            f.write(f"- **ORCA Conformers Evaluated:** {len(all_orca)}\n")
            f.write(f"- **Successful ORCA Completions:** {len(valid_orca)}\n")
            f.write(f"- **True Minima (0 Imag Freqs):** {len(true_minima)}\n\n")
            
            if not true_minima and valid_orca:
                f.write("> **WARNING:** No true minima were found. All completions had imaginary frequencies (Transition States) or skipped the frequency check (Tiers 3/4). The best structure has been extracted anyway so you can open it in Avogadro to inspect the geometry.\n\n")
            elif not valid_orca and len(all_orca) > 0:
                f.write("> **CRITICAL FAILURE:** All ORCA jobs crashed or failed to converge, even after self-healing fallbacks. Please check the `.out` files in `04_ORCA_Refinement`.\n\n")
            
            f.write("## 2. Minima Ranking (Gibbs Free Energy)\n")
            if valid_orca:
                valid_orca.sort(key=lambda x: x[1].get("gibbs") if x[1].get("gibbs", 0) != 0 else x[1].get("energy"))
                best_g = valid_orca[0][1].get("gibbs") if valid_orca[0][1].get("gibbs", 0) != 0 else valid_orca[0][1].get("energy")
                
                f.write("| ORCA ID | Parent Lineage | ΔG (kcal/mol) | Imag Freqs | Status |\n")
                f.write("|---|---|---|---|---|\n")
                
                for k, v in valid_orca:
                    val = v.get("gibbs") if v.get("gibbs", 0) != 0 else v.get("energy")
                    rel_g = (val - best_g) * EH2KCAL
                    f.write(f"| {k} | {v.get('lineage','N/A')} | {rel_g:.2f} | {v.get('imag')} | Success |\n")
                    
                for k, v in all_orca.items():
                    if v.get("status") != "success":
                        f.write(f"| {k} | {v.get('lineage','N/A')} | N/A | N/A | FAILED |\n")
            else:
                f.write("*No valid minima found to rank.*\n")

    def _generate_graphs(self):
        if not MATPLOTLIB_AVAILABLE: return
        graph_dir = os.path.join(self.dirs["comparison"], "graphs")
        os.makedirs(graph_dir, exist_ok=True)
        
        xtb_e = [v["energy"] for v in self.state["xtb"].values() if v.get("status") == "success" and "energy" in v]
        if not xtb_e: return
        min_x = min(xtb_e)
        xtb_rel = sorted([(e - min_x) * EH2KCAL for e in xtb_e])
        
        fig = Figure(figsize=(8, 5))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.plot(range(1, len(xtb_rel)+1), xtb_rel, marker='o', linestyle='-', color='#388bfd', label='xTB Opt')
        ax.axhline(y=self.config.xtb_ewin_kcal, color='r', linestyle='--', label='Promotion Threshold')
        ax.set_title(f"Conformer Energy Distribution ({self.ratio_str.replace('_',':')})")
        ax.set_xlabel("Conformer Rank")
        ax.set_ylabel("Relative Energy (kcal/mol)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(graph_dir, "xtb_energy_profile.png"), dpi=300)

# =============================================================================
# 6. GUI APPLICATION
# =============================================================================
class IAKApp:
    def __init__(self):
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
        self.tk, self.ttk, self.fd, self.mb = tk, ttk, filedialog, messagebox
        self.root = tk.Tk()
        self.root.title("IAK v4.1.20 The Ultimate Orchestrator")
        self.root.geometry("1450x950")
        self.root.configure(bg=_C["bg"])
        self._q = queue.Queue()
        self._vars = {k: tk.StringVar(value=v) for k, v in {"a": "", "b": "", "ratio": "1:2", "mode": "balanced", "out": "run_01"}.items()}
        
        self._vars["cores"] = tk.StringVar(value="4")
        self._vars["maxcore"] = tk.StringVar(value="2000")
        
        self.active_xtb, self.active_crest, self.active_orca = 0, 0, 0
        self.preview_tw = None; self.preview_file = None
        self.is_running = False; self.start_time = 0
        
        self._build_ui()
        setup_logging(gui_queue=self._q)
        self.root.after(100, self._poll_log)
        # Sequence: Capabilities -> Guidelines -> Startup Check
        self.root.after(800, self._show_capabilities_popup)

    def _show_capabilities_popup(self):
        self.cap_w = self.tk.Toplevel(self.root)
        self.cap_w.title("IAK Workflow Capabilities")
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 325
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 200
        self.cap_w.geometry(f"650x420+{x}+{y}")
        self.cap_w.configure(bg=_C["panel"])
        self.cap_w.grab_set()
        self.cap_w.transient(self.root)

        self.tk.Label(self.cap_w, text="✨ IAK Workflow Capabilities", font=("Segoe UI", 16, "bold"), bg=_C["panel"], fg=_C["accent"]).pack(pady=(20, 10))

        caps = [
            "1. Intelligent Generation: Applies H-bond logic docking for supramolecular assembly.",
            "2. Steric Screening: Utilizes Kabsch RMSD clustering to remove structural duplicates.",
            "3. xTB Pre-Optimization: Drives fast GFN2-xTB geometric relaxation.",
            "4. CREST Search: Deep exploration of the conformational energy landscape.",
            "5. ORCA Refinement: 4-Tier Self-Healing DFT optimization & frequencies.",
            "6. Auto-Analysis: Thermodynamic ranking (ΔG) & Top 3 automatic extraction."
        ]
        for cap in caps:
            self.tk.Label(self.cap_w, text=cap, font=("Segoe UI", 11), bg=_C["panel"], fg=_C["text"], justify="left", anchor="w").pack(fill="x", padx=40, pady=8)

        def next_step():
            self.cap_w.destroy()
            self.root.after(100, self._show_guidelines_popup)

        self.tk.Button(self.cap_w, text="Next: Usage Guidelines ➔", command=next_step, bg=_C["run"], fg="white", font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2", width=25).pack(pady=25)

    def _show_guidelines_popup(self):
        self.guide_w = self.tk.Toplevel(self.root)
        self.guide_w.title("IAK Usage Guidelines")
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 350
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 260
        self.guide_w.geometry(f"700x560+{x}+{y}")
        self.guide_w.configure(bg=_C["panel"])
        self.guide_w.grab_set()
        self.guide_w.transient(self.root)

        self.tk.Label(self.guide_w, text="📖 How to Use IAK", font=("Segoe UI", 16, "bold"), bg=_C["panel"], fg=_C["accent"]).pack(pady=(20, 5))

        guide_text = (
            "1. Select your Anchor (A) and Guest (B) .xyz files.\n"
            "2. Define the stoichiometric ratio (e.g., 1:4).\n"
            "3. Set your Hardware Resources (Cores and RAM/Core) to match your system.\n"
            "4. Ensure your computational engines are installed.\n"
            "5. Click 'START RESEARCH PIPELINE' and let IAK handle the rest!"
        )
        self.tk.Label(self.guide_w, text=guide_text, font=("Segoe UI", 11), bg=_C["panel"], fg=_C["text"], justify="left").pack(padx=40, pady=10)

        self.tk.Label(self.guide_w, text="🔗 Manual Engine Downloads:", font=("Segoe UI", 12, "bold"), bg=_C["panel"], fg=_C["yellow"]).pack(pady=(10, 5))

        def make_link(parent, text, url):
            lbl = self.tk.Label(parent, text=text, font=("Segoe UI", 10, "underline"), bg=_C["panel"], fg=_C["accent"], cursor="hand2")
            lbl.pack(pady=2)
            lbl.bind("<Button-1>", lambda e: webbrowser.open_new(url))

        make_link(self.guide_w, "xTB Releases (grimme-lab)", "https://github.com/grimme-lab/xtb/releases")
        make_link(self.guide_w, "CREST Releases (grimme-lab)", "https://github.com/grimme-lab/crest/releases")
        make_link(self.guide_w, "ORCA Forum", "https://orcaforum.kofo.mpg.de")

        self.tk.Label(self.guide_w, text="Thank you for using this app!\n— Asif Raza", font=("Segoe UI", 13, "bold", "italic"), bg=_C["panel"], fg=_C["green"]).pack(pady=30)

        def start_app():
            self.guide_w.destroy()
            self.root.after(100, self._show_startup_check)

        self.tk.Button(self.guide_w, text="Enter Workspace", command=start_app, bg=_C["run"], fg="white", font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2", width=20).pack(pady=10)

    def _show_startup_check(self):
        self.sw = self.tk.Toplevel(self.root)
        self.sw.title("System Verification")
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 225
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 150
        self.sw.geometry(f"450x300+{x}+{y}")
        self.sw.configure(bg=_C["panel"])
        self.sw.grab_set()
        self.sw.transient(self.root)
        
        self.tk.Label(self.sw, text="Checking Computational Engines...", font=("Segoe UI", 14, "bold"), bg=_C["panel"], fg=_C["accent"]).pack(pady=(20, 10))

        self.check_vars = {}
        self.check_btns = {}
        frame = self.tk.Frame(self.sw, bg=_C["panel"])
        frame.pack(fill="both", expand=True, padx=30)
        
        for engine in ["xTB", "CREST", "ORCA"]:
            row = self.tk.Frame(frame, bg=_C["panel"]); row.pack(fill="x", pady=8)
            self.tk.Label(row, text=f"{engine}:", font=("Segoe UI", 11, "bold"), width=8, anchor="w", bg=_C["panel"], fg=_C["text"]).pack(side="left")
            status_lbl = self.tk.Label(row, text="Checking...", font=("Segoe UI", 11, "italic"), width=15, anchor="w", bg=_C["panel"], fg=_C["muted"])
            status_lbl.pack(side="left")
            btn = self.tk.Button(row, text="Add Manually", command=lambda e=engine: self._load_local_from_startup(e), bg=_C["yellow"], fg="black", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2")
            btn.pack(side="right"); btn.pack_forget() 
            self.check_vars[engine] = status_lbl
            self.check_btns[engine] = btn

        self.sw_continue = self.tk.Button(self.sw, text="Continue to IAK", command=self.sw.destroy, bg=_C["run"], fg="white", font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2", width=20)
        self.sw_continue.pack(pady=20); self.sw_continue.pack_forget()

        threading.Thread(target=self._perform_startup_checks, daemon=True).start()

    def _perform_startup_checks(self):
        time.sleep(0.5)
        all_ready = True
        for engine in ["xTB", "CREST", "ORCA"]:
            is_avail = is_tool_available(engine.lower())
            if not is_avail: all_ready = False
            self.root.after(0, lambda e=engine, a=is_avail: self._update_startup_ui(e, a))
            time.sleep(0.4) 
        self.root.after(0, lambda: self._finalize_startup_ui(all_ready))

    def _update_startup_ui(self, engine, is_avail):
        if not hasattr(self, 'sw') or not self.sw.winfo_exists(): return
        lbl, btn = self.check_vars.get(engine), self.check_btns.get(engine)
        if not lbl or not btn: return
        if is_avail: lbl.config(text="Running", fg=_C["green"], font=("Segoe UI", 11, "bold")); btn.pack_forget()
        else: lbl.config(text="Missing", fg=_C["red"], font=("Segoe UI", 11, "bold")); btn.pack(side="right")

    def _finalize_startup_ui(self, all_ready):
        if not hasattr(self, 'sw') or not self.sw.winfo_exists(): return
        self.sw_continue.pack(pady=20)
        if all_ready: self.sw_continue.config(text="All Engines Ready - Start", bg=_C["green"])

    def _load_local_from_startup(self, engine):
        fp = self.fd.askopenfilename(parent=self.sw, title=f"Select {engine} Archive", filetypes=[("Archives", "*.tar.xz *.tar.gz *.tgz *.zip")])
        if fp:
            self.check_vars[engine].config(text="Extracting...", fg=_C["yellow"], font=("Segoe UI", 11, "italic"))
            self.check_btns[engine].pack_forget()
            threading.Thread(target=self._extract_local_worker, args=(fp, engine, True), daemon=True).start()

    def mainloop(self): self.root.mainloop()

    def _poll_log(self):
        while not self._q.empty(): self._append_text(self._q.get() + "\n")
        self.root.after(100, self._poll_log)

    def _append_text(self, t):
        self.term.config(state="normal"); self.term.insert("end", t); self.term.see("end"); self.term.config(state="disabled")

    def _status_cb(self, mode, delta):
        if mode == "xtb": self.active_xtb += delta
        elif mode == "crest": self.active_crest += delta
        elif mode == "orca": self.active_orca += delta
        self.root.after(0, self._update_status_ui)
        
    def _update_status_ui(self):
        total = self.active_xtb + self.active_crest + self.active_orca
        color = _C["green"] if total > 0 else _C["dim"]
        icon = "ACTIVE" if total > 0 else "IDLE"
        self.live_status_lbl.config(text=f"[{icon}] JOBS: {self.active_xtb} xTB | {self.active_crest} CREST | {self.active_orca} ORCA", fg=color)

    def _update_timer(self):
        if self.is_running:
            elapsed = int(time.time() - self.start_time)
            hrs, mins, secs = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
            self.timer_lbl.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
        self.root.after(1000, self._update_timer)

    def _update_installation_labels(self):
        xtb_ok, crest_ok, orca_ok = is_tool_available("xtb"), is_tool_available("crest"), is_tool_available("orca")
        self._xtb_lbl.config(text="xTB: Ready" if xtb_ok else "xTB: Missing", fg=_C["green"] if xtb_ok else _C["red"])
        self._crest_lbl.config(text="CREST: Ready" if crest_ok else "CREST: Missing", fg=_C["green"] if crest_ok else _C["red"])
        self._orca_lbl.config(text="ORCA: Ready" if orca_ok else "ORCA: Missing", fg=_C["green"] if orca_ok else _C["red"])

    def _build_ui(self):
        tk, ttk = self.tk, self.ttk
        style = ttk.Style()
        style.theme_use("clam")
        style.configure('TNotebook.Tab', padding=[15, 5], font=('Segoe UI', 10, 'bold'))
        
        # Header
        hdr = tk.Frame(self.root, bg=_C["hdr_bg"], pady=10); hdr.pack(fill="x")
        tk.Label(hdr, text="IAK PIPELINE", font=("Segoe UI", 20, "bold"), fg=_C["accent"], bg=_C["hdr_bg"]).pack(side="left", padx=20)
        
        stat_f = tk.Frame(hdr, bg=_C["hdr_bg"]); stat_f.pack(side="left", padx=20)
        self._xtb_lbl = tk.Label(stat_f, font=("Segoe UI", 10, "bold"), bg=_C["hdr_bg"]); self._xtb_lbl.pack(side="left", padx=10)
        self._crest_lbl = tk.Label(stat_f, font=("Segoe UI", 10, "bold"), bg=_C["hdr_bg"]); self._crest_lbl.pack(side="left", padx=10)
        self._orca_lbl = tk.Label(stat_f, font=("Segoe UI", 10, "bold"), bg=_C["hdr_bg"]); self._orca_lbl.pack(side="left", padx=10)
        
        self.timer_lbl = tk.Label(hdr, text="00:00:00", font=("Consolas", 12, "bold"), fg=_C["accent"], bg=_C["hdr_bg"])
        self.timer_lbl.pack(side="right", padx=(10, 20))
        
        self.live_status_lbl = tk.Label(hdr, text="[IDLE] JOBS: 0 xTB | 0 CREST | 0 ORCA", font=("Segoe UI", 10, "bold"), fg=_C["dim"], bg=_C["hdr_bg"])
        self.live_status_lbl.pack(side="right", padx=10)
        self._update_installation_labels()

        # Tabs
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.tab_main = tk.Frame(self.nb, bg=_C["bg"]); self.tab_res = tk.Frame(self.nb, bg=_C["bg"])
        self.nb.add(self.tab_main, text=" ⚙️ Workflow Pipeline ")
        self.nb.add(self.tab_res, text=" 📁 Generated Results (Browser) ")
        
        self._build_pipeline_tab(self.tab_main)
        self._build_results_tab(self.tab_res)
        self.root.after(1000, self._update_timer)

    def _build_pipeline_tab(self, parent):
        tk = self.tk
        main = tk.Frame(parent, bg=_C["bg"]); main.pack(fill="both", expand=True, padx=10, pady=10)
        
        left = tk.LabelFrame(main, text=" WORKFLOW SETUP ", fg=_C["accent"], bg=_C["panel"], font=("Segoe UI", 10, "bold"), padx=15, pady=15)
        left.pack(side="left", fill="both", expand=True)
        
        for lbl, var in [("Anchor (A) XYZ:", "a"), ("Guest (B) XYZ:", "b"), ("Ratio (A:B):", "ratio"), ("Output Name:", "out")]:
            f = tk.Frame(left, bg=_C["panel"]); f.pack(fill="x", pady=5)
            tk.Label(f, text=lbl, bg=_C["panel"], fg="white", width=15, anchor="w").pack(side="left")
            tk.Entry(f, textvariable=self._vars[var], bg=_C["entry"], fg="white", bd=0).pack(side="left", fill="x", expand=True, padx=5)
            if "XYZ" in lbl: tk.Button(f, text="...", command=lambda v=var: self._vars[v].set(self.fd.askopenfilename()), bg=_C["accent"]).pack(side="left")
        
        hf = tk.LabelFrame(left, text=" HARDWARE RESOURCES ", fg=_C["accent"], bg=_C["panel"], font=("Segoe UI", 10, "bold"), padx=15, pady=10)
        hf.pack(fill="x", pady=(0, 6))
        
        h1 = tk.Frame(hf, bg=_C["panel"]); h1.pack(fill="x", pady=2)
        tk.Label(h1, text="CPU Cores:", bg=_C["panel"], fg="white", width=15, anchor="w").pack(side="left")
        tk.Entry(h1, textvariable=self._vars["cores"], bg=_C["entry"], fg="white", width=10, bd=0).pack(side="left", padx=5)
        tk.Label(h1, text="(Set to 16, 32, etc. for large systems)", bg=_C["panel"], fg=_C["muted"]).pack(side="left", padx=10)
        
        h2 = tk.Frame(hf, bg=_C["panel"]); h2.pack(fill="x", pady=2)
        tk.Label(h2, text="RAM/Core (MB):", bg=_C["panel"], fg="white", width=15, anchor="w").pack(side="left")
        tk.Entry(h2, textvariable=self._vars["maxcore"], bg=_C["entry"], fg="white", width=10, bd=0).pack(side="left", padx=5)
        tk.Label(h2, text="(e.g., 4000. Total RAM = Cores * RAM/Core)", bg=_C["panel"], fg=_C["muted"]).pack(side="left", padx=10)

        f = tk.Frame(left, bg=_C["panel"]); f.pack(fill="x", pady=15)
        self.run_preopt = tk.BooleanVar(value=True); self.run_xtb = tk.BooleanVar(value=True)
        self.run_crest = tk.BooleanVar(value=True); self.run_orca = tk.BooleanVar(value=True)
        
        tk.Checkbutton(f, text="Pre-Opt", variable=self.run_preopt, bg=_C["panel"], fg=_C["yellow"], selectcolor="black").pack(side="left", padx=5)
        tk.Checkbutton(f, text="Run xTB", variable=self.run_xtb, bg=_C["panel"], fg="white", selectcolor="black").pack(side="left", padx=5)
        tk.Checkbutton(f, text="Run CREST", variable=self.run_crest, bg=_C["panel"], fg="white", selectcolor="black").pack(side="left", padx=5)
        tk.Checkbutton(f, text="Run ORCA DFT", variable=self.run_orca, bg=_C["panel"], fg=_C["accent"], selectcolor="black").pack(side="left", padx=5)
        
        btn_f = tk.Frame(left, bg=_C["panel"]); btn_f.pack(fill="x", pady=5)
        tk.Button(btn_f, text="LOAD LOCAL ENGINE (.tar.xz / .zip)", command=self._load_local, bg="#d29922", fg="white", font=("Segoe UI", 9, "bold")).pack(side="left", fill="x", expand=True, padx=(2, 0))
        
        tk.Label(left, text="💡 ORCA must be downloaded manually from orcaforum.kofo.mpg.de.\nInstall via LOAD LOCAL ENGINE button.", bg=_C["panel"], fg=_C["yellow"], justify="left").pack(anchor="w", pady=(5, 5))
        tk.Label(left, text="SCIENTIFIC NOTICE: Structures are lowest found under current settings,\nNOT guaranteed global minima. ORCA discards transition states.", bg=_C["panel"], fg=_C["red"], justify="left").pack(anchor="w", pady=10)
        
        self.go_btn = tk.Button(left, text="START RESEARCH PIPELINE", command=self._start, bg=_C["run"], fg="white", font=("Segoe UI", 12, "bold"), pady=10)
        self.go_btn.pack(fill="x", pady=10)
        
        right = tk.LabelFrame(main, text=" LIVE PIPELINE TERMINAL ", fg=_C["accent"], bg=_C["panel"], font=("Segoe UI", 10, "bold"))
        right.pack(side="right", fill="both", expand=True, padx=(20, 0))
        self.term = tk.Text(right, bg="black", fg=_C["green"], font=("Consolas", 10), state="disabled")
        self.term.pack(fill="both", expand=True, padx=5, pady=5)

    def _build_results_tab(self, parent):
        tk, ttk = self.tk, self.ttk
        top = tk.Frame(parent, bg=_C["panel"], pady=10); top.pack(fill="x")
        
        tk.Button(top, text=" REFRESH ", command=self._refresh_results, bg=_C["accent"], fg="white", font=("Segoe UI", 10, "bold"), padx=10).pack(side="left", padx=10)
        tk.Button(top, text=" AVOGADRO ", command=self._open_in_avogadro, bg="#6e40c9", fg="white", font=("Segoe UI", 10, "bold"), padx=10).pack(side="left", padx=10)
        tk.Button(top, text=" EXPORT ", command=self._export_file, bg=_C["green"], fg="white", font=("Segoe UI", 10, "bold"), padx=10).pack(side="left", padx=10)
        if MATPLOTLIB_AVAILABLE:
            tk.Button(top, text=" GRAPHS ", command=self._open_graphs, bg=_C["yellow"], fg="black", font=("Segoe UI", 10, "bold"), padx=10).pack(side="left", padx=10)
            
        tk.Label(top, text="(Hover over files for 3D preview)", bg=_C["panel"], fg=_C["muted"], font=("Segoe UI", 10, "italic")).pack(side="right", padx=20)
        
        container = tk.Frame(parent, bg=_C["bg"]); container.pack(fill="both", expand=True, padx=10, pady=10)
        for i in range(5): container.columnconfigure(i, weight=1)
        container.rowconfigure(0, weight=1)
        
        self.listboxes = []
        self.folders = ["01_Inputs_and_Clusters", "02_xTB_Results", "03_CREST_Results", "04_ORCA_Refinement", "05_Top_Models_Comparison"]
        
        def make_listbox(col, title, fg_color=_C["green"]):
            f = tk.LabelFrame(container, text=title, bg=_C["panel"], fg=_C["accent"], font=("Segoe UI", 9, "bold"))
            f.grid(row=0, column=col, sticky="nsew", padx=2, pady=5)
            lb = tk.Listbox(f, bg=_C["entry"], fg=fg_color, font=("Consolas", 9), selectbackground=_C["accent"], exportselection=False)
            lb.pack(side="left", fill="both", expand=True, padx=2, pady=5)
            sb = ttk.Scrollbar(f, orient="vertical", command=lb.yview); sb.pack(side="right", fill="y"); lb.config(yscrollcommand=sb.set)
            lb.bind("<Double-Button-1>", lambda e, l=lb, c=col: self._open_file(l, c))
            lb.bind("<Motion>", lambda e, l=lb, c=col: self._on_hover(e, l, c))
            lb.bind("<Leave>", lambda e: self._hide_preview())
            self.listboxes.append(lb)
            return lb
            
        make_listbox(0, " 1. Clusters "); make_listbox(1, " 2. xTB Opt ")
        make_listbox(2, " 3. CREST "); make_listbox(3, " 4. ORCA DFT ")
        make_listbox(4, " 5. TOP 3 COMPARE ", fg_color=_C["yellow"])

    def _get_selected_filepath(self):
        for col, lb in enumerate(self.listboxes):
            sel = lb.curselection()
            if sel:
                fname = lb.get(sel[0])
                if fname.startswith("("): return None
                return os.path.join(os.path.abspath(self._vars["out"].get().strip(' "\'')), self.folders[col], fname)
        return None

    def _open_graphs(self):
        graph_dir = os.path.join(os.path.abspath(self._vars["out"].get().strip(' "\'')), "05_Top_Models_Comparison", "graphs")
        if os.path.exists(graph_dir):
            if sys.platform == "win32": os.startfile(graph_dir)
            elif sys.platform == "darwin": subprocess.call(["open", graph_dir])
            else: subprocess.call(["xdg-open", graph_dir])
        else:
            self.mb.showinfo("Graphs", "No graphs generated yet. Run pipeline to generate them.")

    def _open_in_avogadro(self):
        path = self._get_selected_filepath()
        if not path: return self.mb.showwarning("Select File", "Please select a file first.")
        cmd = None
        if shutil.which("avogadro"): cmd = ["avogadro", path]
        elif shutil.which("avogadro2"): cmd = ["avogadro2", path]
        elif sys.platform == "win32":
            cps = [
                r"C:\Program Files\Avogadro\bin\avogadro.exe", r"C:\Program Files (x86)\Avogadro\bin\avogadro.exe",
                r"C:\Program Files\Avogadro\avogadro.exe", r"C:\Program Files (x86)\Avogadro\avogadro.exe",
                r"C:\Program Files\Avogadro2\bin\avogadro2.exe", r"C:\Program Files\Avogadro2\avogadro2.exe"
            ]
            for cp in cps:
                if os.path.exists(cp): cmd = [cp, path]; break
        if not cmd: return self.mb.showerror("Not Found", "Avogadro not found in standard paths.")
        try: subprocess.Popen(cmd)
        except Exception as e: self.mb.showerror("Error", f"Launch failed: {e}")

    def _export_file(self):
        path = self._get_selected_filepath()
        if not path: return self.mb.showwarning("Select File", "Please select a file first.")
        dest = self.fd.asksaveasfilename(defaultextension=Path(path).suffix, initialfile=os.path.basename(path), title="Export")
        if dest: shutil.copy2(path, dest)

    def _on_hover(self, event, listbox, col):
        idx = listbox.nearest(event.y)
        bbox = listbox.bbox(idx)
        if not bbox or not (bbox[1] <= event.y <= bbox[1] + bbox[3]): return self._hide_preview()
        fname = listbox.get(idx)
        if fname.startswith("("): return self._hide_preview()
        filepath = os.path.join(os.path.abspath(self._vars["out"].get().strip(' "\'')), self.folders[col], fname)
        if not os.path.exists(filepath) or not fname.endswith(".xyz"): return
        if self.preview_file == filepath and self.preview_tw is not None: return
        self._show_preview(event.x_root, event.y_root, filepath)

    def _hide_preview(self):
        if self.preview_tw: self.preview_tw.destroy(); self.preview_tw = None
        self.preview_file = None

    def _show_preview(self, x, y, filepath):
        self._hide_preview()
        self.preview_file = filepath
        tw = self.tk.Toplevel(self.root); self.preview_tw = tw
        tw.wm_overrideredirect(True); tw.geometry(f"+{x+15}+{y+15}")
        cv = self.tk.Canvas(tw, width=250, height=250, bg=_C["panel"], highlightthickness=2, highlightbackground=_C["accent"])
        cv.pack()
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f: lines = f.readlines()
            n = int(lines[0].strip())
            atoms = [(p[0].upper(), float(p[1]), float(p[2]), float(p[3])) for l in lines[2:2+n] for p in [l.split()] if len(p)>=4]
            if not atoms: return
            coords = np.array([[a[1], a[2], a[3]] for a in atoms])
            coords -= np.mean(coords, axis=0)
            Rx = np.array([[1, 0, 0], [0, math.cos(0.35), -math.sin(0.35)], [0, math.sin(0.35), math.cos(0.35)]])
            Ry = np.array([[math.cos(0.61), 0, math.sin(0.61)], [0, 1, 0], [-math.sin(0.61), 0, math.cos(0.61)]])
            coords = coords @ Rx @ Ry
            scale = 85.0 / (np.max(np.abs(coords[:, :2])) or 1)
            dist_mat = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=2)
            drawn = set()
            for i, j in np.argwhere((dist_mat > 0.4) & (dist_mat < 1.8)):
                if i < j: drawn.add(((coords[i, 2] + coords[j, 2]) / 2, 125+coords[i, 0]*scale, 125+coords[i, 1]*scale, 125+coords[j, 0]*scale, 125+coords[j, 1]*scale))
            for b in sorted(list(drawn), key=lambda x: x[0]): cv.create_line(b[1], b[2], b[3], b[4], fill=_C["muted"], width=3)
            cols = {"H": "#FFFFFF", "C": "#808080", "N": "#3050F8", "O": "#FF0D0D", "F": "#90E050"}
            atom_data = [(coords[i, 2], a[0], 125+coords[i, 0]*scale, 125+coords[i, 1]*scale) for i, a in enumerate(atoms)]
            for z, sym, px, py in sorted(atom_data, key=lambda x: x[0]):
                r = 5 if sym == "H" else 9
                cv.create_oval(px-r, py-r, px+r, py+r, fill=cols.get(sym, "#E06633"), outline="#111111")
        except Exception: cv.create_text(125, 125, text="Preview Unavailable", fill="white")

    def _refresh_results(self):
        out_dir = os.path.abspath(self._vars["out"].get().strip(' "\''))
        for col, lb in enumerate(self.listboxes):
            lb.delete(0, self.tk.END)
            path = os.path.join(out_dir, self.folders[col])
            if os.path.exists(path):
                files = sorted([f for f in os.listdir(path) if f.endswith(".xyz") or f.endswith(".json") or f.endswith(".csv") or f.endswith(".md")])
                for f in files: lb.insert(self.tk.END, f)
                if not files: lb.insert(self.tk.END, "(Empty)")

    def _open_file(self, listbox, col):
        sel = listbox.curselection()
        if not sel: return
        fname = listbox.get(sel[0])
        if fname.startswith("("): return
        path = os.path.join(os.path.abspath(self._vars["out"].get().strip(' "\'')), self.folders[col], fname)
        if os.path.isfile(path):
            try:
                if sys.platform == "win32": os.startfile(path)
                elif sys.platform == "darwin": subprocess.call(["open", path])
                else: subprocess.call(["xdg-open", path])
            except Exception as e: self._append_text(f"[Error] {e}\n")

    def _start(self):
        v = {}
        for k, var in self._vars.items():
            val = var.get().strip(' "\'')
            if k in ["a", "b", "out"] and val:
                val = os.path.abspath(val)
            v[k] = val
            
        inject_embedded_engines()
        self._update_installation_labels()
            
        if not os.path.isfile(v["a"]): 
            self._append_text(f"\n[Error] Anchor XYZ file not found or invalid path: {v['a']}\n")
            return self.mb.showerror("Error", f"Anchor XYZ file not found:\n{v['a']}")
            
        if not os.path.isfile(v["b"]): 
            self._append_text(f"\n[Error] Guest XYZ file not found or invalid path: {v['b']}\n")
            return self.mb.showerror("Error", f"Guest XYZ file not found:\n{v['b']}")
            
        out_dir = v["out"]
        if os.path.exists(out_dir) and os.path.exists(os.path.join(out_dir, "state.json")):
            ans = self.mb.askyesnocancel("Job Exists", "RESUME existing job?\n\nNo = Start NEW Job (Safe)")
            if ans is None: return
            elif ans is False:
                c = 2
                while os.path.exists(f"{out_dir}_{c}"): c += 1
                v["out"] = os.path.abspath(f"{out_dir}_{c}")
                self._vars["out"].set(v["out"])
        
        self.go_btn.config(state="disabled", text="RUNNING...")
        self.nb.select(0) 
        self._append_text("\n[System] Initialization complete. Booting Pipeline Thread...\n")
        
        self.start_time = time.time()
        self.is_running = True
        
        threading.Thread(target=self._worker, args=(v,), daemon=True).start()

    def _worker(self, v):
        try:
            config = Config.from_mode(RunMode[v.get("mode", "balanced").upper()])
            config.preopt_inputs = self.run_preopt.get()
            
            try:
                config.cores = int(v.get("cores", 4))
                config.maxcore = int(v.get("maxcore", 2000))
            except ValueError:
                raise RuntimeError("CPU Cores and RAM/Core must be valid numbers!")
            
            try:
                ratio_val = int(v["ratio"].split(":")[1])
                pipe = Pipeline(v["a"], v["b"], ratio_val, config, v["out"])
            except Exception as parse_e:
                raise RuntimeError(f"Failed to initialize pipeline. Check formatting.\nDetails: {parse_e}")
                
            pipe.run(run_xtb=self.run_xtb.get(), run_crest=self.run_crest.get(), run_orca=self.run_orca.get(), log_cb=self._append_text, status_cb=self._status_cb)
            
            self.root.after(0, self._refresh_results)
            self.root.after(0, lambda: self.mb.showinfo("Done", "Pipeline execution finished!\n\nCheck the 5th section for the Top 3 Models and the Energy Comparison CSV."))
        except Exception as e: 
            self.root.after(0, lambda e=e: self._append_text(f"\n[CRITICAL ERROR] Pipeline aborted: {str(e)}\n"))
            self.root.after(0, lambda e=e: self.mb.showerror("Error", str(e)))
        finally: 
            self.is_running = False
            self.root.after(0, lambda: self.go_btn.config(state="normal", text="START RESEARCH PIPELINE"))

    def _load_local(self):
        fp = self.fd.askopenfilename(title="Select Engine Archive", filetypes=[("Archives", "*.tar.xz *.tar.gz *.tgz *.zip")])
        if fp: 
            fname = os.path.basename(fp).lower()
            if "xtb" in fname: engine_type = "xTB"
            elif "crest" in fname: engine_type = "CREST"
            elif "orca" in fname: engine_type = "ORCA"
            else: engine_type = "Unknown"
            
            self._append_text(f"\n[Local Load] Selected {engine_type} archive: {fname}\n")
            threading.Thread(target=self._extract_local_worker, args=(fp, engine_type), daemon=True).start()

    def _extract_local_worker(self, fp, engine_type, from_startup=False):
        try:
            os.makedirs(ENGINE_DIR, exist_ok=True)
            self._append_text(f"  Extracting {fp} into {ENGINE_DIR}...\n")
            if fp.lower().endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(fp, 'r') as zip_ref:
                    zip_ref.extractall(ENGINE_DIR)
            else:
                success_wsl = False
                if sys.platform == "win32":
                    wsl_fp = get_wsl_path(os.path.abspath(fp))
                    wsl_dir = get_wsl_path(os.path.abspath(ENGINE_DIR))
                    self._append_text(f"  [WSL] Using native Linux extraction to safely handle symlinks...\n")
                    cmd = f"wsl -e bash -c \"cd '{wsl_dir}' && tar -xf '{wsl_fp}'\""
                    rc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if rc.returncode == 0:
                        success_wsl = True
                    else:
                        self._append_text(f"  [WSL Tar Warning] Extraction issue: {rc.stderr.strip()}\n  Falling back to pure Python extractor...\n")
                
                if not success_wsl:
                    with tarfile.open(fp) as f:
                        for member in f.getmembers():
                            try: f.extract(member, ENGINE_DIR)
                            except Exception: pass
            
            inject_embedded_engines()
            self._append_text(f"[Success] {engine_type} locally installed and linked!\n")
            self.root.after(0, self._update_installation_labels)
            
            if from_startup:
                is_avail = is_tool_available(engine_type.lower())
                self.root.after(0, lambda e=engine_type, a=is_avail: self._update_startup_ui(e, a))
            else:
                self.root.after(0, lambda: self.mb.showinfo("Success", f"{engine_type} successfully installed from local file!"))
        except Exception as e:
            self._append_text(f"[Error] Failed to extract local archive: {str(e)}\n")
            if from_startup:
                self.root.after(0, lambda e=engine_type: self._update_startup_ui(e, False))

if __name__ == "__main__": IAKApp().mainloop()
