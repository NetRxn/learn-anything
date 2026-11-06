# learn-anything

**Learn Anything** is a learning system with an existing Claude Code plugin and
a repository-native Codex skill gateway. Both use the canonical learning roles,
references and file-based state for assessment, curriculum, materials and practice.

See [learn-anything-plugin/README.md](learn-anything-plugin/README.md) for full plugin documentation.

A separate experimental [web application foundation](learn-anything-app/README.md)
implements local identity and durable documents only. It is not the browser learning
alpha, deployed service, or a plugin release. Contributor guidance: [AGENTS.md](AGENTS.md).

## Claude Code setup

### 1. Install the plugin

**From GitHub:**

```bash
# Add the marketplace by its HTTPS URL
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

### 3. Optional Python dependency for Anki export

The Material Forge's Anki exporter uses Python and `genanki`; see the plugin's
[export requirements](learn-anything-plugin/requirements.txt). Install these in
an isolated Python environment if you want deck export. They are not required
for the rest of the learning workflow. No dependency security assessment is
claimed here.

### 4. Start learning

```
/learn Spanish
/learn guitar
/learn negotiation
```

Or say it naturally — "I want to learn Spanish", "teach me guitar" — the orchestrator skill activates automatically.

Four Claude Code commands provide the learning entry points:

| Command | Purpose |
|---|---|
| `/learn [topic or context]` | Start, resume, or manage any skill |
| `/train [context or --mode mentor]` | Practice or have a mentor conversation |
| `/materials [type] [task-class]` | Generate missing or requested materials |
| `/update [changes or full refresh]` | Refresh an existing curriculum |

`/learn` delegates to the orchestrator — just describe what you want naturally (e.g., `/learn progress`, `/learn switch guitar`, `/learn I'm stuck on X`).

### 5. Add to your project's .gitignore

The plugin writes learner state to a `learn-anything/` directory in whatever project you're working in. Add this to your project's `.gitignore`:

```
learn-anything/
```

## Codex setup

Use an installed, signed-in Codex client with access to the cloned files.

1. Clone this repository and open its root as your Codex project:

   ```sh
   git clone https://github.com/NetRxn/learn-anything.git
   cd learn-anything
   ```

2. The gateway is in Codex's documented repository discovery location:
   [`.agents/skills/learn-anything/SKILL.md`](.agents/skills/learn-anything/SKILL.md).
   Keep the full repository together; the gateway reads the canonical plugin
   instructions and references. It does not install the Claude marketplace or
   need the experimental web app, PostgreSQL or a separate model API key.

3. In Codex CLI or the IDE extension, select it with `/skills` or type:

   ```text
   $learn-anything I want to learn Python for data analysis
   ```

   Then describe your goal, experience and available time. To return, ask to
   continue your learning program, practice, have a mentor conversation, generate
   materials or refresh the curriculum. Use the Skills picker where your client
   provides it. If discovery has not refreshed, restart Codex.

The `/learn`, `/train`, `/materials` and `/update` commands in the guide above are
**Claude Code commands**. The Codex gateway accepts equivalent requests in normal
language. Both use `learn-anything/<skill-slug>/` state in the same chosen project;
resume there and avoid simultaneous edits from two clients.

This adapter has structural, frontmatter and canonical-reference validation.
A complete Codex teaching journey and learning outcomes have **not** been validated.
Research/rendering/export capabilities depend on tools enabled in your Codex
session; missing capabilities must be reported rather than simulated. Python and
`genanki` remain optional for Anki export.

Discovery/invocation guidance follows the
[official Codex skills documentation](https://developers.openai.com/codex/skills/).

## Troubleshooting

### Authentication for a private fork

The public NetRxn repository does not require private-repository access. If you
use a private fork, verify its URL and your existing Git credentials:

```bash
# Check that you can reach the repo
git ls-remote <your-private-fork-url>

# If access requires authentication, use your normal GitHub setup
gh auth login
```

Use normal GitHub/Git credential management when access is required. Do not add
broad personal tokens to shell profiles as a plugin setup step.

### Common errors

| Error | Fix |
|---|---|
| Private-fork authentication fails | Verify the fork URL and Git access; authenticate for that fork if required. |
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
├── .agents/skills/learn-anything/ ← Codex gateway to canonical plugin instructions
├── learn-anything-app/          ← Experimental identity/document foundation
├── learn-anything-plugin/       ← The Claude Code plugin
│   ├── .claude-plugin/
│   │   └── plugin.json          ← Plugin manifest
│   ├── commands/                ← /learn, /train, /materials, /update
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
