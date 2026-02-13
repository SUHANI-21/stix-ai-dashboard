import os
import json
import networkx as nx
from pyvis.network import Network
from collections import Counter

def build_stix_graph(bundles_dir):
    G = nx.DiGraph()  # Directed graph fits STIX semantics

    for _,_,files in os.walk(bundles_dir):
        for file in files:
            if not file.endswith(".json"):
                continue

            path = os.path.join(bundles_dir, file)

            with open(path, "r", encoding="utf-8") as f:
                bundle = json.load(f)

            if bundle.get("type") != "bundle":
                continue

            for obj in bundle.get("objects", []):

                obj_id = obj.get("id")
                obj_type = obj.get("type")

                if not obj_id or not obj_type:
                    continue

                # ------------------
                # Add node
                # ------------------
                if obj_type != "relationship":
                    G.add_node(
                        obj_id,
                        type=obj_type,
                        name=obj.get("name", ""),
                        description=obj.get("description", ""),
                        stix=obj   # 👈 store full object
                    )


                # ------------------
                # Add edge
                # ------------------
                if obj_type == "relationship":
                    src = obj.get("source_ref")
                    tgt = obj.get("target_ref")
                    rel = obj.get("relationship_type")

                    if src and tgt:
                        G.add_edge(
                            src,
                            tgt,
                            relationship=rel
                        )

    return G


# def draw_interactive_graph(G, output_file="stix_graph.html"):
#     net = Network(
#         height="800px",
#         width="100%",
#         directed=True,
#         bgcolor="#0f172a",
#         font_color="white"
#     )

#     for node, data in G.nodes(data=True):
#         label = data.get("name") or node.split("--")[0]
#         title = f"""
#         <b>{label}</b><br>
#         Type: {data.get("type")}
#         """
#         net.add_node(node, label=label, title=title)

#     for src, tgt, data in G.edges(data=True):
#         net.add_edge(
#             src,
#             tgt,
#             label=data.get("relationship", ""),
#             arrows="to"
#         )

#     net.write_html(output_file)

import json
from pyvis.network import Network

def draw_interactive_graph(G, output_file="stix_graph.html"):
    net = Network(
        height="800px",
        width="100%",
        directed=True,
        bgcolor="#0f172a",
        font_color="white"
    )

    for node, data in G.nodes(data=True):
        label = data.get("name") or node.split("--")[0]

        # Pretty-print JSON
        json_content = json.dumps(data, indent=2, ensure_ascii=False)

        title = f"""
        <div style="font-size:12px; max-width:500px;">
            <b>{label}</b><br>
            <pre>{json_content}</pre>
        </div>
        """

        net.add_node(
            node,
            label=label,
            title=title
        )

    for src, tgt, data in G.edges(data=True):
        net.add_edge(
            src,
            tgt,
            label=data.get("relationship", ""),
            arrows="to"
        )

    net.write_html(output_file)
    print(f"[+] Graph written to {output_file}")

#testing
graph=build_stix_graph("/Users/alwyndsouza/Documents/GitHub/stix_normalizer/antonio_formato_bundles")
print(f"no of edges:{graph.number_of_edges()}, num_of nodes:{graph.number_of_nodes()}")

# from collections import Counter

# types = Counter(
#     data.get("type", "unknown")
#     for _, data in graph.nodes(data=True)
# )

# print(types)

import networkx as nx

def get_ego_graph(graph, id, radius=1):
    if id not in graph:
        raise ValueError(f"ID {id} not found in graph")

    ego = nx.ego_graph(
        graph,
        id,
        radius=radius,
        center=True,
        undirected=False
    )

    print(f"Ego graph for {id}:")
    print(f"Nodes: {ego.number_of_nodes()}, Edges: {ego.number_of_edges()}")
    types = Counter(
        data.get("type", "unknown")
        for _, data in ego.nodes(data=True)
    )

    print(types)
    return ego



ego_graph= get_ego_graph(graph,"malware--d155005c-19f8-0f62-9c02-92a4f6d5a6ae")
draw_interactive_graph(ego_graph)

