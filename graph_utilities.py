import numpy as np
import pandas as pd
import networkx as nx

# import json
# import matplotlib.pyplot as plt


def create_graphdf(data):
    nodedf = pd.DataFrame(data['nodes'], columns=['x', 'y', 'id'])
    edgedf = pd.DataFrame(data['edges'], columns=['source', 'target', 'id'])
    return (edgedf,nodedf)



def generate_clusters(edges, nodedata):
    protein_g = nx.from_pandas_edgelist(edges, 'source', 'target', True, nx.Graph())
    nx.set_node_attributes(protein_g, nodedata.set_index('id').to_dict('index'))

    subgraphs = []
    components = nx.connected_components(protein_g)
    column_names = ['id', 'x', 'y']

    for component in components:
        coord = pd.DataFrame(np.array([(n, v['x'], v['y']) for n, v in protein_g.nodes(data=True) if n in component]),
                             columns=column_names)
        coord['x'] = pd.to_numeric(coord['x'])
        coord['y'] = pd.to_numeric(coord['y'])
        coord['id'] = pd.to_numeric(coord['id'])
        coord['subCentreX'] = coord['x'].sum()/len(coord)
        coord['subCentreY'] = coord['y'].sum()/len(coord)
        subgraphs.append(coord)

    return pd.concat(subgraphs)



def adjust_points(graphdata):

    graphdata['centreX'] = graphdata['subCentreX'].unique().sum() / graphdata['subCentreX'].nunique()
    graphdata['centreY'] = graphdata['subCentreY'].unique().sum() / graphdata['subCentreY'].nunique()
    graphdata['newCX'] = (3*graphdata['centreX'] + graphdata['subCentreX']) / 4
    graphdata['newCY'] = (3*graphdata['centreY'] + graphdata['subCentreY']) / 4

    graphdata['x'] = graphdata['x'] + (graphdata['newCX'] - graphdata['subCentreX'])
    graphdata['y'] = graphdata['y'] + (graphdata['newCY'] - graphdata['subCentreY'])

    return graphdata[['x', 'y', 'id']]


# def plot_this_graph(graphdata):
#     plt.plot(graphdata['x'], graphdata['y'], 'ro')
#     plt.show()
#
# with open('sample.json') as f:
#     data = json.load(f)
#
# edges,nodes = create_graphdf(data)
# clusters = generate_clusters(edges,nodes)
# newCoordinates = adjust_points(clusters)
# plot_this_graph(newCoordinates)
