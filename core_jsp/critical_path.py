def optimized_find_critical_path_duplicate(simulated_path, critical_star, stds_star, n_activties):
    # Read and process the data
    df = pd.read_csv(simulated_path)

    # Precompute durations
    df['duration'] = df['end_time'] - df['start_time']
    df['start_node'] = list(zip(df['id_job'], df['resource'], ['start'] * len(df), range(len(df))))
    df['finish_node'] = list(zip(df['id_job'], df['resource'], ['finish'] * len(df), range(len(df))))

    # Sort the DataFrame by start_time to restrict comparisons
    df = df.sort_values(by='start_time').reset_index(drop=True)

    # Initialize the graph
    G = nx.DiGraph()

    # Add all nodes (start and finish) to the graph
    for index, row in df.iterrows():
        G.add_node(row['start_node'], weight=0, std=row['wip_start'])
        G.add_node(row['finish_node'], weight=row['duration'])

    # Add task edges (start -> finish for the same task)
    edges = [(row['start_node'], row['finish_node'], row['duration']) for _, row in df.iterrows()]
    G.add_weighted_edges_from(edges, weight='weight')

    # Add dependency edges
    for i in range(len(df)):
        finish_node = df.iloc[i]['finish_node']
        end_time = df.iloc[i]['end_time']

        # Only compare tasks that start after the current task's end_time
        possible_dependencies = df[df['start_time'] >= end_time]
        for _, dep_row in possible_dependencies.iterrows():
            G.add_edge(finish_node, dep_row['start_node'], weight=0)

    # Calculate the longest path
    try:
        length = nx.dag_longest_path_length(G, weight='weight')
        path = nx.dag_longest_path(G, weight='weight')
    except nx.NetworkXUnfeasible:
        raise ValueError("Graph contains a cycle, check your input data")

    if length > critical_star:
        # Extract the critical path and retrieve attributes
        critical_path = []
        critical_path_attributes = []
        for i in range(0, len(path) - 1, 2):  # Skip the 'finish' nodes
            critical_path.append(path[i][0])  # Append the id_job
            attributes = G.nodes[path[i]]
            critical_path_attributes.append(attributes)

        stds_star = [act['std'] for act in critical_path_attributes]
        critical_star = length
        n_activties = len(stds_star)

    return critical_star, stds_star, n_activties