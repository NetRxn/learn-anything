# learn-anything

A Claude Code plugin marketplace containing **learn-anything** — a meta-learning system that helps people learn any skill efficiently through adaptive assessment, curriculum design, spaced repetition, and interactive training.

See [learn-anything-plugin/README.md](learn-anything-plugin/README.md) for full plugin documentation.

## Quick Start

### 1. Install the plugin

**From a private GitHub repo** (requires repo access):

```bash
# Use the full HTTPS URL for private repos (owner/repo shorthand only works for public repos)
claude plugin marketplace add https://github.com/NetRxn/learn-anything.git
```

Or from within a Claude Code session:
```
/plugin marketplace add https://github.com/NetRxn/learn-anything.git
```

**From a local clone** (for development or testing):

```bash
# Clone the repo
git clone https://github.com/NetRxn/learn-anything.git
cd learn-anything

# Add the local marketplace
claude plugin marketplace add /path/to/learn-anything
```

### 2. Enable the plugin

After adding the marketplace, enable the plugin when prompted. You can verify with:

```
/plugin
```

The `learn-anything` plugin should appear in your installed plugins list with 8 auto-discovered skills.

### 3. Install Python dependency (for Anki export)

The Material Forge skill exports flashcard decks to Anki. This requires `genanki`:

```bash
# Using uv (recommended)
uv pip install genanki

# Or using pip
pip install genanki
```

### 4. Start learning

```
/learn Spanish
/learn guitar
/learn negotiation
```

Or say it naturally — "I want to learn Spanish", "teach me guitar" — the orchestrator skill activates automatically.

Two commands handle everything:

| Command | Purpose |
|---|---|
| `/learn [topic or context]` | Start, resume, or manage any skill |
| `/train [context]` | Jump straight into a training session |

`/learn` delegates to the orchestrator — just describe what you want naturally (e.g., `/learn progress`, `/learn switch guitar`, `/learn I'm stuck on X`).

### 5. Add to your project's .gitignore

The plugin writes learner state to a `learn-anything/` directory in whatever project you're working in. Add this to your project's `.gitignore`:

```
learn-anything/
```

## Troubleshooting

### Private repo authentication errors

For private repos, Claude Code uses your existing git credentials. Verify access first:

```bash
# Check that you can reach the repo
git ls-remote https://github.com/NetRxn/learn-anything.git

# If that fails, authenticate with GitHub CLI
gh auth login
```

For **background auto-updates** to work (when Claude Code refreshes plugins without user interaction), set a token in your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

### Common errors

| Error | Fix |
|---|---|
| Authentication fails | Use full HTTPS URL, not `owner/repo` shorthand. Run `gh auth login` first. |
| Marketplace not found | Ensure `.claude-plugin/marketplace.json` exists at repo root and is pushed to remote. |
| Plugin not loading | Run `/plugin` and check if the marketplace is listed. Try `/plugin marketplace update`. |
| Git timeout on large repo | Set `export CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=300000` in your shell profile. |
| Skills not discovered | Verify the plugin has `.claude-plugin/plugin.json` and `skills/*/SKILL.md` structure. |

### Validate the plugin locally

```bash
cd learn-anything/learn-anything-plugin
claude plugin validate .
```

## Repository Structure

```
learn-anything/
├── .claude-plugin/
│   └── marketplace.json         ← Marketplace manifest (lists available plugins)
├── learn-anything-plugin/       ← The plugin
│   ├── .claude-plugin/
│   │   └── plugin.json          ← Plugin manifest
│   ├── commands/                ← /learn and /train commands
│   ├── skills/                  ← 8 auto-discovered skills
│   │   ├── orchestrator/
│   │   ├── domain-assessor/
│   │   ├── skill-researcher/
│   │   ├── learner-calibrator/
│   │   ├── curriculum-architect/
│   │   ├── material-forge/
│   │   ├── training-conductor/
│   │   └── dashboard-generator/
│   ├── schemas/                 ← 7 JSON schemas for state files
│   ├── requirements.txt
│   ├── .gitignore
│   └── README.md                ← Full plugin documentation
├── docs/                        ← Research and design documents
└── README.md                    ← This file
```
