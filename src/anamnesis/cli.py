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

    # serve
    serve_p = sub.add_parser("serve", help="Start the REST API server")
    serve_p.add_argument("--config", type=str, default=None, help="Path to config file")
    serve_p.add_argument("--host", type=str, default=None, help="Override host")
    serve_p.add_argument("--port", type=int, default=None, help="Override port")

    # assemble
    asm_p = sub.add_parser("assemble", help="Assemble anamnesis.md and write to disk")
    asm_p.add_argument("--config", type=str, default=None)

    # validate
    val_p = sub.add_parser("validate", help="Validate config and bolus structure")
    val_p.add_argument("--config", type=str, default=None)

    # metrics
    met_p = sub.add_parser("metrics", help="Show injection metrics")
    met_p.add_argument("--config", type=str, default=None)
    met_p.add_argument("--json", dest="as_json", action="store_true")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "serve":
        _cmd_serve(args)
    elif args.command == "assemble":
        _cmd_assemble(args)
    elif args.command == "validate":
        _cmd_validate(args)
    elif args.command == "metrics":
        _cmd_metrics(args)


def _load(config_path: str | None):
    from anamnesis.api.config_loader import load_config
    return load_config(config_path)


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


def _cmd_assemble(args) -> None:
    from anamnesis.framework import KnowledgeFramework
    config = _load(args.config)
    kf = KnowledgeFramework(config)
    path = kf.assemble()
    print(f"Assembled: {path}")


def _cmd_validate(args) -> None:
    from anamnesis.framework import KnowledgeFramework
    from anamnesis.inject.schema import validate_injection
    config = _load(args.config)
    kf = KnowledgeFramework(config)

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


def _cmd_metrics(args) -> None:
    from anamnesis.framework import KnowledgeFramework
    config = _load(args.config)
    kf = KnowledgeFramework(config)

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


if __name__ == "__main__":
    main()
