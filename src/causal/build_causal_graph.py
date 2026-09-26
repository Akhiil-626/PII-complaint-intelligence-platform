"""
Builds and analyzes a root-cause causal graph from extracted cause/effect
data (data/processed/causal_pairs.json, produced by
src.causal.extract_causes).

Since cause/effect phrasing varies across complaints even when
semantically similar, this module first clusters near-duplicate
immediate_cause and root_cause phrases using Sentence-BERT embeddings and
agglomerative clustering, assigning each cluster a canonical label (the
shortest phrase in the cluster). It then builds a directed graph:

    root_cause -> immediate_cause -> category

and reports which root causes have the highest out-degree (i.e. are
connected to the most distinct immediate causes/categories), representing
the most impactful systemic issues across the complaint dataset.

The resulting graph is saved in GEXF format for later visualization (e.g.
in the project's dashboard).

Usage
-----
    python -m src.causal.build_causal_graph
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import networkx as nx
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INPUT_PATH = Path("data/processed/causal_pairs.json")
GRAPH_OUTPUT_PATH = Path("models/saved/causal_graph.gexf")

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Clustering distance threshold (cosine distance). Lower = stricter
# (fewer merges), higher = looser (more merges). Tuned empirically for
# short cause-phrase clustering; adjust if clusters look too coarse/fine
# when inspecting the printed cluster report.
CLUSTER_DISTANCE_THRESHOLD = 0.5

TOP_N_ROOT_CAUSES = 10


# ---------------------------------------------------------------------------
# Data loading + cleaning
# ---------------------------------------------------------------------------

def load_causal_pairs(path: Path = INPUT_PATH) -> List[Dict]:
    """Load the extracted cause/effect pairs from disk.

    Args:
        path: Path to the causal_pairs.json file.

    Returns:
        The list of complaint-level cause/effect dicts.

    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Causal pairs file not found at: {path.resolve()}. "
            "Run src.causal.extract_causes first."
        )

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def clean_cause_value(value: Optional[str]) -> Optional[str]:
    """Normalize a cause field value, treating null-like values as None.

    Handles both real JSON null (parsed as Python None) and the literal
    string "null" (a known quirk of some LLM outputs), plus empty/blank
    strings.

    Args:
        value: The raw immediate_cause or root_cause value from the data.

    Returns:
        The cleaned string, or None if the value represents "no cause".
    """
    if value is None:
        return None
    stripped = value.strip()
    if stripped == "" or stripped.lower() == "null":
        return None
    return stripped


# ---------------------------------------------------------------------------
# Phrase clustering (merge near-duplicate cause phrases)
# ---------------------------------------------------------------------------

def cluster_phrases(
    phrases: List[str], model: SentenceTransformer, distance_threshold: float
) -> Dict[str, str]:
    """Cluster near-duplicate phrases and map each to a canonical label.

    Uses Sentence-BERT embeddings and agglomerative clustering (cosine
    distance) to group semantically similar short phrases. Within each
    cluster, the shortest phrase is chosen as the canonical representative.

    Args:
        phrases: The list of distinct raw phrase strings to cluster.
        model: A loaded SentenceTransformer model.
        distance_threshold: Agglomerative clustering distance threshold.

    Returns:
        A dict mapping every input phrase to its canonical (cluster)
        label. If fewer than 2 distinct phrases are given, returns an
        identity mapping (no clustering needed/possible).
    """
    unique_phrases = list(dict.fromkeys(phrases))

    if len(unique_phrases) < 2:
        return {p: p for p in unique_phrases}

    embeddings = model.encode(unique_phrases, show_progress_bar=False)

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric="cosine",
        linkage="average",
    )
    labels = clustering.fit_predict(embeddings)

    clusters: Dict[int, List[str]] = {}
    for phrase, label in zip(unique_phrases, labels):
        clusters.setdefault(label, []).append(phrase)

    mapping: Dict[str, str] = {}
    for members in clusters.values():
        canonical = min(members, key=len)
        for phrase in members:
            mapping[phrase] = canonical

    return mapping


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph(
    records: List[Dict],
    immediate_cause_map: Dict[str, str],
    root_cause_map: Dict[str, str],
) -> nx.DiGraph:
    """Build a directed causal graph: root_cause -> immediate_cause -> category.

    Edge weights represent how many complaints support that specific
    causal link (repeated links increment the weight rather than creating
    duplicate edges).

    Args:
        records: The raw list of complaint cause/effect dicts.
        immediate_cause_map: Mapping from raw immediate_cause phrases to
            their canonical cluster label.
        root_cause_map: Mapping from raw root_cause phrases to their
            canonical cluster label.

    Returns:
        A populated networkx.DiGraph.
    """
    graph = nx.DiGraph()

    for record in records:
        category = record["category"]
        immediate = clean_cause_value(record.get("immediate_cause"))
        root = clean_cause_value(record.get("root_cause"))

        if immediate is None:
            continue

        immediate_canonical = immediate_cause_map.get(immediate, immediate)

        graph.add_node(immediate_canonical, node_type="immediate_cause")
        graph.add_node(category, node_type="category")

        if graph.has_edge(immediate_canonical, category):
            graph[immediate_canonical][category]["weight"] += 1
        else:
            graph.add_edge(immediate_canonical, category, weight=1)

        if root is not None:
            root_canonical = root_cause_map.get(root, root)
            graph.add_node(root_canonical, node_type="root_cause")

            if graph.has_edge(root_canonical, immediate_canonical):
                graph[root_canonical][immediate_canonical]["weight"] += 1
            else:
                graph.add_edge(root_canonical, immediate_canonical, weight=1)

    return graph


