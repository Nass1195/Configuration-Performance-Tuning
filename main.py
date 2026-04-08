import pandas as pd
import numpy as np
import random
import os


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

        if random.random() < 0.2:
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
    output_folder1 = "search_results1"

    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(output_folder1, exist_ok=True)


    budget = 100

    results = {}
    for file_name in os.listdir(datasets_folder):
        if file_name.endswith(".csv"):
            file_path = os.path.join(datasets_folder, file_name)
            output_file = os.path.join(output_folder, f"{file_name.split('.')[0]}_search_results.csv")
            output_file1 = os.path.join(output_folder1, f"{file_name.split('.')[0]}_search_results.csv")
            best_solution1, best_performance1 = evolutionary_algo(file_path, budget, output_file1)
            best_solution, best_performance = SA(file_path, budget, output_file)
            results[file_name] = {
                "Best Solution": best_solution,
                "Best Performance": best_performance,
                "Best Solution (EA)": best_solution1,
                "Best Performance (EA)": best_performance1
            }
            

    for system, result in results.items():
        print(f"System: {system}")
        print(f"  Best Solution:    [{', '.join(map(str, result['Best Solution']))}]")
        print(f"  Best Performance: {result['Best Performance']}")
        print(f"  Best Solution (EA):    [{', '.join(map(str, result['Best Solution (EA)']))}]")
        print(f"  Best Performance (EA): {result['Best Performance (EA)']}")

if __name__ == "__main__":
    main()
