import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import re
import math
import pandas as pd


# ============================================================
# Domain parsing: supports comma lists, integer ranges, float ranges, and stepped ranges
# ============================================================

def parse_domain(raw):
    """
    Parse column values from user input.
    Formats:
      - comma list: "1,2,4,8" or "low,medium,high"
      - int range: "1-100"
      - float range: "0.0-1.0"
      - stepped range: "0-10 step 2" or "0.0-1.0 step 0.1"
    Returns: list (discrete) or tuple ('int_range'|'float_range', min, max)
    """
    raw = raw.strip()

    # Check for "lo-hi step s" or "lo to hi step s"
    m = re.match(r'^(-?[\d.]+)\s*(?:to|-)\s*(-?[\d.]+)\s+step\s+([\d.]+)$', raw, re.IGNORECASE)
    if m:
        lo, hi, step = float(m.group(1)), float(m.group(2)), float(m.group(3))
        vals, v = [], lo
        while v <= hi + 1e-9:
            s = f"{v:.10g}"
            vals.append(s)
            v += step
        return vals

    # Check for "lo-hi" continuous range (not comma-separated)
    m = re.match(r'^(-?[\d.]+)\s*-\s*(-?[\d.]+)$', raw)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        if lo == int(lo) and hi == int(hi):
            return ('int_range', int(lo), int(hi))
        return ('float_range', lo, hi)

    # Default: comma-separated discrete list
    return [v.strip() for v in raw.split(',') if v.strip()]


def sample_from(domain):
    """Sample a value from a domain (list or continuous range)."""
    if isinstance(domain, list):
        return random.choice(domain)
    kind, lo, hi = domain
    if kind == 'int_range':
        return str(random.randint(lo, hi))
    return f"{random.uniform(lo, hi):.6g}"


def sample_neighbor(domain, current):
    """Sample a different value from domain if possible."""
    if isinstance(domain, list):
        others = [v for v in domain if v != current]
        return random.choice(others) if others else current
    # Continuous: just re-sample (exact equality vanishingly unlikely)
    return sample_from(domain)


# ============================================================
# Interactive algorithm generators
# ============================================================

def rs_interactive(unique_values, config_columns, budget, maximize=False):
    is_better = (lambda n, r: n > r) if maximize else (lambda n, r: n < r)
    best_solution, best_performance = None, None
    history = []

    for _ in range(budget):
        config = [sample_from(unique_values[col]) for col in config_columns]
        perf = yield config
        history.append(list(config) + [perf])
        if best_solution is None or is_better(perf, best_performance):
            best_solution, best_performance = list(config), perf

    return best_solution, best_performance, history


