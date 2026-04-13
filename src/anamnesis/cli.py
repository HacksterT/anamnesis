"""Anamnesis CLI entry points."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="anamnesis",
        description="Anamnesis — knowledge management for LLM agents.",
    )
    sub = parser.add_subparsers(dest="command")

    # ─── init ─────────────────────────────────────────────────
    init_p = sub.add_parser("init", help="Initialize a knowledge directory")
    init_p.add_argument("--agent", type=str, default=None, help="Also register an agent")
    init_p.add_argument("--dir", type=str, default="knowledge", help="Knowledge directory")
    init_p.add_argument("--token-budget", type=int, default=4000)
    init_p.add_argument("--recency-budget", type=int, default=400)
    init_p.add_argument("--boluses", type=str, default="", help="Comma-separated bolus IDs to activate for this agent")

    # ─── serve ────────────────────────────────────────────────
    serve_p = sub.add_parser("serve", help="Start the REST API server")
    serve_p.add_argument("--config", type=str, default=None)
    serve_p.add_argument("--host", type=str, default=None)
    serve_p.add_argument("--port", type=int, default=None)

    # ─── assemble ─────────────────────────────────────────────
    asm_p = sub.add_parser("assemble", help="Assemble anamnesis.md")
    asm_p.add_argument("--config", type=str, default=None)

    # ─── validate ─────────────────────────────────────────────
    val_p = sub.add_parser("validate", help="Validate injection")
    val_p.add_argument("--config", type=str, default=None)

    # ─── metrics ──────────────────────────────────────────────
    met_p = sub.add_parser("metrics", help="Show injection metrics")
    met_p.add_argument("--config", type=str, default=None)
    met_p.add_argument("--json", dest="as_json", action="store_true")

    # ─── bolus ────────────────────────────────────────────────
    bolus_p = sub.add_parser("bolus", help="Manage knowledge boluses")
    bolus_sub = bolus_p.add_subparsers(dest="bolus_command")

    bl_list = bolus_sub.add_parser("list", help="List boluses")
    bl_list.add_argument("--all", dest="show_all", action="store_true", help="Include inactive")
    bl_list.add_argument("--json", dest="as_json", action="store_true")
    bl_list.add_argument("--config", type=str, default=None)

    bl_show = bolus_sub.add_parser("show", help="Show bolus content")
    bl_show.add_argument("bolus_id", type=str)
    bl_show.add_argument("--json", dest="as_json", action="store_true")
    bl_show.add_argument("--config", type=str, default=None)

    bl_create = bolus_sub.add_parser("create", help="Create a bolus")
    bl_create.add_argument("bolus_id", type=str)
    bl_create.add_argument("--title", type=str, default=None)
    bl_create.add_argument("--summary", type=str, default="")
    bl_create.add_argument("--render", type=str, default="reference", choices=["inline", "reference"])
    bl_create.add_argument("--priority", type=int, default=50)
    bl_create.add_argument("--tags", type=str, default="", help="Comma-separated tags")
    bl_create.add_argument("--file", type=str, default=None, help="Read content from file")
    bl_create.add_argument("--config", type=str, default=None)

    bl_update = bolus_sub.add_parser("update", help="Update bolus content")
    bl_update.add_argument("bolus_id", type=str)
    bl_update.add_argument("--file", type=str, default=None, help="Read content from file")
    bl_update.add_argument("--config", type=str, default=None)

    bl_delete = bolus_sub.add_parser("delete", help="Delete a bolus")
    bl_delete.add_argument("bolus_id", type=str)
    bl_delete.add_argument("--config", type=str, default=None)

    bl_activate = bolus_sub.add_parser("activate", help="Activate a bolus")
    bl_activate.add_argument("bolus_id", type=str)
    bl_activate.add_argument("--config", type=str, default=None)

    bl_deactivate = bolus_sub.add_parser("deactivate", help="Deactivate a bolus")
    bl_deactivate.add_argument("bolus_id", type=str)
    bl_deactivate.add_argument("--config", type=str, default=None)

    # ─── agent ────────────────────────────────────────────────
    agent_p = sub.add_parser("agent", help="Manage agents")
    agent_sub = agent_p.add_subparsers(dest="agent_command")

    ag_list = agent_sub.add_parser("list", help="List registered agents")
    ag_list.add_argument("--json", dest="as_json", action="store_true")
    ag_list.add_argument("--config", type=str, default=None)

    ag_show = agent_sub.add_parser("show", help="Show agent details")
    ag_show.add_argument("name", type=str)
    ag_show.add_argument("--json", dest="as_json", action="store_true")
    ag_show.add_argument("--config", type=str, default=None)

    ag_recency = agent_sub.add_parser("recency", help="Set agent recency budget")
    ag_recency.add_argument("name", type=str)
    ag_recency.add_argument("--budget", type=int, required=True, help="Token budget (0-1000)")
    ag_recency.add_argument("--config", type=str, default=None)

    # ─── Parse and dispatch ───────────────────────────────────
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "init": _cmd_init,
        "serve": _cmd_serve,
        "assemble": _cmd_assemble,
        "validate": _cmd_validate,
        "metrics": _cmd_metrics,
        "bolus": _cmd_bolus,
        "agent": _cmd_agent,
    }
    dispatch[args.command](args)


# ─── Config loading ──────────────────────────────────────────────


def _load(config_path: str | None):
    from anamnesis.api.config_loader import load_config
    return load_config(config_path)


def _load_framework(config_path: str | None):
    from anamnesis.framework import KnowledgeFramework
    config = _load(config_path)
    return KnowledgeFramework(config)


# ─── Init ────────────────────────────────────────────────────────


def _cmd_init(args) -> None:
    from anamnesis.init import init_project, register_agent

    knowledge_dir = Path(args.dir)
    config_path = init_project(knowledge_dir, token_budget=args.token_budget)
    print(f"Initialized: {knowledge_dir}/")
    print(f"Config: {config_path}")

    if args.agent:
        boluses = [b.strip() for b in args.boluses.split(",") if b.strip()] if args.boluses else []
        register_agent(
            config_path,
            args.agent,
            token_budget=args.token_budget,
            recency_budget=args.recency_budget,
            active_boluses=boluses,
        )
        print(f"Agent registered: {args.agent}")


# ─── Serve ───────────────────────────────────────────────────────


def _cmd_serve(args) -> None:
    try:
        import uvicorn
    except ImportError:
        print("uvicorn is required: uv sync --extra api", file=sys.stderr)
        sys.exit(1)

    config = _load(args.config)
    host = args.host or config.api_host
    port = args.port or config.api_port

    from anamnesis.api.server import create_app
    app = create_app(config)
    uvicorn.run(app, host=host, port=port)


# ─── Assemble ────────────────────────────────────────────────────


def _cmd_assemble(args) -> None:
    kf = _load_framework(args.config)
    path = kf.assemble()
    print(f"Assembled: {path}")


# ─── Validate ────────────────────────────────────────────────────


def _cmd_validate(args) -> None:
    from anamnesis.inject.schema import validate_injection
    kf = _load_framework(args.config)

    try:
        text = kf.get_injection()
    except ValueError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(2)

    result = validate_injection(text)
    if result.valid:
        print("OK: injection is valid")
        for w in result.warnings:
            print(f"  WARNING: {w}")
    else:
        print("FAIL: injection is invalid", file=sys.stderr)
        for e in result.errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(2)


# ─── Metrics ─────────────────────────────────────────────────────


def _cmd_metrics(args) -> None:
    kf = _load_framework(args.config)

    try:
        metrics = kf.get_injection_metrics()
    except ValueError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        print(json.dumps(metrics, indent=2))
    else:
        print(f"Tokens:      {metrics['total_tokens']} / {metrics['soft_max']} (soft max)")
        print(f"Utilization: {metrics['utilization_pct']}%")
        print(f"Status:      {metrics['status']}")
        print(f"Boluses:     {metrics['active_boluses']} active / {metrics['total_boluses']} total")


# ─── Bolus commands ──────────────────────────────────────────────


def _cmd_bolus(args) -> None:
    if args.bolus_command is None:
        print("Usage: anamnesis bolus {list,show,create,update,delete,activate,deactivate}", file=sys.stderr)
        sys.exit(1)

    dispatch = {
        "list": _bolus_list,
        "show": _bolus_show,
        "create": _bolus_create,
        "update": _bolus_update,
        "delete": _bolus_delete,
        "activate": _bolus_activate,
        "deactivate": _bolus_deactivate,
    }
    dispatch[args.bolus_command](args)


def _bolus_list(args) -> None:
    kf = _load_framework(args.config)
    boluses = kf.list_boluses(active_only=not args.show_all)

    if args.as_json:
        print(json.dumps(boluses, indent=2, default=str))
        return

    if not boluses:
        print("No boluses found.")
        return

    for b in boluses:
        status = "active" if b.get("active", True) else "inactive"
        render = b.get("render", "reference")
        print(f"  {b['id']:30s} [{render:9s}] [{status:8s}] {b.get('summary', '')}")


def _bolus_show(args) -> None:
    kf = _load_framework(args.config)
    try:
        content = kf.read_bolus(args.bolus_id)
        meta = kf.get_bolus_metadata(args.bolus_id)
    except KeyError:
        print(f"Bolus '{args.bolus_id}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        print(json.dumps({"id": args.bolus_id, "metadata": meta, "content": content}, indent=2, default=str))
        return

    print(f"ID:       {meta['id']}")
    print(f"Title:    {meta.get('title', '')}")
    print(f"Render:   {meta.get('render', 'reference')}")
    print(f"Priority: {meta.get('priority', 50)}")
    print(f"Active:   {meta.get('active', True)}")
    print(f"Tags:     {', '.join(meta.get('tags', []))}")
    print(f"Summary:  {meta.get('summary', '')}")
    print(f"---")
    print(content)


def _read_content(args) -> str:
    """Read content from --file flag or stdin."""
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    print("Provide content via --file or stdin.", file=sys.stderr)
    sys.exit(1)


def _bolus_create(args) -> None:
    kf = _load_framework(args.config)
    content = _read_content(args)
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    try:
        kf.create_bolus(
            args.bolus_id,
            content,
            title=args.title,
            summary=args.summary,
            render=args.render,
            priority=args.priority,
            tags=tags,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Created: {args.bolus_id}")


def _bolus_update(args) -> None:
    kf = _load_framework(args.config)
    content = _read_content(args)

    try:
        kf.update_bolus(args.bolus_id, content)
    except KeyError:
        print(f"Bolus '{args.bolus_id}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Updated: {args.bolus_id}")


def _bolus_delete(args) -> None:
    kf = _load_framework(args.config)
    deleted = kf.delete_bolus(args.bolus_id)
    if not deleted:
        print(f"Bolus '{args.bolus_id}' not found.", file=sys.stderr)
        sys.exit(1)
    print(f"Deleted: {args.bolus_id}")


def _bolus_set_active(args, active: bool, verb: str) -> None:
    kf = _load_framework(args.config)
    try:
        kf.set_bolus_active(args.bolus_id, active)
    except KeyError:
        print(f"Bolus '{args.bolus_id}' not found.", file=sys.stderr)
        sys.exit(1)
    print(f"{verb}: {args.bolus_id}")


def _bolus_activate(args) -> None:
    _bolus_set_active(args, True, "Activated")


def _bolus_deactivate(args) -> None:
    _bolus_set_active(args, False, "Deactivated")


# ─── Agent commands ──────────────────────────────────────────────


def _cmd_agent(args) -> None:
    if args.agent_command is None:
        print("Usage: anamnesis agent {list,show,recency}", file=sys.stderr)
        sys.exit(1)

    dispatch = {
        "list": _agent_list,
        "show": _agent_show,
        "recency": _agent_recency,
    }
    dispatch[args.agent_command](args)


def _agent_list(args) -> None:
    from anamnesis.init import load_project_config

    config_path = _find_config(args.config)
    project = load_project_config(config_path)
    agents = project.get("agents", {})

    if args.as_json:
        print(json.dumps(agents, indent=2, default=str))
        return

    if not agents:
        print("No agents registered. Use 'anamnesis init --agent <name>' to register one.")
        return

    for name, cfg in agents.items():
        budget = cfg.get("token_budget", 4000)
        recency = cfg.get("recency_budget", 400)
        print(f"  {name:20s}  budget: {budget}  recency: {recency}")


def _agent_show(args) -> None:
    from anamnesis.init import load_project_config

    config_path = _find_config(args.config)
    project = load_project_config(config_path)
    agents = project.get("agents", {})

    if args.name not in agents:
        print(f"Agent '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)

    agent = agents[args.name]

    if args.as_json:
        print(json.dumps({"name": args.name, **agent}, indent=2, default=str))
        return

    print(f"Name:           {args.name}")
    print(f"Token budget:   {agent.get('token_budget', 4000)}")
    print(f"Recency budget: {agent.get('recency_budget', 400)}")
    print(f"Knowledge dir:  {agent.get('knowledge_dir', 'default')}")


def _agent_recency(args) -> None:
    from anamnesis.init import load_project_config, save_project_config

    if not 0 <= args.budget <= 1000:
        print("Recency budget must be 0-1000.", file=sys.stderr)
        sys.exit(1)

    config_path = _find_config(args.config)
    project = load_project_config(config_path)
    agents = project.setdefault("agents", {})

    if args.name not in agents:
        print(f"Agent '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)

    agents[args.name]["recency_budget"] = args.budget
    save_project_config(config_path, project)
    print(f"Set recency budget for '{args.name}': {args.budget} tokens")


def _find_config(config_path: str | None) -> Path:
    """Find the anamnesis.yaml config file."""
    if config_path:
        p = Path(config_path)
        if p.exists():
            return p
        print(f"Config not found: {p}", file=sys.stderr)
        sys.exit(1)

    for name in ["anamnesis.yaml", "anamnesis.yml"]:
        p = Path(name)
        if p.exists():
            return p

    print("No anamnesis.yaml found. Run 'anamnesis init' first.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
