## Project Overview
This project provides a framework for comparing three search-based optimization algorithms — **Random Search (RS)**, **Simulated Annealing (SA)**, and **Genetic Algorithm (GA)** — on configurable software systems. Each algorithm is evaluated across multiple datasets and runs, with statistical significance testing to identify which algorithm finds the best configuration.

## Features
- Three optimization algorithms: Random Search, Simulated Annealing, and Genetic Algorithm.
- 30 independent runs per algorithm per dataset to ensure statistical reliability.
- Mann-Whitney U statistical tests to compare algorithm performance.
- Per-dataset visualizations showing performance across runs.
- Global summary report with median performance heatmap, win distribution bar chart, and p-value heatmap.

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Nass1195/Configuration-Performance-Tuning.git
cd Configuration-Performance-Tuning
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Dataset Description
The `datasets` folder contains CSV files representing different configurable systems. Each CSV file has the following structure:

- **Columns 1 to n-1:** Configuration parameters (discrete values).
- **Column n:** Performance objective (numeric, lower is better for all included systems).

### Included Systems
| System     | Optimization Type |
|------------|-------------------|
| 7z         | Minimization      |
| Apache     | Minimization      |
| Brotli     | Minimization      |
| LLVM       | Minimization      |
| PostgreSQL | Minimization      |
| Spear      | Minimization      |
| Storm      | Minimization      |
| x264       | Minimization      |

## Algorithms

### Random Search (RS)
Baseline algorithm. At each iteration, uniformly samples a random configuration from the valid domain of each parameter.

### Simulated Annealing (SA)
Starts from a valid random configuration and iteratively explores neighbors by mutating a subset of parameters. Accepts worse solutions with a probability that decreases over time (cooling schedule: rate = 0.98), allowing escape from local optima.

### Genetic Algorithm (GA)
Maintains a population of valid configurations. Uses tournament selection to choose parents, uniform crossover to produce offspring, and single-point mutation. The worst individual in the population is replaced when a valid, better offspring is found.

## Usage

The program has two modes: a **tool mode** (default) for finding the best configuration of a single dataset, and a **test mode** (`-test`) for running the full algorithm comparison loop.

### 1. Tool Mode — Find Best Configuration
Run the program with a dataset path to find the best configuration using the chosen algorithm:
```bash
python main.py -dataset datasets/7z.csv
```

Optional arguments:
- `-algo {RS,SA,GA}` — algorithm to use (default: `SA`)
- `-budget N` — number of evaluations (default: `100`)

Example with all options:
```bash
python main.py -dataset datasets/Apache.csv -algo GA -budget 200
```

Tool-mode output prints the best configuration and its performance, and saves the search trace to `tool_results/<dataset>_<algo>_trace.csv`.

### 2. Test Mode — Algorithm Comparison
Run the full comparison loop (3 algorithms × 30 runs × all datasets, budget = 100):
```bash
python main.py -test
```
Results for each run are saved as CSV files under `rs_results/`, `sa_results/`, and `ga_results/`. Per-dataset comparison plots and a global summary report are saved to `search_results/`.

### 3. Visualize Search Results
Run the visualization script to regenerate performance plots from existing result files:
```bash
python visualize_serach_results.py
```

### 4. Help
```bash
python main.py -h
```

## Output Files

### Per-Dataset (in `search_results/`)
| File | Description |
|------|-------------|
| `<dataset>_search_results.png` | Line plot comparing RS, SA, and GA performance across 30 runs |

### Global Summary (in `search_results/`)
| File | Description |
|------|-------------|
| `global_summary_report.csv` | Median performance and p-values for all datasets |
| `global_performance_heatmap.png` | Normalized median performance heatmap across datasets and algorithms |
| `global_win_distribution.png` | Bar chart showing how many datasets each algorithm wins (lowest median) |
| `p_values_heatmap.png` | Heatmap of Mann-Whitney U p-values for all pairwise comparisons |

### Per-Algorithm Raw Results
Each algorithm stores one CSV per run under its results folder:
```
rs_results/<dataset>/run_<n>.csv
sa_results/<dataset>/run_<n>.csv
ga_results/<dataset>/run_<n>.csv
```

## Statistical Testing
Pairwise comparisons use the one-sided **Mann-Whitney U test** (alternative = `less`). A p-value < 0.05 indicates that one algorithm finds significantly lower (better) performance values than the other.

Comparisons performed per dataset:
- SA vs RS
- GA vs RS
- SA vs GA
- GA vs SA

## Project Structure
```
project-folder/
├── datasets/               # Input datasets (CSV files)
├── tool_results/           # Search traces from tool mode (single-run)
├── rs_results/             # Raw RS run results per dataset (test mode)
├── sa_results/             # Raw SA run results per dataset (test mode)
├── ga_results/             # Raw GA run results per dataset (test mode)
├── search_results/         # Per-dataset plots and global summary (test mode)
├── main.py                 # CLI entry: tool mode (default) or test mode (-test)
├── visualize_serach_results.py  # Script for regenerating visualizations
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## Notes
- Only configurations that exist in the dataset are evaluated; invalid configurations are skipped (SA and GA retry until a valid configuration is found for initialization).
- Random Search assigns a penalty value (`max * 2`) to invalid sampled configurations rather than skipping them.
- All algorithms use a fixed budget of evaluations (not wall-clock time), making comparisons fair across algorithms.
