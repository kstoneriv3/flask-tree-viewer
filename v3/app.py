from flask import Flask, render_template
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
    
    # Note: we now pass "event" along with "this" to our click handler.
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

# Example Node tree
example_tree = Node(
    name="Root Group",
    status="running",
    num_descendants=4,
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

@app.route("/")
def index():
    tree_html = f"<ul>{render_tree(example_tree)}</ul>"
    return render_template("dashboard.html", tree_html=tree_html)

if __name__ == "__main__":
    app.run(debug=True)

