from __future__ import annotations

import math
from urllib.parse import quote

import httpx
import networkx as nx
import plotly.graph_objects as go
import streamlit as st

DEFAULT_API_BASE = "http://localhost:8000"


def _request_json(method: str, base_url: str, path: str, **kwargs) -> dict | list:
    url = f"{base_url.rstrip('/')}{path}"
    with httpx.Client(timeout=30.0) as client:
        response = client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()


def _build_graph_figure(nodes: list[dict], edges: list[dict]) -> go.Figure:
    graph = nx.Graph()

    for node in nodes:
        graph.add_node(
            node["id"],
            name=node.get("name", "unknown"),
            labels=", ".join(node.get("labels", [])),
        )

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source in graph.nodes and target in graph.nodes:
            graph.add_edge(source, target, rel_type=edge.get("type", "RELATES_TO"))

    if graph.number_of_nodes() == 0:
        return go.Figure()

    spring_k = 1.0 / math.sqrt(max(graph.number_of_nodes(), 1))
    positions = nx.spring_layout(graph, seed=42, k=spring_k)

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for source, target in graph.edges():
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line={"width": 1, "color": "#94a3b8"},
        hoverinfo="none",
    )

    node_x: list[float] = []
    node_y: list[float] = []
    node_text: list[str] = []
    node_hover: list[str] = []
    node_color: list[int] = []
    node_size: list[int] = []

    for node_id, attrs in graph.nodes(data=True):
        x, y = positions[node_id]
        degree = graph.degree(node_id)
        node_x.append(x)
        node_y.append(y)
        node_text.append(attrs["name"])
        node_hover.append(
            f"{attrs['name']}<br>Labels: {attrs['labels'] or 'N/A'}<br>Degree: {degree}"
        )
        node_color.append(degree)
        node_size.append(16 + min(degree * 3, 20))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        hovertext=node_hover,
        hoverinfo="text",
        marker={
            "size": node_size,
            "color": node_color,
            "colorscale": "Blues",
            "showscale": True,
            "line": {"width": 1, "color": "#0f172a"},
            "colorbar": {"title": "Degree"},
        },
    )

    figure = go.Figure(data=[edge_trace, node_trace])
    figure.update_layout(
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        showlegend=False,
        plot_bgcolor="#ffffff",
        xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
    )
    return figure


