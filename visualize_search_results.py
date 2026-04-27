import matplotlib.pyplot as plt
import pandas as pd
import os


def visualize_search_results(results_folder, dataset_name):
    """
    Visualize the search results from stored CSV results.

    Parameters:
        results_folder (str): Folder containing the search results CSV files.
        dataset_name (str): Name of the dataset to visualize (without extension).
        visualization_folder (str): Folder to save the visualization images.
    """

    plt.figure(figsize=(10, 6))

    for file in os.listdir(results_folder):
        if file.endswith(".csv"):
            csv_file = os.path.join(results_folder, file)
            output_image = os.path.join(results_folder, f"{dataset_name}_visualization.png")
            search_df = pd.read_csv(csv_file)

            plt.plot(search_df.index, search_df["Performance"], linestyle="-")


    plt.xlabel("Search Iteration", fontsize=14)
    plt.ylabel("Performance", fontsize=14)
    plt.title(f"Search Results Visualization for {dataset_name}", fontsize=16)
    plt.legend()


    plt.savefig(output_image)


def main():
    """
    Main function to generate visualizations for all datasets in the results folder.
    """
    sa_folder = "sa_results"
    ga_folder = "ga_results"
    rs_folder = "rs_results"

    visualization_folder = "visualization_results"

    if not os.path.exists(sa_folder):
        print(f"Error: The folder {sa_folder} does not exist.")
        return
    if not os.path.exists(ga_folder):
        print(f"Error: The folder {ga_folder} does not exist.")
        return
    if not os.path.exists(rs_folder):
        print(f"Error: The folder {rs_folder} does not exist.")
        return
    
    for folder in [sa_folder, ga_folder, rs_folder]:
        for dataset_folder in os.listdir(folder):
            dataset_name = dataset_folder
            dataset_folder = os.path.join(folder, dataset_folder)
            visualize_search_results(dataset_folder, dataset_name)


if __name__ == "__main__":
    main()