# ---------------------------------------------------------------------------
# Analysis / reporting
# ---------------------------------------------------------------------------

def rank_root_causes(graph: nx.DiGraph, top_n: int = TOP_N_ROOT_CAUSES) -> List[Tuple[str, int]]:
    """Rank root-cause nodes by total downstream complaint weight.

    Args:
        graph: The causal graph built by `build_graph`.
        top_n: Number of top root causes to return.

    Returns:
        A list of (root_cause_label, total_downstream_weight) tuples,
        sorted descending by weight.
    """
    root_nodes = [
        n for n, attrs in graph.nodes(data=True) if attrs.get("node_type") == "root_cause"
    ]

    scored = []
    for node in root_nodes:
        total_weight = sum(
            graph[node][neighbor]["weight"] for neighbor in graph.successors(node)
        )
        scored.append((node, total_weight))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]


def print_report(graph: nx.DiGraph, ranked_root_causes: List[Tuple[str, int]]) -> None:
    """Print a console report summarizing the causal graph.

    Args:
        graph: The causal graph built by `build_graph`.
        ranked_root_causes: Output of `rank_root_causes`.
    """
    divider = "=" * 60

    print(divider)
    print("ROOT-CAUSE CAUSAL GRAPH")
    print(divider)
    print(f"Total nodes : {graph.number_of_nodes()}")
    print(f"Total edges : {graph.number_of_edges()}")

    node_types = {}
    for _, attrs in graph.nodes(data=True):
        t = attrs.get("node_type", "unknown")
        node_types[t] = node_types.get(t, 0) + 1
    for t, count in node_types.items():
        print(f"  {t}: {count}")

    print("-" * 60)
    print(f"TOP {len(ranked_root_causes)} ROOT CAUSES BY DOWNSTREAM IMPACT")
    print("-" * 60)
    for rank, (cause, weight) in enumerate(ranked_root_causes, start=1):
        print(f"{rank}. {cause}  (downstream weight: {weight})")
    print(divider)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    """Load data, cluster phrases, build the causal graph, report, and save."""
    records = load_causal_pairs(INPUT_PATH)
    print(f"Loaded {len(records)} complaint cause/effect records.\n")

    immediate_phrases = [
        clean_cause_value(r.get("immediate_cause"))
        for r in records
        if clean_cause_value(r.get("immediate_cause")) is not None
    ]
    root_phrases = [
        clean_cause_value(r.get("root_cause"))
        for r in records
        if clean_cause_value(r.get("root_cause")) is not None
    ]

    print("Loading embedding model for phrase clustering...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("Clustering immediate cause phrases...")
    immediate_cause_map = cluster_phrases(immediate_phrases, model, CLUSTER_DISTANCE_THRESHOLD)

    print("Clustering root cause phrases...")
    root_cause_map = cluster_phrases(root_phrases, model, CLUSTER_DISTANCE_THRESHOLD)

    print(f"\nImmediate causes: {len(set(immediate_phrases))} raw -> "
          f"{len(set(immediate_cause_map.values()))} clusters")
    print(f"Root causes: {len(set(root_phrases))} raw -> "
          f"{len(set(root_cause_map.values()))} clusters\n")

    graph = build_graph(records, immediate_cause_map, root_cause_map)

    ranked = rank_root_causes(graph)
    print_report(graph, ranked)

    GRAPH_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    nx.write_gexf(graph, GRAPH_OUTPUT_PATH)
    print(f"\nGraph saved to: {GRAPH_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
