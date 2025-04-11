import os
import time
from flask import Flask, render_template, jsonify, request, abort
from typing import List, Literal

# Define the Node class with an additional output_dir property.
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
    # Wrap the text in a span with a semi-transparent background color.
    text_html = (
        f'<span style="background-color: {bg_color}; padding: 2px 4px; border-radius: 3px;">'
        f'{node.name} ({node.status})'
        f'</span>'
    )
    return {
        "id": f"{node.name}_{node.node_type}",  # Static id ensures state persistence.
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

app = Flask(__name__)

# Global example tree.
example_tree = Node(
    name="Root_Group",
    status="running",
    num_descendants=3,
    node_type="job_group",
    output_dir="",
    children=[
        Node(name="Job_1", children=[], status="succeeded", num_descendants=0, node_type="job"),
        Node(name="Job_2", children=[], status="failed", num_descendants=0, node_type="job"),
        Node(
            name="Sub_Group",
            children=[
                # Set output_dir for Job_3 as requested.
                Node(name="Job_3", children=[], status="running", num_descendants=0, node_type="job",
                     output_dir="/tmp/example/Root_Group/Sub_Group/Job_3/"),
                Node(name="Job_4", children=[], status="succeeded", num_descendants=0, node_type="job")
            ],
            status="scheduled",
            num_descendants=2,
            node_type="job_group"
        )
    ]
)

# Global variable for simulating updates.
last_node_added_time = time.time()

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/get_tree_json")
def get_tree_json():
    global example_tree, last_node_added_time
    current_time = time.time()
    # Simulate: Every 10 seconds, add or remove a node.
    if current_time - last_node_added_time >= 10:
        import random
        if random.choice([True, False]) or not example_tree.children:
            # Add new node.
            new_node = Node(
                name=f"New Job {int(current_time)}",
                children=[],
                status="scheduled",
                num_descendants=0,
                node_type="job"
            )
            example_tree.children.append(new_node)
        else:
            # Remove the first node.
            example_tree.children.pop(0)
        example_tree.num_descendants = len(example_tree.children)
        last_node_added_time = current_time
    tree_json = [node_to_jstree(example_tree)]
    return jsonify(tree_json)

# Endpoint to serve log file content from a given output directory.
@app.route("/get_log")
def get_log():
    output_dir = request.args.get("path", "")
    # Ensure the path is not empty and exists on the server.
    if not output_dir or not os.path.isdir(output_dir):
        return "Invalid directory path", 400
    log_path = os.path.join(output_dir, "log.txt")
    if os.path.isfile(log_path):
        try:
            print(log_path)
            from pathlib import Path

            print(f"{Path(log_path).touch(exist_ok=True)=}") # Ensure the file exists.
            with open(log_path, "r") as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        except Exception as e:
            return f"Error reading log file: {str(e)}", 500
    else:
        return "Log file not found", 404

if __name__ == "__main__":
    app.run(debug=True)
