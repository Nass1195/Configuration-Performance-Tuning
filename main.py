import pandas as pd
import numpy as np
import random
import os
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns

# Define the random search function
def random_search(file_path, budget, output_file):
    # Load the dataset
    data = pd.read_csv(file_path)

    # Identify the columns for configurations and performance
    config_columns = data.columns[:-1]
    performance_column = data.columns[-1]

    # Determine if this is a maximization or minimization problem
    # maximize throughput and minimize runtime
    system_name = os.path.basename(file_path).split('.')[0]
    if system_name.lower() == "---":
        maximization = True
    else:
        maximization = False

    # Extract the best and worst performance values
    if maximization:
        worst_value = data[performance_column].min() / 2  # For missing configurations
    else:
        worst_value = data[performance_column].max() * 2  # For minssing configrations

    # Initialize the best solution and performance
    best_performance = -np.inf if maximization else np.inf
    best_solution = []

    # Store all search results
    search_results = []

    for _ in range(budget):
        # Randomly sample a configuration
        # For each configuration column, randomly select a value from the unique values available in the dataset
        # This ensures that the sampled configuration is within the valid domain of each parameter
        sampled_config = [int(np.random.choice(data[col].unique())) for col in config_columns]

        # Check if the configuration exists in the dataset
        # Create a Pandas Series from the sampled configuration and match it against all rows in the dataset
        # The .all(axis=1) ensures that the match is applied across all configuration columns
        matched_row = data.loc[(data[config_columns] == pd.Series(sampled_config, index=config_columns)).all(axis=1)]

        if not matched_row.empty:
            # Existing configuration
            performance = matched_row[performance_column].iloc[0]
        else:
            # Non-existing configuration
            performance = worst_value

        # Update the best solution
        if maximization:
            if performance > best_performance:
                best_performance = performance
                best_solution = sampled_config
        else:
            if performance < best_performance:
                best_performance = performance
                best_solution = sampled_config

        # Record the current search result
        search_results.append(sampled_config + [performance])

    # Save the search results to a CSV file
    columns = list(config_columns) + ["Performance"]
    search_df = pd.DataFrame(search_results, columns=columns)
    search_df.to_csv(output_file, index=False)

    return [int(x) for x in best_solution], best_performance

