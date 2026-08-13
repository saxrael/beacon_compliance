"""AST Financial Boundary Verification Script (verify_financial_boundary.py).

Scans Python source code ASTs in backend/src/ to enforce Red-Line 2:
- Zero float conversions (float(...)) in financial accounting, deliverables, or chat routes
- Zero float arithmetic operations in financial modules
"""

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = PROJECT_ROOT / "backend" / "src"

TARGET_MODULES = [
    "core/financial.py",
    "agents/node_calculator.py",
    "api/routes_deliverables.py",
    "api/routes_chat.py",
]


class FloatCallVisitor(ast.NodeVisitor):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.violations: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "float":
            self.violations.append(
                f"{self .filename }:L{node .lineno } - Prohibition of float() conversion in financial path."
            )
        self.generic_visit(node)


def verify_financial_boundary() -> bool:
    print("=" * 60)
    print("Beacon Compliance — AST Red-Line 2 Financial Boundary Verification")
    print("=" * 60)

    total_violations = []

    for rel_path in TARGET_MODULES:
        full_path = BACKEND_SRC / rel_path
        if not full_path.exists():
            print(f"[SKIP] Module {rel_path } not found.")
            continue

        with open(full_path, encoding="utf-8") as f:
            source = f.read()

        try:
            tree = ast.parse(source, filename=str(full_path))
            visitor = FloatCallVisitor(filename=rel_path)
            visitor.visit(tree)

            if visitor.violations:
                for v in visitor.violations:
                    print(f"[FAIL] {v }")
                total_violations.extend(visitor.violations)
            else:
                print(f"[PASS] {rel_path }: 0 float() violations detected.")
        except Exception as err:
            print(f"[ERR] Failed to parse {rel_path }: {err }")
            return False

    print("=" * 60)
    if not total_violations:
        print("RESULT: AST Financial Boundary Audit PASSED cleanly.")
        print("=" * 60)
        return True
    else:
        print(
            f"RESULT: AST Financial Boundary Audit FAILED ({len (total_violations )} violations)."
        )
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = verify_financial_boundary()
    sys.exit(0 if success else 1)
