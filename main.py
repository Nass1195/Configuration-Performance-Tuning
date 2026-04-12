import pandas as pd
import numpy as np
import random
import os
import matplotlib.pyplot as plt
from scipy import stats
from baseline.main import random_search
import seaborn as sns

def evolutionary_algo(file_path, budget, output_file):
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

    os.makedirs(output_folder, exist_ok=True)
    results = {}
    summaries = []


    for file_name in os.listdir(datasets_folder):
        
        if file_name.endswith(".csv"):
            dataset_name = file_name.split('.')[0]
            print(f"\n======================================")
            print(f"Testing Dataset: {dataset_name}")
            print(f"======================================")
            file_path = os.path.join(datasets_folder, file_name)
            output_file = os.path.join(output_folder, f"{file_name.split('.')[0]}_search_results.png")
            algo_results, summary = compare_algorithms(file_path, output_file, budget=1000, runs=30)
            results[dataset_name] = algo_results
            summaries.append(summary)

        
   


def compare_algorithms(file_path, output_file, budget=100, runs=30):
    
    rs_results = []
    sa_results = []
    ga_results = []

    for i in range(runs):
        
        _, rs_perf = random_search(file_path, budget, f"rs_temp.csv")
        _, sa_perf = SA(file_path, budget, f"sa_temp.csv")
        _, ga_perf = evolutionary_algo(file_path, budget, f"ga_temp.csv")

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

  
    plt.figure(figsize=(8, 6))
    plt.boxplot([rs_results, sa_results, ga_results], labels=['Random Search', 'Simulated Annealing', 'Genetic Algorithm'])
    plt.title(f'Performance Comparison ({runs} Runs, Budget={budget})')
    plt.ylabel('Best Performance Found (Lower is Better)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(output_file)
    print("\nSaved boxplot to 'algorithm_comparison.png'")
    summary = {
        'Dataset': file_path.split('/')[-1].split('.')[0],
        'RS_Mean': np.mean(rs_results),
        'SA_Mean': np.mean(sa_results),
        'GA_Mean': np.mean(ga_results),
        'SA_Beats_RS (p < 0.05)': p_sa < 0.05,
        'GA_Beats_RS (p < 0.05)': p_ga < 0.05,
        'SA vs RS p-value': p_sa,
        'GA vs RS p-value': p_ga,
        'SA vs GA p-value': p_sa_ga
    }

    return results, summary



if __name__ == "__main__":
    main()
