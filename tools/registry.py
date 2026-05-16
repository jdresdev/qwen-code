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
                "Replace a string in a file. Fails if old_string is not found. "
                "Fails if old_string appears more than once unless replace_all=true. "
                "Use read_file first to get the exact text."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "old_string": {"type": "string", "description": "Exact string to find."},
                    "new_string": {"type": "string", "description": "Replacement string."},
                    "replace_all": {
                        "type": "boolean",
                        "description": "Replace every occurrence instead of failing on duplicates. Default false.",
                    },
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
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Show the current git branch and working tree status (staged, unstaged, untracked files).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Repository root. Defaults to working directory.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Show changes between the working tree and HEAD, or between commits. Output truncated at 8000 chars.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File or directory to scope the diff. Optional.",
                    },
                    "staged": {
                        "type": "boolean",
                        "description": "Diff staged changes (--cached). Default false.",
                    },
                    "commit": {
                        "type": "string",
                        "description": "Diff against this commit or ref. Optional.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_log",
            "description": "Show recent commit history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "description": "Number of commits to show. Default 10.",
                    },
                    "path": {
                        "type": "string",
                        "description": "Limit log to commits touching this path. Optional.",
                    },
                    "oneline": {
                        "type": "boolean",
                        "description": "Compact one-line format. Default true.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "Stage files (if specified) and create a git commit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Commit message.",
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Files to stage before committing. Optional — omit to commit already-staged changes.",
                    },
                    "all": {
                        "type": "boolean",
                        "description": "Stage all tracked modified files before committing (-u). Default false.",
                    },
                },
                "required": ["message"],
            },
        },
    },
]
