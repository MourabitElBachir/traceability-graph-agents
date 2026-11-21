"use client";

import { Background, ReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { Impact, Status } from "@/lib/types";

const fill: Record<Status, string> = {
  livre: "#b42318",
  stock: "#c2410c",
  sain: "#3f7d4e",
};

export function ImpactMap({ impact }: { impact: Impact }) {
  const nodes = impact.nodes.map((node) => ({
    id: node.id,
    position: { x: node.x, y: node.y },
    data: { label: node.label },
    style: {
      background: fill[node.status],
      color: "#fffdf8",
      border: "none",
      borderRadius: 12,
      padding: 12,
      width: 170,
      fontSize: 14,
    },
  }));
  const edges = impact.edges.map((edge, index) => ({
    id: `${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
  }));
  return (
    <div className="h-[420px] overflow-hidden rounded-lg border border-border bg-card">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background />
      </ReactFlow>
    </div>
  );
}
