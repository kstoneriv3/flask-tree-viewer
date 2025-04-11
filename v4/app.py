import time
from flask import Flask, render_template, jsonify, request
from typing import List, Literal

# Define the Node class
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

# Helper function to render the Node tree as an HTML unordered list.
def render_tree(node: Node) -> str:
    status_color = {
        "scheduled": "gray",
        "running": "blue",
        "failed": "red",
        "succeeded": "green"
    }
    color = status_color.get(node.status, "black")
    html = (
        f'<li data-name="{node.name}" '
        f'data-status="{node.status}" '
        f'data-numdesc="{node.num_descendants}" '
        f'data-nodetype="{node.node_type}" '
        f'onclick="selectNode(event, this)" style="cursor: pointer;">'
    )
    html += f'<span style="color: {color}; font-weight: bold;">{node.name} ({node.status})'
    if node.num_descendants > 0:
        html += f' - Descendants: {node.num_descendants}'
    html += '</span>'
    
    if node.children:
        html += '<ul>'
        for child in node.children:
            html += render_tree(child)
        html += '</ul>'
    html += '</li>'
    return html

app = Flask(__name__)

# Global example tree
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
            ],
            status="scheduled",
            num_descendants=1,
            node_type="job_group"
        )
    ]
)

# Global variable to record when we last added a new node
last_node_added_time = time.time()

@app.route("/")
def index():
    tree_html = f"<ul>{render_tree(example_tree)}</ul>"
    return render_template("dashboard.html", tree_html=tree_html)

@app.route("/get_tree")
def get_tree():
    global example_tree, last_node_added_time
    current_time = time.time()
    # Every 10 seconds, simulate adding a new node to the root group.
    if current_time - last_node_added_time >= 10:
        new_node_name = f"New Job {int(current_time)}"
        new_node = Node(new_node_name, children=[], status="scheduled", num_descendants=0, node_type="job")
        example_tree.children.append(new_node)
        # Update the root's descendant count (simple simulation)
        example_tree.num_descendants = len(example_tree.children)
        last_node_added_time = current_time
    tree_html = f"<ul>{render_tree(example_tree)}</ul>"
    # Return the HTML string (MIME type text/html)
    return tree_html

if __name__ == "__main__":
    app.run(debug=True)

