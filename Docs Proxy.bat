@echo off
rem Retrieval proxy between the in-Max MCP Chat and Ollama.
rem Point [llm] base_url in %LOCALAPPDATA%\3dsmax-mcp\mcp_config.ini at http://localhost:11435/v1
cd /d "%~dp0"
if not exist "%LOCALAPPDATA%\3dsmax-mcp\docs_index.json" (
    echo Building the reference index first...
    uv run python -m maxmcp.docsearch build
)
uv run python -m maxmcp.docsearch serve --port 11435 %*
if errorlevel 1 pause
