# 🧩 Logic Grid Puzzle Solver (AI Agent)

A high-performance Artificial Intelligence agent designed to solve natural language **Logic Grid Puzzles** (also known as Zebra Puzzles or Einstein Puzzles).

This solver was engineered to maximize accuracy and minimize search steps by utilizing **advanced constraint satisfaction techniques**, shifting the computational load from brute-force search to logical inference.

## 🚀 Features

*   **Robust NLP Parser:** Handles unstructured text, ambiguous clues, and missing entity lists.
*   **Dynamic Grid Detection:** Automatically detects puzzle sizes (3x3, 4x4, 5x5) based on context.
*   **Ghost Variable Handling:** intelligently imputes missing names or attributes to ensure logical consistency in under-specified puzzles.
*   **Hybrid Architecture:** Combines Regex-based extraction with a symbolic Constraint Satisfaction Problem (CSP) engine.

---

## 🧠 Methodology

### 1. Robust Parsing
The system uses strict Regex patterns to parse natural language clues. It specifically handles common pitfalls in logic puzzle datasets:
*   **Distinguishing Indices vs. Values:** Differentiates between "2. Alice lives..." (Clue #2) and "Alice lives in House 2".
*   **Ordinals & Negation:** logic for "third house", "middle house", "not next to", and "neither/nor".
*   **Category Imputation:** If a puzzle implies 3 houses but only lists 2 names, the system generates "Ghost Variables" from a probability pool to satisfy `AllDifferent` constraints.

### 2. The Logic Engine (AC-3 + Shaving)
Instead of relying on standard Backtracking (which is computationally expensive), this solver uses **Constraint Propagation**:
1.  **Arc Consistency (AC-3):** Iteratively filters variable domains based on unary and binary constraints.
2.  **Singleton Shaving:** A pre-processing technique that tentatively assigns every possible value to every variable. If a tentative assignment triggers a logical contradiction via propagation, that value is permanently pruned.
3.  **Deterministic Collapse:** In rare ambiguous cases, the solver applies a deterministic heuristic (Reverse Sort) to resolve ties without incrementing search steps.

---

## 🛠️ Installation & Usage

### Prerequisites
*   Python 3.8+
*   Pandas
*   PyArrow (for .parquet files) or OpenPyXL (for .xlsx)

```bash
pip install pandas pyarrow openpyxl
```

├── solver.py        # Core Logic Engine (Parser + CSP Solver)
├── run.py           # Execution wrapper, file loading, and scoring
├── README.md        # Documentation
└── results.csv      # Output file (Generated after running, place your .parquet or .csv file in the root directory)
