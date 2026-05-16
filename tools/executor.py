from __future__ import annotations

import atexit
import json

from config import Config
from tools.file_ops import read_file, write_file, edit_file
from tools.git import git_status, git_diff, git_log, git_commit
from tools.shell import run_bash
from tools.search import glob_files, grep_files, list_dir
from tools.web import fetch_url
from tools.symbols import get_symbol, replace_symbol

# RAG singletons — lazily initialised on first use so that the agent
# starts without requiring Qdrant/embedder to be available.
_embedder = None
_store = None


def _close_rag() -> None:
    if _store is not None:
        try:
            _store._client.close()
        except Exception:
            pass


atexit.register(_close_rag)


def _get_rag(config: Config):
    global _embedder, _store
    if _embedder is None:
        from rag.embedder import Embedder
        _embedder = Embedder(base_url=config.base_url, model=config.embed_model)
    if _store is None:
        from rag.vector_store import VectorStore
        _store = VectorStore(url=config.qdrant_url, dimension=_embedder.dimension)
    return _embedder, _store


def execute_tool(name: str, arguments_json: str, config: Config) -> str:
    """Dispatch a tool call by name and return the result as a string."""
    try:
        args = json.loads(arguments_json) if arguments_json.strip() else {}
    except json.JSONDecodeError as e:
        return f"Error: could not parse tool arguments: {e}\nRaw: {arguments_json}"

    wd = config.working_dir

    try:
        if name == "read_file":
            return read_file(
                args["path"],
                offset=args.get("offset", 1),
                limit=args.get("limit", 500),
                working_dir=wd,
            )
        elif name == "write_file":
            return write_file(args["path"], args["content"], working_dir=wd)
        elif name == "edit_file":
            return edit_file(
                args["path"],
                args["old_string"],
                args["new_string"],
                replace_all=args.get("replace_all", False),
                working_dir=wd,
            )
        elif name == "run_bash":
            return run_bash(
                args["command"],
                description=args.get("description", ""),
                timeout=args.get("timeout", config.bash_timeout),
                working_dir=wd,
            )
        elif name == "glob_files":
            return glob_files(args["pattern"], path=args.get("path"), working_dir=wd)
        elif name == "grep_files":
            return grep_files(
                args["pattern"],
                path=args.get("path"),
                glob=args.get("glob"),
                case_insensitive=args.get("case_insensitive", False),
                working_dir=wd,
            )
        elif name == "list_dir":
            return list_dir(path=args.get("path"), working_dir=wd)
        elif name == "ingest_documents":
            from rag.ingestion import ingest
            embedder, store = _get_rag(config)
            return ingest(
                path=args["path"],
                collection=args.get("collection", config.rag_collection),
                embedder=embedder,
                store=store,
                chunk_size=args.get("chunk_size", config.rag_chunk_size),
                chunk_overlap=args.get("chunk_overlap", config.rag_chunk_overlap),
                working_dir=wd,
            )
        elif name == "retrieve_context":
            from rag.ingestion import retrieve
            embedder, store = _get_rag(config)
            return retrieve(
                query=args["query"],
                collection=args.get("collection", config.rag_collection),
                embedder=embedder,
                store=store,
                top_k=args.get("top_k", 5),
            )
        elif name == "git_status":
            return git_status(working_dir=args.get("path", wd))
        elif name == "git_diff":
            return git_diff(
                path=args.get("path"),
                staged=args.get("staged", False),
                commit=args.get("commit"),
                working_dir=wd,
            )
        elif name == "git_log":
            return git_log(
                n=args.get("n", 10),
                path=args.get("path"),
                oneline=args.get("oneline", True),
                working_dir=wd,
            )
        elif name == "git_commit":
            return git_commit(
                message=args["message"],
                files=args.get("files"),
                stage_all=args.get("all", False),
                working_dir=wd,
            )
        elif name == "fetch_url":
            return fetch_url(
                url=args["url"],
                max_chars=args.get("max_chars", 8000),
            )
        elif name == "get_symbol":
            return get_symbol(args["path"], args["name"])
        elif name == "replace_symbol":
            return replace_symbol(args["path"], args["name"], args["new_source"])
        else:
            return f"Error: unknown tool '{name}'"
    except KeyError as e:
        return f"Error: missing required argument {e} for tool '{name}'"
    except Exception as e:
        return f"Error executing tool '{name}': {e}"
