import ast
from pathlib import Path


ROUTERS = Path(__file__).resolve().parents[1] / "app" / "routers"
MUTATION_METHODS = {"post", "put", "patch", "delete"}
PROTECTED_MODULES = (
    "curation.py",
    "dossiers.py",
    "evidence_intelligence.py",
    "formulations.py",
    "interactions.py",
    "process_knowledge.py",
    "regulatory.py",
    "vendor_materials.py",
    "organizations.py",
    "vendors.py",
    "analytical_methods.py",
    "enrichment.py",
    "agents.py",
    "bioinformatics.py",
    "research.py",
    "auth.py",
)


def _route_method(node):
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
            continue
        owner = decorator.func.value
        if isinstance(owner, ast.Name) and owner.id == "router" and decorator.func.attr in MUTATION_METHODS:
            return decorator.func.attr, decorator
    return None, None


def _has_rate_limit_dependency(decorator):
    dependencies = next((item.value for item in decorator.keywords if item.arg == "dependencies"), None)
    if not isinstance(dependencies, (ast.List, ast.Tuple)):
        return False
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"authenticated_write_rate_limit", "public_request_rate_limit"}
        for dependency in dependencies.elts
        for node in ast.walk(dependency)
    )


def _has_direct_rate_limit(function):
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "enforce_rate_limit"
        for node in ast.walk(function)
    )


def test_sensitive_mutation_routes_have_shared_rate_limits():
    uncovered = []
    total = 0
    for filename in PROTECTED_MODULES:
        tree = ast.parse((ROUTERS / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            method, decorator = _route_method(node)
            if method is None:
                continue
            total += 1
            if not _has_rate_limit_dependency(decorator) and not _has_direct_rate_limit(node):
                uncovered.append(f"{filename}:{node.name}:{method}")
    assert total >= 40, "The route audit unexpectedly found too few mutation endpoints."
    assert uncovered == [], "Sensitive mutation routes need shared per-user limits: " + ", ".join(uncovered)


PUBLIC_MUTATION_ALLOWLIST = {
    ("auth.py", "register"),
    ("auth.py", "login"),
    ("bioinformatics.py", "analyze_sequence"),
    ("bioinformatics.py", "align_sequences"),
    ("research.py", "synthesize_research_answer"),
}


def _has_authenticated_user_dependency(function, decorator):
    for argument in [*function.args.args, *function.args.kwonlyargs]:
        if argument.annotation is not None and any(
            isinstance(node, ast.Name) and node.id == "get_current_user"
            for node in ast.walk(argument.annotation)
        ):
            return True
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "authenticated_write_rate_limit"
        for keyword in decorator.keywords if keyword.arg == "dependencies"
        for node in ast.walk(keyword.value)
    )


def test_mutation_routes_require_authentication_or_explicit_public_allowlisting():
    unprotected = []
    public_without_limit = []
    for filename in PROTECTED_MODULES:
        tree = ast.parse((ROUTERS / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            method, decorator = _route_method(node)
            if method is None:
                continue
            route = (filename, node.name)
            if route in PUBLIC_MUTATION_ALLOWLIST:
                has_public_limit = (
                    _has_rate_limit_dependency(decorator)
                    or _has_direct_rate_limit(node)
                )
                if not has_public_limit:
                    public_without_limit.append(f"{filename}:{node.name}")
            elif not _has_authenticated_user_dependency(node, decorator):
                unprotected.append(f"{filename}:{node.name}:{method}")
    assert public_without_limit == [], "Public mutation allowlist entries need network/IP rate limits: " + ", ".join(public_without_limit)
    assert unprotected == [], "Mutation routes need an authenticated user dependency or explicit public allowlist: " + ", ".join(unprotected)
