import pandas as pd
import numpy as np
import random
import os

def SA(file_path, budget, output_file):

    data = pd.read_csv(file_path)

    config_columns = data.columns[:-1]
    performance_column = data.columns[-1]

    best_performance = np.inf
    best_solution = []

    search_results = []
    
    temp = 100

    colling_rate = 0.99

    iteration = 0

    while True:
        sampled_config = [int(np.random.choice(data[col].unique())) for col in config_columns]
        matched_row = data.loc[(data[config_columns] == pd.Series(sampled_config, index=config_columns)).all(axis=1)]

        if not matched_row.empty:
            best_performance = matched_row[performance_column].iloc[0]
            best_solution = sampled_config
            break
    
    current_solution = best_solution
    current_performance = best_performance

    while iteration < budget:
        new_solution = list(current_solution)
        num_changes = min(len(config_columns), 1)
        selected_indices = random.sample(range(len(config_columns)), num_changes)
        for idx in selected_indices:
            column_to_change = config_columns[idx]
            changed_value = int(np.random.choice(data[column_to_change].unique()))
            new_solution[idx] = changed_value

        

        matched_row = data.loc[(data[config_columns] == pd.Series(new_solution, index=config_columns)).all(axis=1)]

        if not matched_row.empty:
            performance = matched_row[performance_column].iloc[0]

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

    budget = 100

    results = {}
    for file_name in os.listdir(datasets_folder):
        if file_name.endswith(".csv"):
            file_path = os.path.join(datasets_folder, file_name)
            output_file = os.path.join(output_folder, f"{file_name.split('.')[0]}_search_results.csv")
            best_solution, best_performance = SA(file_path, budget, output_file)
            results[file_name] = {
                "Best Solution": best_solution,
                "Best Performance": best_performance
            }
            

    for system, result in results.items():
        print(f"System: {system}")
        print(f"  Best Solution:    [{', '.join(map(str, result['Best Solution']))}]")
        print(f"  Best Performance: {result['Best Performance']}")


if __name__ == "__main__":
    main()
