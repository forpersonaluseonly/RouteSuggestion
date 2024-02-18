from flask import Flask, render_template, request, send_from_directory
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import os

app = Flask(__name__)

# Define the directory to save images
app.config['UPLOAD_FOLDER'] = 'static/images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Create the directory if it doesn't exist

# Load your own .osm file
G = ox.graph_from_xml(r"map.osm")

@app.route('/')
def display_map():
    return render_template('map.html', image_data="")

@app.route('/calculate', methods=['POST'])
def calculate_shortest_path():
    source_node = int(request.form['source_node'])
    target_node = int(request.form['target_node'])

    # Define a heuristic function for straight-line distance
    def heuristic_function(node1, node2):
        x1, y1 = G.nodes[node1]['x'], G.nodes[node1]['y']
        x2, y2 = G.nodes[node2]['x'], G.nodes[node2]['y']
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    # Calculate the shortest path
    path = nx.astar_path(G, source=source_node, target=target_node, heuristic=heuristic_function)

    # Plot the graph with the shortest path
    fig, ax = ox.plot_graph_route(G, path, route_linewidth=6, node_size=0, bgcolor='k', show=False)

    # Save the figure to a file
    image_file = os.path.join(app.config['UPLOAD_FOLDER'], 'map.png')
    fig.savefig(image_file, format='png')
    plt.close(fig)  # Close the figure to release resources

    return render_template('map.html', image_file=image_file)

# Serve the image using a static route
@app.route('/static/images/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
