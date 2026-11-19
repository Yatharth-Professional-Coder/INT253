const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

const root = 'c:/LPU/SEM 7/INT 253/INT253';
const uaDir = path.join(root, '.ua');
const interDir = path.join(uaDir, 'intermediate');

// 1. Read assembled-graph.json
const graph = JSON.parse(fs.readFileSync(path.join(interDir, 'assembled-graph.json'), 'utf8'));
const fileLevelTypes = new Set(['file', 'config', 'document', 'service', 'pipeline', 'table', 'schema', 'resource', 'endpoint']);

// Collect all file-level node IDs
const allFileNodeIds = graph.nodes.filter(n => fileLevelTypes.has(n.type)).map(n => n.id);

// 2. Define Layers
const layers = [
  {
    id: "layer:presentation-ui",
    name: "Presentation & Web UI",
    description: "Responsive Bootstrap 5 templates, POS checkout modals, KPI cards, and Chart.js reporting dashboards.",
    nodeIds: []
  },
  {
    id: "layer:controllers-routing",
    name: "HTTP Controllers & Routing",
    description: "Django views, URL routing dispatchers, forms validation, and template context processors.",
    nodeIds: []
  },
  {
    id: "layer:business-logic",
    name: "Business Logic & Services",
    description: "Atomic transaction handling for POS sales checkout, purchase order increments, stock adjustments, and administrative tooling.",
    nodeIds: []
  },
  {
    id: "layer:data-models",
    name: "Data Models & Persistence",
    description: "Relational database models for Products, Categories, Suppliers, Purchases, Sales, and UserProfiles.",
    nodeIds: []
  },
  {
    id: "layer:core-infra",
    name: "Configuration & Infrastructure",
    description: "Django core settings, WSGI/ASGI application hooks, CLI management tools, and runtime launchers.",
    nodeIds: []
  },
  {
    id: "layer:docs-testing",
    name: "Documentation & Quality Assurance",
    description: "System documentation, architectural overview, and automated unit test suite verifying stock safety.",
    nodeIds: []
  }
];

// Assign nodes to layers
allFileNodeIds.forEach(id => {
  if (id.includes("templates/")) {
    layers[0].nodeIds.push(id);
  } else if (id.includes("views.py") || id.includes("urls.py") || id.includes("forms.py") || id.includes("context_processors.py")) {
    layers[1].nodeIds.push(id);
  } else if (id.includes("services.py") || id.includes("admin.py") || id.includes("seed_data.py")) {
    layers[2].nodeIds.push(id);
  } else if (id.includes("models.py") || id.includes("apps.py") || id.includes("migrations/")) {
    layers[3].nodeIds.push(id);
  } else if (id.includes("settings.py") || id.includes("wsgi.py") || id.includes("asgi.py") || id.includes("manage.py") || id.includes("requirements.txt") || id.includes("start.sh") || id.includes(".gitkeep")) {
    layers[4].nodeIds.push(id);
  } else {
    layers[5].nodeIds.push(id);
  }
});

// 3. Define Tour
const tour = [
  {
    order: 1,
    title: "1. System Overview & Architecture",
    description: "Explore the core architecture of the Smart Inventory & POS Billing system, its Django settings, and database configurations.",
    nodeIds: ["document:README.md", "file:smart_inventory/settings.py", "file:manage.py"]
  },
  {
    order: 2,
    title: "2. Relational Data Models & ORM",
    description: "Understand the core entities: Products, Categories, Suppliers, Purchases, and Sales transactions.",
    nodeIds: ["file:inventory/models.py"]
  },
  {
    order: 3,
    title: "3. Atomic Inventory & Sales Services",
    description: "Discover how the system enforces atomic stock deductions on checkout, restocks on purchase receipt, and logs audit trails.",
    nodeIds: ["file:inventory/services.py"]
  },
  {
    order: 4,
    title: "4. POS Register & Web Views",
    description: "Inspect the high-speed barcode search, interactive cart calculations, and real-time cashier checkout views.",
    nodeIds: ["file:inventory/views.py", "file:templates/inventory/pos.html", "file:templates/inventory/dashboard.html"]
  },
  {
    order: 5,
    title: "5. Automated Testing & Reliability",
    description: "Review automated test assertions verifying stock deductions, oversell protections, and receipt calculations.",
    nodeIds: ["file:inventory/tests.py"]
  }
];

// 4. Update assembled-graph.json
graph.layers = layers;
graph.tour = tour;
fs.writeFileSync(path.join(interDir, 'assembled-graph.json'), JSON.stringify(graph, null, 2));
console.log('assembled-graph.json updated with layers and tour.');

// 5. Run validation script
const nodeIds = new Set(graph.nodes.map(n => n.id));
const issues = [];
const warnings = [];

graph.edges.forEach((e, i) => {
  if (!nodeIds.has(e.source)) issues.push(`Edge[${i}] source '${e.source}' not found`);
  if (!nodeIds.has(e.target)) issues.push(`Edge[${i}] target '${e.target}' not found`);
});

const assigned = new Map();
graph.layers.forEach(layer => {
  (layer.nodeIds || []).forEach(id => {
    if (!nodeIds.has(id)) issues.push(`Layer '${layer.id}' refs missing node '${id}'`);
    if (assigned.has(id)) issues.push(`Node '${id}' appears in multiple layers`);
    assigned.set(id, layer.id);
  });
});

allFileNodeIds.forEach(id => {
  if (!assigned.has(id)) issues.push(`File node '${id}' not in any layer`);
});

graph.tour.forEach((step, i) => {
  (step.nodeIds || []).forEach(id => {
    if (!nodeIds.has(id)) issues.push(`Tour step[${i}] refs missing node '${id}'`);
  });
});

console.log('Validation results: issues:', issues.length, 'warnings:', warnings.length);
if (issues.length > 0) {
  console.error('Issues:', issues);
}

// 6. Write final knowledge-graph.json
fs.writeFileSync(path.join(uaDir, 'knowledge-graph.json'), JSON.stringify(graph, null, 2));
console.log('Saved .ua/knowledge-graph.json successfully (' + graph.nodes.length + ' nodes, ' + graph.edges.length + ' edges).');

// 7. Write meta.json
let commitHash = 'unknown';
try {
  commitHash = execSync('git rev-parse HEAD', { cwd: root }).toString().trim();
} catch (e) {}

const meta = {
  version: "2.9.8",
  updatedAt: new Date().toISOString(),
  gitCommitHash: commitHash,
  stats: {
    totalFiles: allFileNodeIds.length,
    totalNodes: graph.nodes.length,
    totalEdges: graph.edges.length,
    totalLayers: graph.layers.length,
    totalTourSteps: graph.tour.length
  }
};
fs.writeFileSync(path.join(uaDir, 'meta.json'), JSON.stringify(meta, null, 2));
console.log('Saved .ua/meta.json successfully.');
