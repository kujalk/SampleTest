from dash import State, Input, Output, Dash
import dash_cytoscape as cyto
from dash import html
import networkx as nx

app = Dash(__name__)

# Define the nodes and edges of the graph
elements = [
    {'data': {'id': 'A'}},
    {'data': {'id': 'B'}},
    {'data': {'id': 'C'}},
    {'data': {'id': 'D'}},
    {'data': {'id': 'E'}},
    {'data': {'id': 'AB', 'source': 'A', 'target': 'B'}},
    {'data': {'id': 'BC', 'source': 'B', 'target': 'C'}},
    {'data': {'id': 'CD', 'source': 'C', 'target': 'D'}},
    {'data': {'id': 'DE', 'source': 'D', 'target': 'E'}},
    {'data': {'id': 'AC', 'source': 'A', 'target': 'C'}},
    {'data': {'id': 'CE', 'source': 'C', 'target': 'E'}}
]

# Define the styles for the nodes and edges
# Define the styles for the nodes and edges
styles = [
    {
        'selector': 'node',
        'style': {
            'label': 'data(id)',
            'background-color': '#ddd',
            'border-color': '#555',
            'border-width': '1px',
            'width': '50px',
            'height': '50px'
        }
    },
    {
        'selector': 'edge',
        'style': {
            'width': 2,
            'line-color': '#ccc'
        }
    },
    {
        'selector': 'node:selected',
        'style': {
            'border-color': 'purple',
            'border-width': '3px'
        }
    },
    {
        'selector': 'edge:selected',
        'style': {
            'line-color': 'purple',
            'width': 3
        }
    }
]


# Define the layout of the graph
layout = {'name': 'cose'}

# Create a NetworkX graph from the elements
G = nx.DiGraph()
for element in elements:
    if 'source' in element['data'] and 'target' in element['data']:
        G.add_edge(element['data']['source'], element['data']['target'])

# Define the app layout
app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape',
        elements=elements,
        style={'height': '500px'},
        stylesheet=styles,
        layout=layout
    )
])

# Define a callback that highlights the shortest path between two nodes


@app.callback(
    Output('cytoscape', 'stylesheet'),
    Input('cytoscape', 'selectedNodeData'),
    State('cytoscape', 'elements')
)
def highlight_path(node, elements):
    if node is None or len(node) < 2:
        return styles

    source_id = node[-1]['id']
    target_id = node[-2]['id']

    # Use NetworkX to compute the shortest path
    try:
        shortest_path = nx.shortest_path(G, source_id, target_id)
    except:
        try:
            shortest_path = nx.shortest_path(G, target_id, source_id)
        except:
            return styles

    print(f"Path -> {shortest_path}")

    # Create a dictionary that maps the node and edge IDs along the shortest path to their respective style objects
    style = {
        node_id: {'background-color': 'orange', 'border-color': 'orange'}
        for node_id in shortest_path
    }

    # Create a dictionary that maps the edge IDs along the shortest path to their respective style objects
    edge_style = {}
    for i in range(len(shortest_path)-1):
        source_node = shortest_path[i]
        target_node = shortest_path[i+1]
        edge_id = f'{source_node}{target_node}'
        edge_style[edge_id] = {'line-color': 'red'}

    # Update the style dictionary with the edge styles
    style.update(edge_style)

    style_dict = [{
        'selector': f'#{element["data"]["id"]}',
        'style': style.get(element['data']['id'], {})
    } for element in elements]

    styles_copy = styles.copy()
    styles_copy.extend(style_dict)

    return styles_copy


if __name__ == '__main__':
    app.run_server(debug=True)
