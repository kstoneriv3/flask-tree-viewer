import time
from flask import Flask, render_template, jsonify
from typing import List, Literal

# Define the Node class.
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

# Helper function: Convert a Node to a jsTree-compatible dictionary.
def node_to_jstree(node: Node) -> dict:
    return {
        "id": f"{node.name}_{node.node_type}",  # Use a static id based on name and type.
        "text": f"{node.name} ({node.status})",
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

# Global variable to track time for simulating new nodes.
last_node_added_time = time.time()

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/get_tree_json")
def get_tree_json():
    global example_tree, last_node_added_time
    current_time = time.time()
    # Simulate: Every 10 seconds, add a new node OR remove one randomly.
    if current_time - last_node_added_time >= 10:
        # For demonstration, randomly add or remove a node.
        import random
        if random.choice([True, False]):
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
            # Remove a node if there is at least one removable (avoid removing root)
            if example_tree.children:
                removed_node = example_tree.children.pop(0)
                # Update descendant count
        example_tree.num_descendants = len(example_tree.children)
        last_node_added_time = current_time
    # Return the tree as a JSON array.
    tree_json = [node_to_jstree(example_tree)]
    return jsonify(tree_json)

if __name__ == "__main__":
    app.run(debug=True)

