"""OpenAI function-calling schemas for every tool the agent can use."""

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from disk and return its contents with line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file.",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Line number to start reading from (1-indexed). Default 1.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of lines to read. Default 500.",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file, creating it (and any parent directories) if it does not exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "content": {"type": "string", "description": "Full content to write."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Replace an exact string in a file. Fails if old_string is not found "
                "or appears more than once. Use read_file first to get the exact text."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "old_string": {"type": "string", "description": "Exact string to find."},
                    "new_string": {"type": "string", "description": "Replacement string."},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "Execute a shell command and return its stdout + stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run."},
                    "description": {
                        "type": "string",
                        "description": "Short human-readable description of what this command does.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds. Default 30.",
                    },
                },
                "required": ["command", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob_files",
            "description": "Find files matching a glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern, e.g. '**/*.py' or 'src/**/*.ts'.",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search in. Defaults to working directory.",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_files",
            "description": "Search file contents with a regex pattern. Returns matching lines with file path and line number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for.",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory or file to search. Defaults to working directory.",
                    },
                    "glob": {
                        "type": "string",
                        "description": "File glob filter, e.g. '*.py'. Optional.",
                    },
                    "case_insensitive": {
                        "type": "boolean",
                        "description": "Case-insensitive search. Default false.",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory to list. Defaults to working directory.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ingest_documents",
            "description": (
                "Chunk, embed, and index a file or directory into the vector store so it "
                "can be searched with retrieve_context. Re-ingesting the same source is "
                "idempotent (old chunks are replaced)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File or directory to ingest.",
                    },
                    "collection": {
                        "type": "string",
                        "description": "Qdrant collection name. Defaults to config value ('default').",
                    },
                    "chunk_size": {
                        "type": "integer",
                        "description": "Words per chunk. Default 500.",
                    },
                    "chunk_overlap": {
                        "type": "integer",
                        "description": "Overlapping words between consecutive chunks. Default 50.",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_context",
            "description": (
                "Semantic search over ingested documents. Returns the top-k most relevant "
                "chunks for the given query. Call this before answering questions about "
                "documents that have been indexed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural-language search query.",
                    },
                    "collection": {
                        "type": "string",
                        "description": "Qdrant collection to search. Defaults to config value ('default').",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of chunks to return. Default 5.",
                    },
                },
                "required": ["query"],
            },
        },
    },
]
