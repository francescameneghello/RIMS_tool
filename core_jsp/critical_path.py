import pandas as pd
import networkx as nx

def find_critical_path(simulated_path, critical_star, stds_star):
    # Read and process the data
    data = pd.read_csv(simulated_path)
    data = {
        'id_job': list(data['id_job']),
        'resource': list(data['resource']),
        'start_time': list(data['start_time']),
        'end_time': list(data['end_time']),
        'std': list(data['wip_start'])
    }
    df = pd.DataFrame(data)
    G = nx.DiGraph()

    # Add nodes and edges with unique identifiers
    for index, row in df.iterrows():
        # Use index as a unique identifier for tasks
        start_node = (row['id_job'], row['resource'], 'start', index)
        finish_node = (row['id_job'], row['resource'], 'finish', index)
        duration = row['end_time'] - row['start_time']

        G.add_node(start_node, weight=0, std=row['std'])
        G.add_node(finish_node, weight=duration)
        G.add_edge(start_node, finish_node, weight=duration)

        # Create dependencies between tasks
        for other_index, other_row in df.iterrows():
            if row['end_time'] <= other_row['start_time']:
                finish_node = (row['id_job'], row['resource'], 'finish', index)
                other_start_node = (other_row['id_job'], other_row['resource'], 'start', other_index)
                G.add_edge(finish_node, other_start_node, weight=0)

    # Calculate the longest path
    try:
        length = nx.dag_longest_path_length(G, weight='weight')
        path = nx.dag_longest_path(G, weight='weight')
    except nx.NetworkXUnfeasible:
        raise ValueError("Graph contains a cycle, check your input data")

    #if length > critical_star:
        # Extract the critical path and retrieve attributes
    critical_path = []
    critical_path_attributes = []
    for i in range(0, len(path) - 1, 2):  # Skip the 'finish' nodes
        critical_path.append(path[i][0])  # Append the id_job
        attributes = G.nodes[path[i]]
        critical_path_attributes.append(attributes)

    stds_star = [act['std'] for act in critical_path_attributes]
    critical_star = length

    return critical_star, stds_star

critical_star, stds_star = 0, []

simulated_path = '/Users/francescameneghello/Documents/GitHub/RIMS_tool/core_jsp/output/output_simple_example/simulated_log_simple_example.csv'
find_critical_path(simulated_path, critical_star, stds_star)