def sa_interactive(unique_values, config_columns, budget, maximize=False):
    is_better = (lambda n, r: n > r) if maximize else (lambda n, r: n < r)

    current = [sample_from(unique_values[col]) for col in config_columns]
    current_perf = yield current
    best, best_perf = list(current), current_perf
    history = [list(current) + [current_perf]]

    temp = max(1.0, abs(current_perf) * 0.2)
    cooling = 0.98
    n_changes = max(min(3, len(config_columns) // 2), 1)

    for _ in range(budget - 1):
        neighbor = list(current)
        for idx in random.sample(range(len(config_columns)), n_changes):
            col = config_columns[idx]
            neighbor[idx] = sample_neighbor(unique_values[col], current[idx])

        perf = yield neighbor
        history.append(list(neighbor) + [perf])

        delta = (current_perf - perf) if maximize else (perf - current_perf)
        if delta < 0 or random.random() < math.exp(-delta / max(temp, 1e-10)):
            current, current_perf = neighbor, perf
            if is_better(current_perf, best_perf):
                best, best_perf = list(current), current_perf
        temp *= cooling

    return best, best_perf, history


def ga_interactive(unique_values, config_columns, budget, maximize=False):
    is_better = (lambda n, r: n > r) if maximize else (lambda n, r: n < r)
    best_fn = max if maximize else min
    worst_fn = min if maximize else max

    pop_size = min(max(5, budget // 5), budget)
    pop, perfs, history = [], [], []

    for _ in range(pop_size):
        config = [sample_from(unique_values[col]) for col in config_columns]
        perf = yield config
        pop.append(list(config))
        perfs.append(perf)
        history.append(list(config) + [perf])

    best_perf = best_fn(perfs)
    best = list(pop[perfs.index(best_perf)])

    for _ in range(budget - pop_size):
        t1, t2 = random.sample(range(len(pop)), 2)
        p1 = pop[t1] if is_better(perfs[t1], perfs[t2]) else pop[t2]
        t3, t4 = random.sample(range(len(pop)), 2)
        p2 = pop[t3] if is_better(perfs[t3], perfs[t4]) else pop[t4]

        child = [p1[i] if random.random() < 0.5 else p2[i] for i in range(len(config_columns))]
        mut_idx = random.randint(0, len(config_columns) - 1)
        child[mut_idx] = sample_from(unique_values[config_columns[mut_idx]])

        perf = yield child
        history.append(list(child) + [perf])

        wi = perfs.index(worst_fn(perfs))
        pop[wi], perfs[wi] = list(child), perf
        if is_better(perf, best_perf):
            best, best_perf = list(child), perf

    return best, best_perf, history


ALGORITHMS = {
    'RS': ('Random Search', rs_interactive),
    'SA': ('Simulated Annealing', sa_interactive),
    'GA': ('Genetic Algorithm', ga_interactive),
}

# Penalty values for invalid configs (sent to generator, not displayed in UI)
INVALID_PERF = {True: -1e15, False: 1e15}


class ConfigTunerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Configuration Tuning Tool")
        self.column_rows = []
        self._processing = False  # Guard against double-submit
        self.valid_evals = 0  # Count of valid (non-invalid) evaluations
        self._build_setup_view()

    # ---- Setup view ----
    def _build_setup_view(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.column_rows = []
        self.root.title("Configuration Tuning Tool — Setup")
        self.root.minsize(650, 450)

        intro = ttk.Label(
            self.root,
            text="Interactive search: define your configuration space, then evaluate "
                 "each suggested configuration and enter the measured performance.",
            padding=10, wraplength=600, justify='left',
        )
        intro.pack(fill='x')

        top = ttk.Frame(self.root, padding=(10, 0, 10, 5))
        top.pack(fill='x')

        ttk.Label(top, text="Algorithm:").grid(row=0, column=0, sticky='w', padx=4, pady=5)
        self.algo_var = tk.StringVar(value='SA')
        ttk.Combobox(top, textvariable=self.algo_var, values=['RS', 'SA', 'GA'],
                     state='readonly', width=6).grid(row=0, column=1, padx=4)

        ttk.Label(top, text="Budget:").grid(row=0, column=2, sticky='w', padx=10)
        self.budget_var = tk.StringVar(value='20')
        ttk.Entry(top, textvariable=self.budget_var, width=8).grid(row=0, column=3, padx=4)

        ttk.Label(top, text="Objective:").grid(row=0, column=4, sticky='w', padx=10)
        self.obj_var = tk.StringVar(value='min')
        ttk.Radiobutton(top, text="Minimize", variable=self.obj_var, value='min').grid(row=0, column=5, padx=2)
        ttk.Radiobutton(top, text="Maximize", variable=self.obj_var, value='max').grid(row=0, column=6, padx=2)

        ttk.Label(self.root, text="Configuration Columns:", padding=(10, 6, 10, 2)).pack(anchor='w')

        hint = ttk.Label(
            self.root,
            text="Format: comma-separated (1,2,4,8) | integer range (1-100) | float range (0.0-1.0) | stepped (0-10 step 2)",
            foreground='gray', padding=(10, 0), font=('TkDefaultFont', 9),
        )
        hint.pack(anchor='w')

        hdr = ttk.Frame(self.root, padding=(10, 2))
        hdr.pack(fill='x')
        ttk.Label(hdr, text="Column name", width=20, anchor='w').grid(row=0, column=0, padx=4)
        ttk.Label(hdr, text="Possible values / range", width=42, anchor='w').grid(row=0, column=1, padx=4)

        self.columns_frame = ttk.Frame(self.root, padding=(10, 0))
        self.columns_frame.pack(fill='x')

        self._add_column_row()
        self._add_column_row()

        actions = ttk.Frame(self.root, padding=10)
        actions.pack(fill='x')
        ttk.Button(actions, text="+ Add Column", command=self._add_column_row).pack(side='left')
        ttk.Button(actions, text="Start", command=self._start, width=15).pack(side='right', ipadx=5, ipady=3)

    def _add_column_row(self):
        row = ttk.Frame(self.columns_frame)
        row.pack(fill='x', pady=2)
        name_e = ttk.Entry(row, width=20)
        name_e.grid(row=0, column=0, padx=4)
        vals_e = ttk.Entry(row, width=42)
        vals_e.grid(row=0, column=1, padx=4)
        ttk.Button(row, text="Remove", command=lambda r=row: self._remove_column_row(r)).grid(row=0, column=2, padx=4)
        self.column_rows.append((row, name_e, vals_e))

    def _remove_column_row(self, row):
        self.column_rows = [r for r in self.column_rows if r[0] is not row]
        row.destroy()

    def _start(self):
        try:
            budget = int(self.budget_var.get())
            if budget <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Budget must be a positive integer.")
            return

        config_columns, unique_values = [], {}
        for _, name_e, vals_e in self.column_rows:
            name = name_e.get().strip()
            raw = vals_e.get().strip()
            if not name and not raw:
                continue
            if not name:
                messagebox.showerror("Invalid input", "Every column needs a name.")
                return
            domain = parse_domain(raw)
            if not domain or (isinstance(domain, list) and len(domain) == 0):
                messagebox.showerror("Invalid input", f"Column '{name}' has no valid values.")
                return
            if name in unique_values:
                messagebox.showerror("Invalid input", f"Duplicate column name '{name}'.")
                return
            config_columns.append(name)
            unique_values[name] = domain

        if not config_columns:
            messagebox.showerror("Invalid input", "Add at least one configuration column.")
            return

        self.config_columns = config_columns
        self.unique_values = unique_values
        self.budget = budget
        self.maximize = (self.obj_var.get() == 'max')
        self.algo_code = self.algo_var.get()
        self.algo_name = ALGORITHMS[self.algo_code][0]

        self._build_run_view()
        self._start_algorithm()

    # ---- Run view ----
    def _build_run_view(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title(f"Running {self.algo_name}")

        info = ttk.Frame(self.root, padding=10)
        info.pack(fill='x')
        self.iter_label = ttk.Label(info, text="Iteration: 0 / 0", font=('TkDefaultFont', 11, 'bold'))
        self.iter_label.pack(side='left', padx=8)
        self.best_label = ttk.Label(info, text="Best so far: —")
        self.best_label.pack(side='left', padx=8)

        prompt = ttk.LabelFrame(self.root, text="Test this configuration", padding=10)
        prompt.pack(fill='x', padx=10, pady=5)

        self.config_text = tk.Text(prompt, height=8, width=60, state='disabled')
        self.config_text.pack(fill='x')

        entry_row = ttk.Frame(prompt)
        entry_row.pack(fill='x', pady=(8, 0))
        ttk.Label(entry_row, text="Measured performance:").pack(side='left')
        self.perf_var = tk.StringVar()
        self.perf_entry = ttk.Entry(entry_row, textvariable=self.perf_var, width=15)
        self.perf_entry.pack(side='left', padx=5)
        self.perf_entry.bind('<Return>', lambda e: self._submit_performance())

        self.submit_btn = ttk.Button(entry_row, text="Submit", command=self._submit_performance)
        self.submit_btn.pack(side='left', padx=4)

        self.invalid_btn = ttk.Button(entry_row, text="Invalid/Skip", command=self._mark_invalid)
        self.invalid_btn.pack(side='left', padx=4)

        hist_frame = ttk.LabelFrame(self.root, text="History", padding=5)
        hist_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.history_box = tk.Text(hist_frame, height=10, state='disabled')
        self.history_box.pack(fill='both', expand=True, side='left')
        sb = ttk.Scrollbar(hist_frame, command=self.history_box.yview)
        sb.pack(side='right', fill='y')
        self.history_box.config(yscrollcommand=sb.set)

    def _start_algorithm(self):
        algo_fn = ALGORITHMS[self.algo_code][1]
        self.gen = algo_fn(self.unique_values, self.config_columns, self.budget, maximize=self.maximize)
        self.history = []
        self.best_solution = self.best_performance = None
        self.iteration = 0
        self.valid_evals = 0
        self._processing = False
        self._advance(None)

    def _set_buttons(self, state):
        """Enable/disable Submit and Invalid buttons."""
        self.submit_btn.config(state=state)
        self.invalid_btn.config(state=state)

    def _advance(self, perf):
        try:
            self.current_config = next(self.gen) if perf is None else self.gen.send(perf)
        except StopIteration as e:
            _, _, history = e.value
            self.history = history
            self._show_results()
            return

        self.iteration += 1
        self.iter_label.config(text=f"Iteration: {self.iteration} / {self.budget}")
        self._render_config(self.current_config)
        self.perf_var.set('')
        self._set_buttons('normal')
        self._processing = False
        self.root.update_idletasks()
        self.perf_entry.focus_set()

    def _render_config(self, config):
        text = '\n'.join(f"  {col} = {val}" for col, val in zip(self.config_columns, config))
        self.config_text.config(state='normal')
        self.config_text.delete('1.0', 'end')
        self.config_text.insert('1.0', text)
        self.config_text.config(state='disabled')

    def _submit_performance(self):
        if self._processing:
            return

        try:
            perf = float(self.perf_var.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Performance must be a number.")
            return

        self._processing = True
        self._set_buttons('disabled')

        is_better = (lambda n, r: n > r) if self.maximize else (lambda n, r: n < r)
        if self.best_performance is None or is_better(perf, self.best_performance):
            self.best_performance = perf
            self.best_solution = list(self.current_config)
        self.best_label.config(text=f"Best so far: {self.best_performance}")

        self.valid_evals += 1
        self._append_history_line(self.iteration, self.current_config, perf)
        self._advance(perf)

    def _mark_invalid(self):
        """Mark current config as invalid and send penalty to generator."""
        if self._processing:
            return

        self._processing = True
        self._set_buttons('disabled')

        penalty = INVALID_PERF[self.maximize]
        config_str = ', '.join(f"{c}={v}" for c, v in zip(self.config_columns, self.current_config))
        line = f"Iter {self.iteration:>3}: [{config_str}] -> INVALID\n"
        self.history_box.config(state='normal')
        self.history_box.insert('end', line)
        self.history_box.see('end')
        self.history_box.config(state='disabled')

        self._advance(penalty)

    def _append_history_line(self, iteration, config, perf):
        config_str = ', '.join(f"{c}={v}" for c, v in zip(self.config_columns, config))
        self.history_box.config(state='normal')
        self.history_box.insert('end', f"Iter {iteration:>3}: [{config_str}] -> {perf}\n")
        self.history_box.see('end')
        self.history_box.config(state='disabled')

    # ---- Results view ----
    def _show_results(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title("Search Complete")

        frm = ttk.Frame(self.root, padding=15)
        frm.pack(fill='both', expand=True)

        ttk.Label(frm, text="Search Complete", font=('TkDefaultFont', 14, 'bold')).pack(anchor='w')
        ttk.Label(frm, text=f"Algorithm: {self.algo_name}").pack(anchor='w')
        ttk.Label(frm, text=f"Objective: {'Maximize' if self.maximize else 'Minimize'}").pack(anchor='w')
        ttk.Label(frm, text=f"Evaluations: {len(self.history)} ({self.valid_evals} valid)").pack(anchor='w')

        ttk.Separator(frm).pack(fill='x', pady=8)
        ttk.Label(frm, text="Best Configuration:", font=('TkDefaultFont', 11, 'bold')).pack(anchor='w')
        if self.best_solution:
            for col, val in zip(self.config_columns, self.best_solution):
                ttk.Label(frm, text=f"  {col} = {val}").pack(anchor='w')
            ttk.Label(frm, text=f"Best Performance: {self.best_performance}",
                      font=('TkDefaultFont', 11, 'bold')).pack(anchor='w', pady=(8, 0))
        else:
            ttk.Label(frm, text="  No valid configuration found.", foreground='red').pack(anchor='w')

        acts = ttk.Frame(frm)
        acts.pack(fill='x', pady=15)
        ttk.Button(acts, text="Save Trace as CSV", command=self._save_trace, width=15).pack(side='left', padx=2)
        ttk.Button(acts, text="New Search", command=self._build_setup_view, width=15).pack(side='left', padx=2)
        ttk.Button(acts, text="Close", command=self.root.destroy, width=15).pack(side='right', padx=2)

    def _save_trace(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv')],
            initialfile=f"gui_{self.algo_code}_trace.csv",
        )
        if not path:
            return
        df = pd.DataFrame(self.history, columns=self.config_columns + ['Performance'])
        df.to_csv(path, index=False)
        messagebox.showinfo("Saved", f"Trace saved to {path}")


def launch_gui():
    root = tk.Tk()
    ConfigTunerGUI(root)
    root.mainloop()


if __name__ == '__main__':
    launch_gui()
