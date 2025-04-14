import os
import time
import fire
import waitress
import concurrent.futures
from flask import Flask, render_template, jsonify, request
from typing import List, Literal, Tuple

# Global variable for the user-supplied root directory
ROOT_PATH = None

# Define the Node class.
class Node:
    def __init__(
        self,
        name: str,
        children: List['Node'],
        status: str,  # now "small", "medium", "large", or "huge"
        num_descendants: int,
        node_type: Literal["job_group", "job"],
        output_dir: str = ""
    ):
        self.name = name
        self.children = children
        self.status = status
        self.num_descendants = num_descendants
        self.node_type = node_type
        self.output_dir = output_dir

# Convert a Node to a jsTree-compatible dictionary.
def node_to_jstree(node: Node) -> dict:
    # Map size category to colors: blue, green, yellow, red.
    colors = {
       "small": "rgba(0,0,255,0.3)",   # blue
       "medium": "rgba(0,255,0,0.3)",    # green
       "large": "rgba(255,255,0,0.3)",   # yellow
       "huge": "rgba(255,0,0,0.3)"       # red
    }
    bg_color = colors.get(node.status, "transparent")
    # The title now shows the folder name and its size category.
    text_html = (
        f'<span title="{node.name}" style="background-color: {bg_color}; padding: 2px 4px; border-radius: 3px;">'
        f'{node.name} ({node.status})'
        f'</span>'
    )
    return {
        "id": f"{node.name}_{node.node_type}",
        "text": text_html,
        "data": {
            "name": node.name,
            "status": node.status,
            "num_descendants": node.num_descendants,
            "node_type": node.node_type,
            "output_dir": node.output_dir
        },
        "children": [node_to_jstree(child) for child in node.children]
    }

# DFS scanning using os.path.scandir with multithreading.
def build_tree(path: str, executor: concurrent.futures.ThreadPoolExecutor) -> Tuple[int, Node]:
    aggregated_size = 0
    children_nodes = []
    futures = []
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        # Submit a task to process the subdirectory
                        futures.append((entry.name, entry.path, executor.submit(build_tree, entry.path, executor)))
                    elif entry.is_file(follow_symlinks=False):
                        try:
                            size = entry.stat().st_size
                        except Exception:
                            size = 0
                        aggregated_size += size
                except Exception as e:
                    print(f"Error accessing entry in {path}: {e}")
    except Exception as e:
        print(f"Error scanning directory {path}: {e}")
    
    # Process the subdirectory futures.
    for sub_name, sub_path, future in futures:
        try:
            sub_size, sub_node = future.result()
            aggregated_size += sub_size
            children_nodes.append(sub_node)
        except Exception as e:
            print(f"Error processing subdirectory {sub_path}: {e}")

    # Determine size category based on aggregated_size.
    if aggregated_size < 1024:
         status = "small"
    elif aggregated_size < 1024 * 1024:
         status = "medium"
    elif aggregated_size < 1024 * 1024 * 1024:
         status = "large"
    else:
         status = "huge"

    # Determine node type: if "log.txt" exists in the current folder, it's a job.
    is_job = os.path.isfile(os.path.join(path, "log.txt"))
    node_type = "job" if is_job else "job_group"
    
    # Calculate the number of descendant nodes.
    num_descendants = sum(1 + child.num_descendants for child in children_nodes)
    
    # Use the folder name (or the full path if basename is empty).
    node_name = os.path.basename(path) if os.path.basename(path) else path
    node = Node(name=node_name, children=children_nodes, status=status, num_descendants=num_descendants, node_type=node_type, output_dir=path)
    return aggregated_size, node

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/get_tree_json")
def get_tree_json():
    global ROOT_PATH
    if not ROOT_PATH or not os.path.isdir(ROOT_PATH):
         return jsonify({"error": "Invalid root path"}), 400
    # Use a thread pool to scan the tree in parallel.
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
         _, tree = build_tree(ROOT_PATH, executor)
    tree_json = [node_to_jstree(tree)]
    return jsonify(tree_json)

# Enhanced endpoint to serve log file content.
@app.route("/get_log", methods=["GET", "HEAD"])
def get_log():
    output_dir = request.args.get("path", "")
    filename = request.args.get("filename", "log.txt")
    
    if not output_dir:
        return "Invalid directory path", 400
    if not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            return f"Error creating directory: {str(e)}", 500

    log_path = os.path.join(output_dir, filename)
    
    # For HEAD requests, simply indicate existence.
    if request.method == "HEAD":
        if os.path.isfile(log_path):
            return "", 200
        else:
            return "", 404
    
    # If the file exists and is too large (>1MB), don’t send its content.
    if os.path.exists(log_path) and os.path.getsize(log_path) > 1024 * 1024:
         return "File too large to display", 400, {'Content-Type': 'text/plain; charset=utf-8'}
    
    # If the file does not exist, create a sample log file.
    if not os.path.exists(log_path):
        try:
            if filename == "log.txt":
                content = f"This is a sample log file for {output_dir}\n"
                content += "INFO: Job started at 2025-04-12 09:00:00\n"
                content += "INFO: Processing input data...\n"
                content += "INFO: Task 1 completed successfully\n"
                content += "INFO: Task 2 completed successfully\n"
                content += "INFO: Job completed at 2025-04-12 09:15:32\n"
            elif filename == "stderr.txt":
                content = "Warning: Resource usage approaching limits\n"
                content += "Warning: Memory usage at 85%\n"
            elif filename == "stdout.txt":
                content = "Output 1: 42.5\n"
                content += "Output 2: Success\n"
                content += "Output 3: Completed with results [1, 2, 3]\n"
            elif filename == "config.json":
                content = '{\n  "workers": 4,\n  "memory": "8GB",\n  "timeout": 3600\n}'
            else:
                content = f"Content of {filename}\n"
            with open(log_path, "w") as f:
                f.write(content)
        except Exception as e:
            return f"Error creating sample log file: {str(e)}", 500
    
    try:
        with open(log_path, "r") as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return f"Error reading log file: {str(e)}", 500

# Endpoint to list all files in a given output directory.
@app.route("/list_logs")
def list_logs():
    output_dir = request.args.get("path", "")
    if not output_dir:
        return jsonify({"error": "No directory provided"}), 400
    if not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    try:
        files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def main(mode="debug", root=".", host="localhost", port=5000):
    global ROOT_PATH
    ROOT_PATH = os.path.abspath(root)
    print("Serving directory tree for:", ROOT_PATH)
    if mode == "debug":
        app.run(debug=True, host=host, port=port)
    elif mode == "serve":
        waitress.serve(app, host=host, port=port, threads=4)
    else:
        print("Invalid mode. Use 'debug' or 'serve'.")

if __name__ == "__main__":
    fire.Fire(main)
