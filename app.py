from flask import Flask, render_template, request, send_from_directory, session, redirect, url_for, send_file
import osmnx as ox
import networkx as nx
from PIL import Image
import matplotlib.pyplot as plt
from io import BytesIO
import os
import csv
from datetime import datetime
import threading

app = Flask(__name__)
app.secret_key = "RouteSuggestion"

# Define the directory to save images
app.config['UPLOAD_FOLDER'] = 'static/images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

G = ox.graph_from_xml(r"map.osm")

def save_nodes_to_csv(name, source_node, target_node, timestamp):
    with open('records.csv', 'a', newline='') as csvfile:
        fieldnames = ['name', 'source_node', 'target_node', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if os.stat('records.csv').st_size == 0:
            writer.writeheader()
        writer.writerow({'name': name, 'source_node': source_node, 'target_node': target_node, 'timestamp': timestamp})

def plot_graph_async(G, path, image_file):
    fig, ax = ox.plot_graph_route(G, path, route_linewidth=6, node_size=0, bgcolor='k', show=False)
    fig.savefig(image_file, format='png')
    plt.close(fig)

@app.route('/')
def index():
    if 'loggedin' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        
        if name:
            session['loggedin'] = True
            session['name'] = name
            return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('map.html', name=session['name'], image_data="")

@app.route('/calculate', methods=['POST'])
def calculate_shortest_path():
    name = request.form['name']
    source_node = int(request.form['source_node'])
    target_node = int(request.form['target_node'])
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    save_nodes_to_csv(name, source_node, target_node, timestamp)

    def heuristic_function(node1, node2):
        x1, y1 = G.nodes[node1]['x'], G.nodes[node1]['y']
        x2, y2 = G.nodes[node2]['x'], G.nodes[node2]['y']
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    path = nx.astar_path(G, source=source_node, target=target_node, heuristic=heuristic_function)

    image_file = os.path.join(app.config['UPLOAD_FOLDER'], 'map.png')
    threading.Thread(target=plot_graph_async, args=(G, path, image_file)).start()

    return redirect(url_for('dashboard', image_file=image_file))

@app.route('/static/images/<filename>')
def serve_image(filename):
    img = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    cropped_img = img.crop((0, 50, img.width, img.height))
    cropped_img_io = BytesIO()
    cropped_img.save(cropped_img_io, format='PNG')
    cropped_img_io.seek(0)
    return send_file(cropped_img_io, mimetype='image/png')

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('name', None)
    return redirect(url_for('index'))