def _render_query_tab(base_url: str, default_mode: str, default_top_k: int) -> None:
    st.subheader("Ask Questions")

    question = st.text_area(
        "Question",
        placeholder="Ask a grounded question about your documents...",
        height=120,
    )
    controls_col1, controls_col2 = st.columns(2)
    with controls_col1:
        mode = st.selectbox("Mode", options=["rag", "agent"], index=0 if default_mode == "rag" else 1)
    with controls_col2:
        top_k = st.slider("Top K", min_value=1, max_value=20, value=default_top_k)

    if st.button("Run Query", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("Enter a question before running a query.")
            return

        with st.spinner("Querying..."):
            try:
                response = _request_json(
                    "POST",
                    base_url,
                    "/query",
                    json={"question": question.strip(), "mode": mode, "top_k": top_k},
                )
            except httpx.HTTPStatusError as exc:
                st.error(f"Request failed: HTTP {exc.response.status_code}")
                st.code(exc.response.text)
                return
            except Exception as exc:
                st.error(f"Request failed: {exc}")
                return

        st.markdown("### Answer")
        st.write(response.get("answer", ""))

        if response.get("sources"):
            st.markdown("### Sources")
            st.dataframe(response["sources"], hide_index=True, use_container_width=True)

        if response.get("graph_context"):
            st.markdown("### Graph Context")
            st.code(response["graph_context"])

        if response.get("agent_steps"):
            st.markdown("### Agent Steps")
            for index, step in enumerate(response["agent_steps"], start=1):
                with st.expander(f"Step {index}: {step.get('tool', 'unknown')}"):
                    st.write(f"Thought: {step.get('thought', '')}")
                    st.write(f"Input: {step.get('input', '')}")
                    st.write(step.get("observation", ""))


def _render_graph_tab(base_url: str) -> None:
    st.subheader("Knowledge Graph Explorer")
    st.caption("Load an entity and render its local subgraph from Neo4j.")

    if "graph_entities" not in st.session_state:
        st.session_state.graph_entities = []

    controls_col1, controls_col2 = st.columns([2, 1])

    with controls_col1:
        selected_name = ""
        if st.session_state.graph_entities:
            selected_name = st.selectbox(
                "Select an entity",
                options=[""] + [entry["name"] for entry in st.session_state.graph_entities],
                index=0,
            )
        manual_name = st.text_input("Or enter entity name")
        target_entity = manual_name.strip() or selected_name

    with controls_col2:
        max_hops = st.slider("Max hops", min_value=1, max_value=4, value=2)
        node_limit = st.slider("Node limit", min_value=10, max_value=1000, value=200, step=10)
        edge_limit = st.slider("Edge limit", min_value=10, max_value=2000, value=400, step=10)

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("Load Entity List", use_container_width=True):
            with st.spinner("Loading entities..."):
                try:
                    entities = _request_json(
                        "GET",
                        base_url,
                        "/graph/entities",
                        params={"limit": 500},
                    )
                    st.session_state.graph_entities = entities
                    st.success(f"Loaded {len(entities)} entities.")
                except httpx.HTTPStatusError as exc:
                    st.error(f"Failed to load entities: HTTP {exc.response.status_code}")
                    st.code(exc.response.text)
                except Exception as exc:
                    st.error(f"Failed to load entities: {exc}")

    with action_col2:
        render_graph = st.button("Render Subgraph", type="primary", use_container_width=True)

    if not render_graph:
        return
    if not target_entity:
        st.warning("Provide an entity name before rendering.")
        return

    with st.spinner("Rendering graph..."):
        encoded_entity = quote(target_entity, safe="")
        try:
            subgraph = _request_json(
                "GET",
                base_url,
                f"/graph/subgraph/{encoded_entity}",
                params={"max_hops": max_hops, "node_limit": node_limit, "edge_limit": edge_limit},
            )
        except httpx.HTTPStatusError as exc:
            st.error(f"Subgraph query failed: HTTP {exc.response.status_code}")
            st.code(exc.response.text)
            return
        except Exception as exc:
            st.error(f"Subgraph query failed: {exc}")
            return

    nodes = subgraph.get("nodes", [])
    edges = subgraph.get("edges", [])
    stats_col1, stats_col2 = st.columns(2)
    stats_col1.metric("Nodes", len(nodes))
    stats_col2.metric("Edges", len(edges))

    st.plotly_chart(_build_graph_figure(nodes, edges), use_container_width=True)
    with st.expander("Subgraph Data"):
        st.write("Nodes")
        st.dataframe(nodes, hide_index=True, use_container_width=True)
        st.write("Edges")
        st.dataframe(edges, hide_index=True, use_container_width=True)


def _render_system_tab(base_url: str) -> None:
    st.subheader("System Status")
    st.caption("Quick visibility into service health and graph inventory.")

    if st.button("Refresh Health", use_container_width=True):
        st.session_state.pop("cached_health", None)

    if "cached_health" not in st.session_state:
        try:
            st.session_state.cached_health = _request_json("GET", base_url, "/health")
        except Exception as exc:
            st.error(f"Health check failed: {exc}")
            return

    health = st.session_state.cached_health
    status_col1, status_col2, status_col3 = st.columns(3)
    status_col1.metric("Service Status", health.get("status", "unknown"))
    status_col2.metric("Chroma Docs", health.get("chroma_docs", 0))
    status_col3.metric("Neo4j Connected", "Yes" if health.get("neo4j_connected") else "No")

    if st.button("Preview Entities", use_container_width=True):
        try:
            entities = _request_json("GET", base_url, "/graph/entities", params={"limit": 25})
            st.dataframe(entities, hide_index=True, use_container_width=True)
        except Exception as exc:
            st.error(f"Could not load entity preview: {exc}")


def main() -> None:
    st.set_page_config(
        page_title="Enterprise Document Intelligence Dashboard",
        layout="wide",
    )

    st.title("Enterprise Document Intelligence")
    st.caption("Interactive dashboard for querying documents and visualizing graph relationships.")

    with st.sidebar:
        st.header("Settings")
        api_base = st.text_input("API Base URL", value=DEFAULT_API_BASE).strip() or DEFAULT_API_BASE
        default_mode = st.selectbox("Default Query Mode", options=["rag", "agent"], index=0)
        default_top_k = st.slider("Default Top K", min_value=1, max_value=20, value=5)

    query_tab, graph_tab, system_tab = st.tabs(["Ask", "Graph", "System"])

    with query_tab:
        _render_query_tab(api_base, default_mode, default_top_k)
    with graph_tab:
        _render_graph_tab(api_base)
    with system_tab:
        _render_system_tab(api_base)


if __name__ == "__main__":
    main()