def genetic_algorithm(file_path, budget, output_file):
    data = pd.read_csv(file_path)

    config_columns = list(data.columns[:-1])
    performance_column = data.columns[-1]
    
    data_dict = data.set_index(config_columns)[performance_column].to_dict()
    unique_values = {col: data[col].unique() for col in config_columns}

    search_results = []

    pop_size = max(5, budget // 5)

    pop = []
    performances = []

    while len(pop) < pop_size:
        config = tuple(int(random.choice(unique_values[col])) for col in config_columns)
        if config in data_dict:
            pop.append(config)
            performances.append(data_dict[config])
            search_results.append(list(config) + [data_dict[config]])

    best_performance = min(performances)
    best_idx = performances.index(best_performance)
    best_individual = list(pop[best_idx])

    iteration = len(pop)
    while iteration < budget:

        t1, t2 = random.sample(range(pop_size), 2)
        p1 = pop[t1] if performances[t1] < performances[t2] else pop[t2]

        t3, t4 = random.sample(range(pop_size), 2)
        p2 = pop[t3] if performances[t3] < performances[t4] else pop[t4]


        child = [p1[i] if random.random() < 0.5 else p2[i] for i in range(len(config_columns))]

        
        mut_idx = random.randint(0, len(config_columns) - 1)
        col_name = config_columns[mut_idx]
        child[mut_idx] = int(random.choice(unique_values[col_name]))

        child_tuple = tuple(child)
        perf = data_dict.get(child_tuple)

        if perf is not None:
            worst_idx = performances.index(max(performances))
            pop[worst_idx] = child
            performances[worst_idx] = perf
            if perf < best_performance:
                best_performance = perf
                best_individual = list(child)
            iteration += 1
            search_results.append(child + [perf])
        
    columns = config_columns + ["Performance"]
    pd.DataFrame(search_results, columns=columns).to_csv(output_file, index=False)

    return best_individual, best_performance


def SA(file_path, budget, output_file):

    data = pd.read_csv(file_path)

    config_columns = list(data.columns[:-1])
    performance_column = data.columns[-1]
    
    data_dict = data.set_index(config_columns)[performance_column].to_dict()
    unique_values = {col: data[col].unique() for col in config_columns}

    search_results = []
    
    while True:
        sampled_config = tuple(int(np.random.choice(unique_values[col])) for col in config_columns)
        if sampled_config in data_dict:
            best_performance = data_dict[sampled_config]
            best_solution = list(sampled_config)
            break
    
    current_solution = best_solution
    current_performance = best_performance

    temp = max(1.0, current_performance * 0.2)
    colling_rate = 0.98
    iteration = 1

    num_of_changes = max(min(3, len(config_columns) // 2), 1)
    while iteration < budget:

        new_solution = list(current_solution)

        changes = random.sample(range(len(config_columns)), num_of_changes)
        for idx in changes:
            column_to_change = config_columns[idx]
            possible_values = [v for v in unique_values[column_to_change] if v != current_solution[idx]]
            new_solution[idx] = int(random.choice(possible_values))

        new_solution_tuple = tuple(new_solution)
       
        performance = data_dict.get(new_solution_tuple)

        if performance is not None:
            performance_delta = performance - current_performance
            
            if performance_delta < 0 or np.random.rand() < np.exp(-performance_delta / temp):
                current_solution = new_solution
                current_performance = performance

                if current_performance < best_performance:
                    best_solution = list(current_solution)
                    best_performance = current_performance

            temp *= colling_rate
            iteration += 1
            search_results.append(new_solution + [performance])

    columns = list(config_columns) + ["Performance"]
    search_df = pd.DataFrame(search_results, columns=columns)
    search_df.to_csv(output_file, index=False)

    return [int(x) for x in best_solution], best_performance


def main():
    datasets_folder = "datasets"
    output_folder = "search_results"
    SA_results_folder = "sa_results"
    GA_results_folder = "ga_results"
    RS_results_folder = "rs_results"

    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(SA_results_folder, exist_ok=True)
    os.makedirs(GA_results_folder, exist_ok=True)
    os.makedirs(RS_results_folder, exist_ok=True)
    results = {}
    summaries = []


    for file_name in os.listdir(datasets_folder):
        
        if file_name.endswith(".csv"):
            dataset_name = file_name.split('.')[0]
            print(f"\n======================================")
            print(f"Testing Dataset: {dataset_name}")
            print(f"======================================")
            sa_results_file = SA_results_folder + f"/{dataset_name}"
            ga_results_file = GA_results_folder + f"/{dataset_name}"
            rs_results_file = RS_results_folder + f"/{dataset_name}"
            os.makedirs(sa_results_file, exist_ok=True)
            os.makedirs(ga_results_file, exist_ok=True)
            os.makedirs(rs_results_file, exist_ok=True)
            file_path = os.path.join(datasets_folder, file_name)
            output_file = os.path.join(output_folder, f"{file_name.split('.')[0]}_search_results.png")
            algo_results, summary = compare_algorithms(file_path, output_file, sa_results_file, ga_results_file, rs_results_file, budget=100, runs=30)
            results[dataset_name] = algo_results
            summaries.append(summary)

        
    generate_global_report(summaries, output_folder)


def compare_algorithms(file_path, output_file, sa_results_path, ga_results_path, rs_results_path, budget=100, runs=30):
    
    rs_results = []
    sa_results = []
    ga_results = []

    for i in range(runs):

        rs_results_file = rs_results_path + f"/run_{i+1}.csv"
        sa_results_file = sa_results_path + f"/run_{i+1}.csv"
        ga_results_file = ga_results_path + f"/run_{i+1}.csv"

        _, rs_perf = random_search(file_path, budget, rs_results_file)
        _, sa_perf = SA(file_path, budget, sa_results_file)
        _, ga_perf = genetic_algorithm(file_path, budget, ga_results_file)

        rs_results.append(rs_perf)
        sa_results.append(sa_perf)
        ga_results.append(ga_perf)
        
        if (i + 1) % 5 == 0:
            print(f"Completed {i + 1}/{runs} runs...")
    
    results = {
        'RS': rs_results, 'SA': sa_results, 'GA': ga_results
    }
   
    print("\n--- RESULTS SUMMARY (Lower is Better) ---")
    print(f"Random Search (Baseline): Mean = {np.mean(rs_results):.2f}, Median = {np.median(rs_results):.2f}")
    print(f"Simulated Annealing:      Mean = {np.mean(sa_results):.2f}, Median = {np.median(sa_results):.2f}")
    print(f"Genetic Algorithm:        Mean = {np.mean(ga_results):.2f}, Median = {np.median(ga_results):.2f}")

   
    print("\n--- STATISTICAL TESTS (p-value < 0.05 means significantly better) ---")
    
    
    stat, p_sa = stats.mannwhitneyu(sa_results, rs_results, alternative='less')
    print(f"SA vs Random Search p-value: {p_sa:.4e} -> {'SA is significantly better' if p_sa < 0.05 else 'No significant difference'}")

   
    stat, p_ga = stats.mannwhitneyu(ga_results, rs_results, alternative='less')
    print(f"GA vs Random Search p-value: {p_ga:.4e} -> {'GA is significantly better' if p_ga < 0.05 else 'No significant difference'}")

    
    stat, p_sa_ga = stats.mannwhitneyu(sa_results, ga_results, alternative='less')
    print(f"SA vs GA p-value: {p_sa_ga:.4e} -> {'SA is significantly better than GA' if p_sa_ga < 0.05 else 'GA is better or no difference'}")

    stat, p_ga_sa = stats.mannwhitneyu(ga_results, sa_results, alternative='less')
    print(f"GA vs SA p-value: {p_ga_sa:.4e} -> {'GA is significantly better than SA' if p_ga_sa < 0.05 else 'SA is better or no difference'}")

  
    plt.figure(figsize=(8, 6))
    results_data = [rs_results, sa_results, ga_results]
    labels = ["Random Search", "Simulated Annealing", "Genetic Algorithm"]
    for line, label in zip(results_data, labels):
        plt.plot(line, marker='o', linestyle='-', alpha=0.5, label=label)
    plt.title(f'Performance Comparison ({runs} Runs, Budget={budget})')
    plt.ylabel('Best Performance Found (Lower is Better)')
    plt.xlabel('Run Number')
    plt.legend()
    plt.savefig(output_file)
    summary = {
        'Dataset': file_path.split('/')[-1].split('.')[0],
        'RS_Median': np.median(rs_results),
        'SA_Median': np.median(sa_results),
        'GA_Median': np.median(ga_results),
        'SA_Beats_RS (p < 0.05)': p_sa < 0.05,
        'GA_Beats_RS (p < 0.05)': p_ga < 0.05,
        'SA vs RS p-value': p_sa,
        'GA vs RS p-value': p_ga,
        'SA vs GA p-value': p_sa_ga,
        'GA vs SA p-value': p_ga_sa
    }

    return results, summary

def generate_global_report(summaries, output_folder):
    """
    Takes the list of summary dictionaries and creates global visualizations.
    """
    if not summaries:
        print("No summaries to visualize.")
        return

    df = pd.DataFrame(summaries)
    df.set_index('Dataset', inplace=True)
    
    csv_path = os.path.join(output_folder, "global_summary_report.csv")
    df.to_csv(csv_path)
    print(f"\nSaved global statistical summary to '{csv_path}'")


    plt.figure(figsize=(10, len(df) * 0.5 + 3)) 
    
    median_cols = ['RS_Median', 'SA_Median', 'GA_Median']
    medians_df = df[median_cols]
    
    normalized_df = (medians_df.T - medians_df.min(axis=1)) / (medians_df.max(axis=1) - medians_df.min(axis=1) + 1e-9)
    normalized_df = normalized_df.T 

    print(normalized_df)
    sns.heatmap(normalized_df, cmap="YlGnBu", cbar_kws={'label': 'Normalized Performance (Lighter/Yellower is Better)'})
    plt.title("Algorithm Median Performance Across Datasets")
    plt.ylabel("Dataset")
    plt.xlabel("Algorithm")
    plt.tight_layout()
    heatmap_path = os.path.join(output_folder, "global_performance_heatmap.png")
    plt.savefig(heatmap_path)
    

    plt.figure(figsize=(8, 5))
    wins = medians_df.idxmin(axis=1)
    
    win_labels = wins.map({'RS_Median': 'Random Search', 'SA_Median': 'Simulated Annealing', 'GA_Median': 'Genetic Algorithm'})
    win_counts = win_labels.value_counts()
    
    for algo in ['Random Search', 'Simulated Annealing', 'Genetic Algorithm']:
        if algo not in win_counts:
            win_counts[algo] = 0

    ax = win_counts.plot(kind='bar', color=['#95a5a6', '#e74c3c', '#2ecc71'], edgecolor='black')
    plt.title("Algorithm 'Wins' (Lowest Median per Dataset)")
    plt.ylabel("Number of Datasets Won")
    plt.xticks(rotation=0)
    
   
    for p in ax.patches:
        ax.annotate(str(p.get_height()), (p.get_x() * 1.005, p.get_height() * 1.005))
        
    plt.tight_layout()
    bar_path = os.path.join(output_folder, "global_win_distribution.png")
    plt.savefig(bar_path)
    print(f"Saved global visualizations to '{output_folder}' directory.")

    p_val_cols = ['SA vs RS p-value', 'GA vs RS p-value', 'SA vs GA p-value', 'GA vs SA p-value']
    p_val_df = df[p_val_cols]

    sig_counts = (p_val_df < 0.05).sum()

    new_labels = [f"{col}\n(sig: {sig_counts[col]}/{len(p_val_df)})" for col in p_val_cols]

    plt.figure(figsize=(8, len(df) * 0.6 + 2))

    sns.heatmap(p_val_df, 
                cmap="RdYlGn_r",    
                vmin=0.0, 
                vmax=0.1,           
                linewidths=0.5,
                xticklabels=new_labels,
                cbar_kws={'label': 'p-value (Green indicates p < 0.05)'})
    
    plt.title('Algorithm Comparison P-Values per Dataset')
    plt.ylabel('Datasets')
    plt.xlabel('Statistical Tests (Alternative = Less)')
    
    # Adjust layout and save
    plt.tight_layout()
    heatmap_path = f"{output_folder}/p_values_heatmap.png"
    plt.savefig(heatmap_path)
    plt.close()

if __name__ == "__main__":
    main()
