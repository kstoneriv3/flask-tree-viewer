import os
import time
from flask import Flask, render_template, jsonify, request, abort
from typing import List, Literal

# Define the Node class.
class Node:
    def __init__(
        self,
        name: str,
        children: List['Node'],
        status: Literal["scheduled", "running", "failed", "succeeded"],
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
    colors = {
       "succeeded": "rgba(0,255,0,0.3)",
       "failed": "rgba(255,0,0,0.3)",
       "running": "rgba(255,255,0,0.3)",
       "scheduled": "rgba(0,0,255,0.3)"
    }
    bg_color = colors.get(node.status, "transparent")
    text_html = (
        f'<span style="background-color: {bg_color}; padding: 2px 4px; border-radius: 3px;">'
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

# Helper function to generate a tree with the given number of nodes.
def generate_example_tree(num_nodes: int = 100) -> Node:
    nodes = []
    statuses = ["scheduled", "running", "failed", "succeeded"]
    for i in range(1, num_nodes + 1):
        # Cycle through statuses.
        status = statuses[i % len(statuses)]
        node = Node(
            name=f"Job_{i}",
            children=[],
            status=status,
            num_descendants=0,
            node_type="job",
            output_dir=f"/tmp/example/Root_Group/Job_{i}/"
        )
        nodes.append(node)
    return Node(
        name="Root_Group",
        children=nodes,
        status="running",
        num_descendants=len(nodes),
        node_type="job_group",
        output_dir="/tmp/example/Root_Group/"
    )

app = Flask(__name__)
# Generate a tree with 10K nodes.
example_tree = generate_example_tree(10000)
last_node_added_time = time.time()

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/get_tree_json")
def get_tree_json():
    global example_tree, last_node_added_time
    current_time = time.time()
    # Simulate an update every 10 seconds:
    # Only add a new node if the tree has fewer than 10K nodes.
    if current_time - last_node_added_time >= 10:
        import random
        if len(example_tree.children) < 10000:
            new_node = Node(
                name=f"New_Job_{int(current_time)}",
                children=[],
                status="scheduled",
                num_descendants=0,
                node_type="job",
                output_dir=f"/tmp/example/Root_Group/New_Job_{int(current_time)}/"
            )
            example_tree.children.append(new_node)
        else:
            # Remove the first node to maintain the 10K limit (optional)
            example_tree.children.pop(0)
        example_tree.num_descendants = len(example_tree.children)
        last_node_added_time = current_time
    tree_json = [node_to_jstree(example_tree)]
    return jsonify(tree_json)

# Enhanced endpoint to serve log file content from a given output directory.
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
    
    if request.method == "HEAD":
        if os.path.isfile(log_path):
            return "", 200
        else:
            return "", 404
    
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

# New endpoint to list all files in the given output directory.
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

if __name__ == "__main__":
    app.run(debug=True)
