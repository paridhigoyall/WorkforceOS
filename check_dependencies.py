import os
import re
import sys

# Define base paths
WORKSPACE_ROOT = r"C:\Users\Hp\WorkforceOS"
APP_DIR = os.path.join(WORKSPACE_ROOT, "backend", "app")

print(f"Scanning APP_DIR: {APP_DIR}")

# 1. Gather all existing models, schemas, repositories, services, routes
components = {
    "models": set(),
    "schemas": set(),
    "repositories": set(),
    "services": set(),
    "routes": set(),
}

# Scan directory structures
for root, dirs, files in os.walk(APP_DIR):
    for f in files:
        if not f.endswith(".py") or f.startswith("__"):
            continue
        rel_dir = os.path.relpath(root, APP_DIR)
        name = os.path.splitext(f)[0]
        
        if rel_dir == "models":
            components["models"].add(name)
        elif rel_dir == "schemas":
            components["schemas"].add(name)
        elif rel_dir == "repositories":
            components["repositories"].add(name)
        elif rel_dir == "services":
            components["services"].add(name)
        elif rel_dir == "api" or rel_dir.startswith("api"):
            components["routes"].add(name)

print("Detected Components:")
for k, v in components.items():
    print(f"  {k}: {sorted(list(v))}")

# Patterns to scan
# Search for imports like:
# from app.models.visit_diagnosis import VisitDiagnosis
# from app.repositories import user_repository
# from app.models import ...
# import ...

errors = []

for root, dirs, files in os.walk(APP_DIR):
    for f in files:
        if not f.endswith(".py"):
            continue
        filepath = os.path.join(root, f)
        rel_path = os.path.relpath(filepath, WORKSPACE_ROOT)
        
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            lines = content.splitlines()
            
            # Check for broken imports or references
            for idx, line in enumerate(lines, 1):
                # 1. Model imports
                # Matches: from app.models.XYZ import ...
                model_import_match = re.search(r"from\s+app\.models\.(\w+)\s+import", line)
                if model_import_match:
                    model_name = model_import_match.group(1)
                    if model_name not in components["models"]:
                        errors.append({
                            "file": rel_path,
                            "line": idx,
                            "type": "Broken Model Import",
                            "detail": f"Imports non-existent model module 'app.models.{model_name}': {line.strip()}"
                        })
                
                # Matches: from app.repositories import XYZ
                repo_import_match = re.search(r"from\s+app\.repositories\s+import\s+(\w+)", line)
                if repo_import_match:
                    repo_name = repo_import_match.group(1)
                    if repo_name not in components["repositories"] and repo_name != "audit_repository":
                        errors.append({
                            "file": rel_path,
                            "line": idx,
                            "type": "Broken Repository Import",
                            "detail": f"Imports non-existent repository '{repo_name}': {line.strip()}"
                        })

                # Matches: from app.schemas.XYZ import ...
                schema_import_match = re.search(r"from\s+app\.schemas\.(\w+)\s+import", line)
                if schema_import_match:
                    schema_name = schema_import_match.group(1)
                    if schema_name not in components["schemas"]:
                        errors.append({
                            "file": rel_path,
                            "line": idx,
                            "type": "Broken Schema Import",
                            "detail": f"Imports non-existent schema module 'app.schemas.{schema_name}': {line.strip()}"
                        })

                # 2. Check for is_deleted usage in queries or properties
                if "is_deleted" in line and not rel_path.endswith("check_dependencies.py"):
                    errors.append({
                        "file": rel_path,
                        "line": idx,
                        "type": "is_deleted Reference",
                        "detail": f"References 'is_deleted' which is not in DB models: {line.strip()}"
                    })

                # 3. Check for UUID references in repositories or deps
                if ("uuid.UUID" in line or "UUID" in line) and "schemas" not in rel_path and "response_models.py" not in rel_path and not rel_path.endswith("check_dependencies.py"):
                    errors.append({
                        "file": rel_path,
                        "line": idx,
                        "type": "UUID Reference",
                        "detail": f"References UUID which is inconsistent with Integer PKs: {line.strip()}"
                    })

                # 4. Check for ProductIngredient usage
                if "ProductIngredient" in line and not rel_path.endswith("check_dependencies.py"):
                    errors.append({
                        "file": rel_path,
                        "line": idx,
                        "type": "ProductIngredient Reference",
                        "detail": f"References 'ProductIngredient' which is not implemented: {line.strip()}"
                    })

                # 5. Check for Farm references in repositories or files
                if ("Farm" in line or "farm_id" in line or "Visit.farm" in line) and "farm_repository.py" not in rel_path and not rel_path.endswith("check_dependencies.py"):
                    errors.append({
                        "file": rel_path,
                        "line": idx,
                        "type": "Farm Reference",
                        "detail": f"References 'Farm' which is not in DB models: {line.strip()}"
                    })

# Generate report markdown
report_path = os.path.join(WORKSPACE_ROOT, "backend", "dependency_validation_report.md")
with open(report_path, "w", encoding="utf-8") as rep:
    rep.write("# Dependency Validation Report\n\n")
    rep.write("This report lists all broken imports, non-existent references, and schema/repository mismatches.\n\n")
    if not errors:
        rep.write("### ✅ No Dependency Issues Found!\n")
    else:
        rep.write(f"### ❌ Found {len(errors)} Dependency Issues\n\n")
        rep.write("| File | Line | Type | Details |\n")
        rep.write("| --- | --- | --- | --- |\n")
        for err in errors:
            rep.write(f"| `{err['file']}` | {err['line']} | **{err['type']}** | `{err['detail']}` |\n")

print(f"Report written to: {report_path}")
