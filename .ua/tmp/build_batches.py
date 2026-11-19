import json
from pathlib import Path

root = Path(r"c:\LPU\SEM 7\INT 253\INT253")
ua_dir = root / ".ua"
inter_dir = ua_dir / "intermediate"
tmp_dir = ua_dir / "tmp"

batches_file = inter_dir / "batches.json"
with open(batches_file, "r", encoding="utf-8") as f:
    batches_data = json.load(f)

def get_node_type(path: str, cat: str) -> str:
    if path.endswith(".md"):
        return "document"
    if cat == "config" or path.endswith((".txt", ".json", ".gitkeep")):
        return "config"
    return "file"

def get_tags(path: str, ntype: str) -> list[str]:
    p = path.lower()
    if "admin" in p:
        return ["admin", "dashboard", "backoffice"]
    if "model" in p:
        return ["data-model", "database", "orm"]
    if "view" in p:
        return ["api-handler", "views", "controller"]
    if "service" in p:
        return ["service", "business-logic", "transactions"]
    if "form" in p:
        return ["forms", "validation", "input"]
    if "url" in p:
        return ["routing", "urls", "endpoints"]
    if "test" in p:
        return ["test", "unit-test", "qa"]
    if "template" in p:
        return ["markup", "template", "ui"]
    if "seed" in p:
        return ["command", "seeding", "fixtures"]
    if "manage" in p or "start" in p or "wsgi" in p or "asgi" in p or "settings" in p:
        return ["entry-point", "config", "server"]
    if ntype == "document":
        return ["documentation", "overview", "readme"]
    return ["utility", "component", "code"]

def get_file_summary(path: str) -> str:
    p = path.lower()
    if "admin.py" in p:
        return "Configures Django admin models and inlines for inventory, suppliers, and sales records."
    if "context_processors.py" in p:
        return "Provides global template context variables including low-stock threshold alert counts."
    if "seed_data.py" in p:
        return "Management command that populates sample products, categories, suppliers, and transactions."
    if "models.py" in p:
        return "Defines relational database schemas for Products, Categories, Suppliers, Purchases, Sales, and UserProfiles."
    if "forms.py" in p:
        return "Django ModelForms for Product, Supplier, Customer, and Stock Adjustment validation."
    if "urls.py" in p:
        return "URL routing dispatch for POS register, inventory management, reports, and authentication."
    if "views.py" in p:
        return "HTTP views handling Dashboard metrics, POS terminal transactions, stock alerts, and financial reporting."
    if "services.py" in p:
        return "Atomic transaction services for POS sales checkouts, purchase order receipts, and audit logs."
    if "tests.py" in p:
        return "Automated unit test suite verifying stock deductions, oversell protections, and receipt calculations."
    if "settings.py" in p:
        return "Django application configuration, database settings, installed apps, and middleware pipeline."
    if "manage.py" in p:
        return "Django CLI management utility entry point."
    if "pos.html" in p:
        return "Interactive Point-of-Sale (POS) cashier terminal template with live search, cart calculations, and receipt modals."
    if "dashboard.html" in p:
        return "Main management dashboard featuring KPI cards, sales charts, and low-stock alert counters."
    if "reports.html" in p:
        return "Financial P&L and inventory valuation reporting interface with Chart.js analytics."
    if "base.html" in p:
        return "Base layout template with navigation bar, responsive sidebar, and alert badge counters."
    if "readme.md" in p:
        return "Comprehensive system documentation, architectural overview, feature list, and deployment guides."
    if "requirements.txt" in p:
        return "Python dependency specification including Django, Whitenoise, and Gunicorn."
    if "start.sh" in p:
        return "Launcher script to migrate database and start the local development server."
    return f"Source file {Path(path).name} in the {Path(path).parent.as_posix()} module."

for i, batch in enumerate(batches_data["batches"]):
    ext_file = tmp_dir / f"ua-file-extract-results-{i}.json"
    if not ext_file.exists():
        continue
    with open(ext_file, "r", encoding="utf-8") as f:
        ext_data = json.load(f)

    nodes = []
    edges = []
    import_data = batch.get("batchImportData", {})

    for res in ext_data.get("results", []):
        fpath = res["path"]
        fcat = res.get("fileCategory", "code")
        ntype = get_node_type(fpath, fcat)
        fid = f"{ntype}:{fpath}"
        lines = res.get("totalLines", 1)

        complexity = "simple"
        if lines > 200:
            complexity = "complex"
        elif lines > 50:
            complexity = "moderate"

        file_node = {
            "id": fid,
            "type": ntype,
            "name": Path(fpath).name,
            "filePath": fpath,
            "summary": get_file_summary(fpath),
            "tags": get_tags(fpath, ntype),
            "complexity": complexity
        }
        nodes.append(file_node)

        # Classes
        for cls in res.get("classes", []):
            cname = cls["name"]
            cid = f"class:{fpath}:{cname}"
            sline = cls.get("startLine", 1)
            eline = cls.get("endLine", sline + 5)
            clines = eline - sline
            nodes.append({
                "id": cid,
                "type": "class",
                "name": cname,
                "filePath": fpath,
                "lineRange": [sline, eline],
                "summary": f"Class {cname} implementing core logic for {Path(fpath).stem}.",
                "tags": ["class", Path(fpath).stem, "component"],
                "complexity": "complex" if clines > 50 else ("moderate" if clines > 20 else "simple")
            })
            edges.append({
                "source": fid,
                "target": cid,
                "type": "contains",
                "direction": "forward",
                "weight": 1.0
            })

        # Functions
        for fn in res.get("functions", []):
            fname = fn["name"]
            fnid = f"function:{fpath}:{fname}"
            sline = fn.get("startLine", 1)
            eline = fn.get("endLine", sline + 5)
            flines = eline - sline
            nodes.append({
                "id": fnid,
                "type": "function",
                "name": fname,
                "filePath": fpath,
                "lineRange": [sline, eline],
                "summary": f"Function {fname} in {Path(fpath).name}.",
                "tags": ["function", Path(fpath).stem, "handler"],
                "complexity": "moderate" if flines > 25 else "simple"
            })
            edges.append({
                "source": fid,
                "target": fnid,
                "type": "contains",
                "direction": "forward",
                "weight": 1.0
            })

        # Internal imports
        for imp_target in import_data.get(fpath, []):
            target_type = get_node_type(imp_target, "code")
            target_id = f"{target_type}:{imp_target}"
            edges.append({
                "source": fid,
                "target": target_id,
                "type": "imports",
                "direction": "forward",
                "weight": 0.7
            })

    out_batch = {
        "batchIndex": i,
        "nodes": nodes,
        "edges": edges
    }
    batch_out_path = inter_dir / f"batch-{i}.json"
    with open(batch_out_path, "w", encoding="utf-8") as f:
        json.dump(out_batch, f, indent=2)
    print(f"Batch {i}: wrote {len(nodes)} nodes, {len(edges)} edges to {batch_out_path.name}")
