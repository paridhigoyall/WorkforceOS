import os
import re
import sys

# Ensure UTF-8 output encoding if supported by stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Dynamic path resolution relative to script location
WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(WORKSPACE_ROOT, "backend", "app")
MAIN_PY_PATH = os.path.join(APP_DIR, "main.py")
MODELS_INIT_PATH = os.path.join(APP_DIR, "models", "__init__.py")

print("=" * 60)
print(" WorkForceOS Static Dependency & Schema Audit")
print(f" Target Directory: {APP_DIR}")
print("=" * 60)

# 1. Gather all existing modules across layers
components = {
    "models": set(),
    "schemas": set(),
    "repositories": set(),
    "services": set(),
    "routes": set(),
    "core": set(),
    "dependencies": set(),
}

# Scan backend directory structures
for root, dirs, files in os.walk(APP_DIR):
    for f in files:
        if not f.endswith(".py") or f.startswith("__"):
            continue
        rel_dir = os.path.relpath(root, APP_DIR)
        name = os.path.splitext(f)[0]
        
        parts = rel_dir.split(os.sep)
        if parts[0] in components:
            components[parts[0]].add(name)
        elif len(parts) > 1 and parts[0] == "api":
            if parts[1] == "routes":
                components["routes"].add(name)
            elif parts[1] == "dependencies":
                components["dependencies"].add(name)

print("\nDetected Application Modules:")
for k, v in components.items():
    print(f"  * {k.capitalize()}: {sorted(list(v))}")

errors = []

# 2. Audit Route Registrations in main.py
if os.path.exists(MAIN_PY_PATH):
    with open(MAIN_PY_PATH, "r", encoding="utf-8") as f:
        main_content = f.read()
        for route_module in components["routes"]:
            pattern = rf"from\s+app\.api\.routes\.{route_module}\s+import\s+router"
            if not re.search(pattern, main_content):
                errors.append({
                    "file": os.path.relpath(MAIN_PY_PATH, WORKSPACE_ROOT),
                    "line": 1,
                    "type": "Unmounted Route",
                    "detail": f"Route module 'app.api.routes.{route_module}' is not imported or mounted in main.py"
                })

# 3. Audit Model Exports in models/__init__.py
if os.path.exists(MODELS_INIT_PATH):
    with open(MODELS_INIT_PATH, "r", encoding="utf-8") as f:
        models_init_content = f.read()
        for model_module in components["models"]:
            if model_module == "base":
                continue
            pattern = rf"from\s+app\.models\.{model_module}\s+import"
            if not re.search(pattern, models_init_content):
                errors.append({
                    "file": os.path.relpath(MODELS_INIT_PATH, WORKSPACE_ROOT),
                    "line": 1,
                    "type": "Missing Model Export",
                    "detail": f"Model module 'app.models.{model_module}' is not re-exported in app/models/__init__.py"
                })

# 4. Scan files for broken imports and structural mismatches
for root, dirs, files in os.walk(APP_DIR):
    for f in files:
        if not f.endswith(".py"):
            continue
        filepath = os.path.join(root, f)
        rel_path = os.path.relpath(filepath, WORKSPACE_ROOT)
        
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            lines = content.splitlines()
            
            for idx, line in enumerate(lines, 1):
                # Ignore comments
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue

                # Model module imports check
                model_match = re.search(r"from\s+app\.models\.(\w+)\s+import", line)
                if model_match:
                    model_name = model_match.group(1)
                    if model_name not in components["models"]:
                        errors.append({
                            "file": rel_path,
                            "line": idx,
                            "type": "Broken Model Import",
                            "detail": f"Imports non-existent model module 'app.models.{model_name}': {stripped}"
                        })

                # Schema module imports check
                schema_match = re.search(r"from\s+app\.schemas\.(\w+)\s+import", line)
                if schema_match:
                    schema_name = schema_match.group(1)
                    if schema_name not in components["schemas"]:
                        errors.append({
                            "file": rel_path,
                            "line": idx,
                            "type": "Broken Schema Import",
                            "detail": f"Imports non-existent schema module 'app.schemas.{schema_name}': {stripped}"
                        })

                # Repository module imports check
                repo_match = re.search(r"from\s+app\.repositories\.(\w+)\s+import", line)
                if repo_match:
                    repo_name = repo_match.group(1)
                    if repo_name not in components["repositories"]:
                        errors.append({
                            "file": rel_path,
                            "line": idx,
                            "type": "Broken Repository Import",
                            "detail": f"Imports non-existent repository module 'app.repositories.{repo_name}': {stripped}"
                        })

                # Service module imports check
                service_match = re.search(r"from\s+app\.services\.(\w+)\s+import", line)
                if service_match:
                    service_name = service_match.group(1)
                    if service_name not in components["services"]:
                        errors.append({
                            "file": rel_path,
                            "line": idx,
                            "type": "Broken Service Import",
                            "detail": f"Imports non-existent service module 'app.services.{service_name}': {stripped}"
                        })

                # Check for legacy integer ID typehints in service or repository signatures
                if re.search(r"def\s+\w+\(.*?\bid:\s*int\b", line) or re.search(r"def\s+\w+\(.*?\buser_id:\s*int\b", line):
                    errors.append({
                        "file": rel_path,
                        "line": idx,
                        "type": "Non-UUID Type Hint",
                        "detail": f"Uses integer primary key typehint instead of UUID: {stripped}"
                    })

# 5. Generate Markdown Audit Report
report_path = os.path.join(WORKSPACE_ROOT, "backend", "dependency_validation_report.md")
with open(report_path, "w", encoding="utf-8") as rep:
    rep.write("# Dependency Validation Report\n\n")
    rep.write("This report details static code analysis results for module imports, router mounts, model re-exports, and architectural constraints.\n\n")
    if not errors:
        rep.write("### [PASS] All Dependency & Schema Audits Passed Cleanly!\n")
    else:
        rep.write(f"### [FAIL] Found {len(errors)} Issues\n\n")
        rep.write("| File | Line | Type | Details |\n")
        rep.write("| --- | --- | --- | --- |\n")
        for err in errors:
            rep.write(f"| `{err['file']}` | {err['line']} | **{err['type']}** | `{err['detail']}` |\n")

print("\n" + "=" * 60)
if not errors:
    print(" [PASS] SUCCESS: No static dependency or schema issues detected!")
else:
    print(f" [FAIL] ERROR: Detected {len(errors)} static analysis issues.")
print(f" Full report written to: {report_path}")
print("=" * 60 + "\n")

if errors:
    sys.exit(1)
else:
    sys.exit(0)


