import time
from flask import Flask, render_template, jsonify
from typing import List, Literal

# Define your Node class.
class Node:
    def __init__(
        self,
        name: str,
        children: List['Node'],
        status: Literal["scheduled", "running", "failed", "succeeded"],
        num_descendants: int,
        node_type: Literal["job_group", "job"]
    ):
        self.name = name
        self.children = children
        self.status = status
        self.num_descendants = num_descendants
        self.node_type = node_type

# Convert a Node to a jsTree-compatible dictionary.
# We use a static id (name + node_type) so that existing nodes retain their id.
def node_to_jstree(node: Node) -> dict:
    colors = {
       "succeeded": "rgba(0,255,0,0.3)",
       "failed": "rgba(255,0,0,0.3)",
       "running": "rgba(255,255,0,0.3)",
       "scheduled": "rgba(0,0,255,0.3)"
    }
    bg_color = colors.get(node.status, "transparent")
    # Create HTML for node text with a background color marker.
    text_html = (
        f'<span style="background-color: {bg_color}; padding: 2px 4px; border-radius: 3px;">'
        f'{node.name} ({node.status})'
        f'</span>'
    )
    return {
        "id": f"{node.name}_{node.node_type}",  # Static id to preserve jsTree state.
        "text": text_html,
        "data": {
            "name": node.name,
            "status": node.status,
            "num_descendants": node.num_descendants,
            "node_type": node.node_type
        },
        "children": [node_to_jstree(child) for child in node.children]
    }

app = Flask(__name__)

# Global example tree.
example_tree = Node(
    name="Root Group",
    status="running",
    num_descendants=3,
    node_type="job_group",
    children=[
        Node(name="Job 1", children=[], status="succeeded", num_descendants=0, node_type="job"),
        Node(name="Job 2", children=[], status="failed", num_descendants=0, node_type="job"),
        Node(
            name="Sub Group",
            children=[
                Node(name="Job 3", children=[], status="running", num_descendants=0, node_type="job"),
                Node(name="Job 4", children=[], status="succeeded", num_descendants=0, node_type="job")
            ],
            status="scheduled",
            num_descendants=2,
            node_type="job_group"
        )
    ]
)

# Global variable to simulate updates.
last_node_added_time = time.time()

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/get_tree_json")
def get_tree_json():
    global example_tree, last_node_added_time
    current_time = time.time()
    # Simulate adding or removing a node every 10 seconds.
    if current_time - last_node_added_time >= 10:
        import random
        if random.choice([True, False]) or not example_tree.children:
            # Add a new node.
            new_node = Node(
                name=f"New Job {int(current_time)}",
                children=[],
                status="scheduled",
                num_descendants=0,
                node_type="job"
            )
            example_tree.children.append(new_node)
        else:
            # Remove a node from the beginning.
            example_tree.children.pop(0)
        example_tree.num_descendants = len(example_tree.children)
        last_node_added_time = current_time
    tree_json = [node_to_jstree(example_tree)]
    return jsonify(tree_json)

if __name__ == "__main__":
    app.run(debug=True)

