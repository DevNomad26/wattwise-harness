cat > CLAUDE.md << 'EOF'
# WattWise: electricity bill checker harness

A harness that makes small open models (Gemma 4, Qwen3.5 via Ollama) reliably
check electricity bill photos and write complaint letters. 2-day hackathon build,
3-person team. Only Member B (Akash) uses Claude Code; teammates write code by hand,
so never edit their folders unless asked.

## Rules
- Models run through Ollama only. Read model names from .env (MAIN_MODEL, VISION_MODEL); never hardcode them.
- Shared schemas live in wattwise/schemas.py. Do not change them without asking.
- The model never does arithmetic. All math goes through the calculator MCP server.
- Every tariff number comes from data/tariff.json, which cites the official tariff order.
- Tools are MCP servers in mcp_servers/ (FastMCP, stdio).
- Skills follow the Agent Skills format: skills/<name>/SKILL.md with name + description frontmatter.
- Write a pytest test for every new function. Run `pytest` before committing.
- Commit messages: `feat: ... (#issue)`, `fix:`, `test:`, `docs:`, `chore:`. Small commits.
- Never commit to main. One branch per issue, e.g. feat/4-calculator-mcp.
- Windows + Git Bash environment. Activate the venv with `source .venv/Scripts/activate`.

## Folder ownership
- A: wattwise/ (except verifier.py)
- B (Akash): mcp_servers/, data/, skills/
- C: wattwise/verifier.py, eval/, app.py, notebooks/, README.md
EOF