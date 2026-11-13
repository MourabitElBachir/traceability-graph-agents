"""Resolve and summarise ontology/traceability.ttl."""

from __future__ import annotations

import os
from pathlib import Path

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS

AGR = Namespace("https://example.org/agritrace/ontology#")


def locate_ontology(explicit: str = "") -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(path)
        return path
    env = os.getenv("AGRITRACE_ONTOLOGY", "")
    if env:
        return locate_ontology(env)
    cwd = Path.cwd() / "ontology" / "traceability.ttl"
    if cwd.exists():
        return cwd
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "ontology" / "traceability.ttl"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("ontology/traceability.ttl not found; set AGRITRACE_ONTOLOGY")


def load_graph(path: Path | None = None) -> Graph:
    graph = Graph()
    graph.parse(path or locate_ontology(), format="turtle")
    return graph


def summarise(path: Path | None = None) -> dict[str, object]:
    graph = load_graph(path)
    ontology = URIRef("https://example.org/agritrace/ontology")
    version = None
    for value in graph.objects(ontology, OWL.versionInfo):
        version = str(value)
    classes = sorted(
        str(graph.value(subject, RDFS.label) or subject) for subject in graph.subjects(RDF.type, OWL.Class)
    )
    properties = sorted(
        str(graph.value(subject, RDFS.label) or subject) for subject in graph.subjects(RDF.type, OWL.ObjectProperty)
    )
    return {
        "path": str(path or locate_ontology()),
        "version": version,
        "classes": classes,
        "object_properties": properties,
    }
