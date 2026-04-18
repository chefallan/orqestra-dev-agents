const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawn, spawnSync } = require("child_process");
const {
  TEMPLATE_FILES,
  MINIMAL_TEMPLATE_FILES,
  REQUIRED_FILES,
  REQUIRED_MINIMAL_FILES,
} = require("./templates");

function printHelp() {
  console.log(`orqestra-dev-agents

Usage:
  orqestra-dev-agents hub
  orqestra-dev-agents agents [name] [--print|--path]
  orqestra-dev-agents workflows [name] [--print|--path]
  orqestra-dev-agents skills [name] [--print|--path]
  orqestra-dev-agents skills agents
  orqestra-dev-agents skills install [name] --agent <id> [--scope project|global] [--force]
  orqestra-dev-agents contracts [name] [--print|--path]
  orqestra-dev-agents tools [name] [args...]
  orqestra-dev-agents init [targetDir] [--force] [--minimal] [--with-runtime] [--with-contracts]
  orqestra-dev-agents doctor [targetDir] [--minimal] [--with-runtime] [--with-contracts]
  orqestra-dev-agents vscode-check [targetDir] [--ack]
  orqestra-dev-agents install-vscode [--check]
  orqestra-dev-agents runtime <start|stop|status|progress> [--port 64789] [--port-strict]
  orqestra-dev-agents onboarding [targetDir]
  orqestra-dev-agents --help
  orqestra-dev-agents --version
`);
}

const BUNDLED_ASSET_ROOT = path.join(__dirname, "..", "assets");
const VSCODE_REQUIRED_EXTENSIONS = [
  { id: "GitHub.copilot", name: "GitHub Copilot" },
  { id: "GitHub.copilot-chat", name: "GitHub Copilot Chat" },
];
const RUNTIME_REQUIRED_FILES = [
  "runtime/main.py",
  "scripts/run_runtime.ps1",
  "scripts/run_runtime.sh",
  "scripts/memory_cli.py",
  "agents/memory/memory-schema.sql",
  "requirements.txt",
];
const CONTRACT_REQUIRED_FILES = [
  "agents/contracts/handoff-contract.md",
  "templates/handoff-ticket.template.md",
];
const RUNTIME_PID_FILE = ".orqestra-runtime.pid";
const RUNTIME_META_FILE = ".orqestra-runtime.json";
const DEFAULT_RUNTIME_PORT = "64789";
const DEFAULT_RUNTIME_BASE_URL = `http://127.0.0.1:${DEFAULT_RUNTIME_PORT}`;
const DEFAULT_RUNTIME_TENANT = "local-dev";
const DEFAULT_RUNTIME_API_KEY = "local-dev-key";
const DEFAULT_PROGRESS_INTERVAL_SEC = 3;
const DEFAULT_PROGRESS_LIMIT = 5;
const CHATMODE_FILE = ".github/chatmodes/orqestra-orchestrator.chatmode.md";
const VSCODE_RELOAD_MARKER_FILE = ".orqestra-vscode-reload-required";
const MIN_PYTHON_MAJOR = 3;
const MIN_PYTHON_MINOR = 8;
const ORQESTRA_SKILL_NAME = "orqestra-workflow";
const ORQESTRA_SKILL_TEMPLATE_PATH = ".github/skills/orqestra-workflow/SKILL.md";

const SUPPORTED_SKILL_AGENTS = [
  { name: "Amp", ids: ["amp", "universal", "kimi-cli", "replit"], projectPath: ".agents/skills", globalPath: "~/.config/agents/skills" },
  { name: "Antigravity", ids: ["antigravity"], projectPath: ".agents/skills", globalPath: "~/.gemini/antigravity/skills" },
  { name: "Augment", ids: ["augment"], projectPath: ".augment/skills", globalPath: "~/.augment/skills" },
  { name: "IBM Bob", ids: ["bob"], projectPath: ".bob/skills", globalPath: "~/.bob/skills" },
  { name: "Claude Code", ids: ["claude-code"], projectPath: ".claude/skills", globalPath: "~/.claude/skills" },
  { name: "OpenClaw", ids: ["openclaw"], projectPath: "skills", globalPath: "~/.openclaw/skills" },
  { name: "Cline", ids: ["cline", "warp"], projectPath: ".agents/skills", globalPath: "~/.agents/skills" },
  { name: "CodeBuddy", ids: ["codebuddy"], projectPath: ".codebuddy/skills", globalPath: "~/.codebuddy/skills" },
  { name: "Codex", ids: ["codex"], projectPath: ".agents/skills", globalPath: "~/.codex/skills" },
  { name: "Command Code", ids: ["command-code"], projectPath: ".commandcode/skills", globalPath: "~/.commandcode/skills" },
  { name: "Continue", ids: ["continue"], projectPath: ".continue/skills", globalPath: "~/.continue/skills" },
  { name: "Cortex Code", ids: ["cortex"], projectPath: ".cortex/skills", globalPath: "~/.snowflake/cortex/skills" },
  { name: "Crush", ids: ["crush"], projectPath: ".crush/skills", globalPath: "~/.config/crush/skills" },
  { name: "Cursor", ids: ["cursor"], projectPath: ".agents/skills", globalPath: "~/.cursor/skills" },
  { name: "Deep Agents", ids: ["deepagents"], projectPath: ".agents/skills", globalPath: "~/.deepagents/agent/skills" },
  { name: "Droid", ids: ["droid"], projectPath: ".factory/skills", globalPath: "~/.factory/skills" },
  { name: "Firebender", ids: ["firebender"], projectPath: ".agents/skills", globalPath: "~/.firebender/skills" },
  { name: "Gemini CLI", ids: ["gemini-cli"], projectPath: ".agents/skills", globalPath: "~/.gemini/skills" },
  { name: "GitHub Copilot", ids: ["github-copilot"], projectPath: ".agents/skills", globalPath: "~/.copilot/skills" },
  { name: "Goose", ids: ["goose"], projectPath: ".goose/skills", globalPath: "~/.config/goose/skills" },
  { name: "Junie", ids: ["junie"], projectPath: ".junie/skills", globalPath: "~/.junie/skills" },
  { name: "iFlow CLI", ids: ["iflow-cli"], projectPath: ".iflow/skills", globalPath: "~/.iflow/skills" },
  { name: "Kilo Code", ids: ["kilo"], projectPath: ".kilocode/skills", globalPath: "~/.kilocode/skills" },
  { name: "Kiro CLI", ids: ["kiro-cli"], projectPath: ".kiro/skills", globalPath: "~/.kiro/skills" },
  { name: "Kode", ids: ["kode"], projectPath: ".kode/skills", globalPath: "~/.kode/skills" },
  { name: "MCPJam", ids: ["mcpjam"], projectPath: ".mcpjam/skills", globalPath: "~/.mcpjam/skills" },
  { name: "Mistral Vibe", ids: ["mistral-vibe"], projectPath: ".vibe/skills", globalPath: "~/.vibe/skills" },
  { name: "Mux", ids: ["mux"], projectPath: ".mux/skills", globalPath: "~/.mux/skills" },
  { name: "OpenCode", ids: ["opencode"], projectPath: ".agents/skills", globalPath: "~/.config/opencode/skills" },
  { name: "OpenHands", ids: ["openhands"], projectPath: ".openhands/skills", globalPath: "~/.openhands/skills" },
  { name: "Pi", ids: ["pi"], projectPath: ".pi/skills", globalPath: "~/.pi/agent/skills" },
  { name: "Qoder", ids: ["qoder"], projectPath: ".qoder/skills", globalPath: "~/.qoder/skills" },
  { name: "Qwen Code", ids: ["qwen-code"], projectPath: ".qwen/skills", globalPath: "~/.qwen/skills" },
  { name: "Roo Code", ids: ["roo"], projectPath: ".roo/skills", globalPath: "~/.roo/skills" },
  { name: "Trae", ids: ["trae"], projectPath: ".trae/skills", globalPath: "~/.trae/skills" },
  { name: "Trae CN", ids: ["trae-cn"], projectPath: ".trae/skills", globalPath: "~/.trae-cn/skills" },
  { name: "Windsurf", ids: ["windsurf"], projectPath: ".windsurf/skills", globalPath: "~/.codeium/windsurf/skills" },
  { name: "Zencoder", ids: ["zencoder"], projectPath: ".zencoder/skills", globalPath: "~/.zencoder/skills" },
  { name: "Neovate", ids: ["neovate"], projectPath: ".neovate/skills", globalPath: "~/.neovate/skills" },
  { name: "Pochi", ids: ["pochi"], projectPath: ".pochi/skills", globalPath: "~/.pochi/skills" },
  { name: "AdaL", ids: ["adal"], projectPath: ".adal/skills", globalPath: "~/.adal/skills" },
];

const SUPPORTED_SKILL_AGENT_ALIAS_MAP = new Map(
  SUPPORTED_SKILL_AGENTS.flatMap((agent) => agent.ids.map((id) => [id, agent]))
);

const TOOL_DEFINITIONS = [
  {
    name: "runtime",
    description: "Manage runtime start, stop, status, and progress watch.",
    usage: "orqestra-dev-agents tools runtime <start|stop|status|progress> [--port 64789] [--port-strict] [flags]",
    run(targetDir, args) {
      const action = args[0] || "status";
      const portIndex = args.indexOf("--port");
      const port = portIndex >= 0 ? args[portIndex + 1] : DEFAULT_RUNTIME_PORT;
      const strictPort = args.includes("--port-strict");

      if (action === "start") {
        runtimeStart(targetDir, port, strictPort);
        return;
      }
      if (action === "stop") {
        runtimeStop(targetDir);
        return;
      }
      if (action === "status") {
        runtimeStatus(targetDir);
        return;
      }
      if (action === "progress") {
        runtimeProgress(targetDir, args.slice(1));
        return;
      }

      console.error(`Unknown runtime action: ${action}`);
      console.error("Use one of: start, stop, status, progress");
      process.exitCode = 1;
    },
  },
  {
    name: "handoff",
    description: "Create a new handoff ticket from the contract template.",
    usage:
      "orqestra-dev-agents tools handoff --from orchestrator --to webapp-builder --epic compact-cli [--priority P1]",
    run(targetDir, args) {
      const absTarget = path.resolve(targetDir || process.cwd());
      const isWindows = process.platform === "win32";
      const command = isWindows ? "powershell" : "bash";
      const scriptPath = path.join(
        absTarget,
        "scripts",
        isWindows ? "new_handoff_ticket.ps1" : "new_handoff_ticket.sh"
      );

      if (!fs.existsSync(scriptPath)) {
        console.error("Handoff ticket script is missing. Run: orqestra-dev-agents init --with-runtime --with-contracts");
        process.exitCode = 1;
        return;
      }

      const commandArgs = isWindows
        ? ["-ExecutionPolicy", "Bypass", "-File", scriptPath, ...args]
        : [scriptPath, ...args];
      runInheritedCommand(command, commandArgs, absTarget);
    },
  },
  {
    name: "memory",
    description: "Run the persistent memory CLI for init, search, get, and upsert.",
    usage: "orqestra-dev-agents tools memory <init|search|get|upsert> [flags]",
    run(targetDir, args) {
      const absTarget = path.resolve(targetDir || process.cwd());
      const pythonCmd = detectPythonCommand(absTarget);
      if (!pythonCmd) {
        console.error(
          `Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ was not found in PATH. Install Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ and retry.`
        );
        process.exitCode = 1;
        return;
      }

      const scriptPath = path.join(absTarget, "scripts", "memory_cli.py");
      if (!fs.existsSync(scriptPath)) {
        console.error("Memory CLI is missing. Run: orqestra-dev-agents init --with-runtime");
        process.exitCode = 1;
        return;
      }

      runInheritedCommand(pythonCmd, [scriptPath, ...args], absTarget);
    },
  },
  {
    name: "validate-contracts",
    description: "Validate agent JSON schema blocks against runtime contracts.",
    usage: "orqestra-dev-agents tools validate-contracts [--repo-root .]",
    run(targetDir, args) {
      const absTarget = path.resolve(targetDir || process.cwd());
      const pythonCmd = detectPythonCommand(absTarget);
      if (!pythonCmd) {
        console.error(
          `Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ was not found in PATH. Install Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ and retry.`
        );
        process.exitCode = 1;
        return;
      }

      const scriptPath = path.join(absTarget, "scripts", "validate_prompt_contracts.py");
      if (!fs.existsSync(scriptPath)) {
        console.error("Prompt contract validator is missing. Run: orqestra-dev-agents init --with-runtime");
        process.exitCode = 1;
        return;
      }

      const commandArgs = [scriptPath, "--repo-root", absTarget, ...args];
      runInheritedCommand(pythonCmd, commandArgs, absTarget);
    },
  },
  {
    name: "doctor",
    description: "Run scaffold validation for the current repo.",
    usage: "orqestra-dev-agents tools doctor [--minimal] [--with-runtime] [--with-contracts]",
    run(targetDir, args) {
      doctor(targetDir, args.includes("--minimal"), args.includes("--with-runtime"), args.includes("--with-contracts"));
    },
  },
  {
    name: "onboarding",
    description: "Print the guided onboarding flow for the current repo.",
    usage: "orqestra-dev-agents tools onboarding",
    run(targetDir) {
      printOnboarding(targetDir);
    },
  },
  {
    name: "install-vscode",
    description: "Check or install required VS Code extensions.",
    usage: "orqestra-dev-agents tools install-vscode [--check]",
    run(_targetDir, args) {
      installVSCodeExtensions(args.includes("--check"));
    },
  },
  {
    name: "vscode-check",
    description: "Check whether the Orqestra chat mode needs a VS Code reload acknowledgement.",
    usage: "orqestra-dev-agents tools vscode-check [--ack]",
    run(targetDir, args) {
      vscodeCheck(targetDir, args.includes("--ack"));
    },
  },
];

const TOOL_MAP = new Map(TOOL_DEFINITIONS.map((tool) => [tool.name, tool]));

function runCommand(command, args, cwd, options = {}) {
  return spawnSync(command, args, {
    cwd,
    stdio: options.stdio || "pipe",
    encoding: "utf8",
    shell: false,
  });
}

function detectVSCodeCommand(cwd) {
  const candidates = ["code", "code-insiders"];
  for (const cmd of candidates) {
    const result = runCommand(cmd, ["--version"], cwd);
    if (result.status === 0) {
      return cmd;
    }
  }
  return null;
}

function runInheritedCommand(command, args, cwd) {
  const result = runCommand(command, args, cwd, { stdio: "inherit" });
  if (result.status !== 0) {
    process.exitCode = result.status || 1;
  }
}

function expandHomeDir(dirPath) {
  if (!dirPath.startsWith("~/")) {
    return dirPath;
  }
  return path.join(os.homedir(), dirPath.slice(2));
}

function getSupportedSkillDirPaths(targetDir) {
  const dirs = [];
  for (const agent of SUPPORTED_SKILL_AGENTS) {
    dirs.push(path.join(targetDir, agent.projectPath));
    dirs.push(expandHomeDir(agent.globalPath));
  }
  return dirs;
}

function resolveSupportedSkillAgent(agentId) {
  return SUPPORTED_SKILL_AGENT_ALIAS_MAP.get(String(agentId || "").trim().toLowerCase()) || null;
}

function renderSupportedSkillAgent(agent) {
  return `${agent.name} [${agent.ids.join(", ")}]\n  project: ${agent.projectPath}/\n  global: ${agent.globalPath}/`;
}

function printSupportedSkillAgents() {
  console.log(`Supported skill agents (${SUPPORTED_SKILL_AGENTS.length})`);
  console.log("");
  for (const agent of SUPPORTED_SKILL_AGENTS) {
    console.log(renderSupportedSkillAgent(agent));
  }
}

function resolveSkillInstallSource(targetDir, skillName) {
  const candidates = [
    path.join(targetDir, ".github", "skills", skillName, "SKILL.md"),
    path.join(targetDir, ".agents", "skills", skillName, "SKILL.md"),
    path.join(targetDir, "skills", skillName, "SKILL.md"),
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return fs.readFileSync(candidate, "utf8");
    }
  }

  if (skillName === ORQESTRA_SKILL_NAME && TEMPLATE_FILES[ORQESTRA_SKILL_TEMPLATE_PATH]) {
    return TEMPLATE_FILES[ORQESTRA_SKILL_TEMPLATE_PATH];
  }

  return "";
}

function installSkill(targetDir, args) {
  const absTarget = path.resolve(targetDir || process.cwd());
  const positionalArgs = getPositionalArgs(args, ["--agent", "--scope"]);
  const skillName = positionalArgs[0] || ORQESTRA_SKILL_NAME;
  const agentId = getArgValue(args, "--agent");
  const scope = (getArgValue(args, "--scope") || "project").toLowerCase();
  const force = args.includes("--force");

  if (!agentId) {
    console.error("Missing --agent value. Use: orqestra-dev-agents skills install orqestra-workflow --agent claude-code");
    process.exitCode = 1;
    return;
  }

  if (scope !== "project" && scope !== "global") {
    console.error("Invalid --scope value. Use 'project' or 'global'.");
    process.exitCode = 1;
    return;
  }

  const agent = resolveSupportedSkillAgent(agentId);
  if (!agent) {
    console.error(`Unsupported agent: ${agentId}`);
    console.error("Use 'orqestra-dev-agents skills agents' to list supported agent ids.");
    process.exitCode = 1;
    return;
  }

  const content = resolveSkillInstallSource(absTarget, skillName);
  if (!content) {
    console.error(`Unable to resolve skill content for '${skillName}'.`);
    console.error("Initialize the repo first or install the bundled Orqestra workflow skill.");
    process.exitCode = 1;
    return;
  }

  const baseDir = scope === "global" ? expandHomeDir(agent.globalPath) : path.join(absTarget, agent.projectPath);
  const destination = path.join(baseDir, skillName, "SKILL.md");

  if (fs.existsSync(destination) && !force) {
    console.error(`Skill already exists at ${destination}`);
    console.error("Use --force to overwrite it.");
    process.exitCode = 1;
    return;
  }

  ensureDir(destination);
  fs.writeFileSync(destination, content, "utf8");
  console.log(`Installed skill '${skillName}' for ${agent.name} (${scope})`);
  console.log(destination);
}

function normalizeLookupKey(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/\.agents\.md$/g, "")
    .replace(/\.md$/g, "")
    .replace(/[^a-z0-9]+/g, "");
}

function stripExtension(fileName) {
  return fileName.replace(/\.agents\.md$/i, "").replace(/\.md$/i, "");
}

function toDisplayPath(baseDir, fullPath) {
  return normalizeRelativePath(path.relative(baseDir, fullPath));
}

function collectFileEntries(baseDir, relativeDir, filterFn, mapFn) {
  const absoluteDir = path.join(baseDir, relativeDir);
  if (!fs.existsSync(absoluteDir)) {
    return [];
  }

  const entries = [];
  const stack = [absoluteDir];

  while (stack.length > 0) {
    const currentDir = stack.pop();
    const dirEntries = fs.readdirSync(currentDir, { withFileTypes: true });
    for (const entry of dirEntries) {
      const fullPath = path.join(currentDir, entry.name);
      if (entry.isDirectory()) {
        stack.push(fullPath);
        continue;
      }
      if (!filterFn(entry.name, fullPath)) {
        continue;
      }
      entries.push(mapFn(fullPath));
    }
  }

  return entries.sort((left, right) => left.name.localeCompare(right.name));
}

function resolveSkillDirs(targetDir) {
  const requested = String(process.env.ORQESTRA_SKILLS_DIRS || "")
    .split(path.delimiter)
    .map((value) => value.trim())
    .filter(Boolean);
  const defaults = [
    path.join(targetDir, "skills"),
    path.join(targetDir, ".agents", "skills"),
    path.join(targetDir, ".github", "skills"),
    ...getSupportedSkillDirPaths(targetDir),
  ];
  const seen = new Set();

  return [...requested, ...defaults]
    .map((dirPath) => path.resolve(dirPath))
    .filter((dirPath) => {
      if (seen.has(dirPath) || !fs.existsSync(dirPath)) {
        return false;
      }
      seen.add(dirPath);
      return fs.statSync(dirPath).isDirectory();
    });
}

function collectAgents(targetDir) {
  return collectFileEntries(
    targetDir,
    "agents",
    (name, fullPath) =>
      name.endsWith(".agents.md") && !fullPath.includes(`${path.sep}contracts${path.sep}`) && !fullPath.includes(`${path.sep}workflows${path.sep}`),
    (fullPath) => ({
      kind: "agents",
      name: stripExtension(path.basename(fullPath)),
      lookup: [stripExtension(path.basename(fullPath)), toDisplayPath(targetDir, fullPath)],
      path: fullPath,
      relativePath: toDisplayPath(targetDir, fullPath),
      source: "workspace",
    })
  );
}

function collectWorkflows(targetDir) {
  return collectFileEntries(
    targetDir,
    path.join("agents", "workflows"),
    (name) => name.endsWith(".md"),
    (fullPath) => ({
      kind: "workflows",
      name: stripExtension(path.basename(fullPath)),
      lookup: [stripExtension(path.basename(fullPath)), toDisplayPath(targetDir, fullPath)],
      path: fullPath,
      relativePath: toDisplayPath(targetDir, fullPath),
      source: "workspace",
    })
  );
}

function collectContracts(targetDir) {
  return collectFileEntries(
    targetDir,
    path.join("agents", "contracts"),
    (name) => name.endsWith(".md"),
    (fullPath) => ({
      kind: "contracts",
      name: stripExtension(toDisplayPath(path.join(targetDir, "agents", "contracts"), fullPath)),
      lookup: [
        stripExtension(path.basename(fullPath)),
        stripExtension(toDisplayPath(path.join(targetDir, "agents", "contracts"), fullPath)),
        toDisplayPath(targetDir, fullPath),
      ],
      path: fullPath,
      relativePath: toDisplayPath(targetDir, fullPath),
      source: "workspace",
    })
  );
}

function collectSkills(targetDir) {
  const skillDirs = resolveSkillDirs(targetDir);
  const results = [];

  for (const skillDir of skillDirs) {
    const directoryEntries = fs.readdirSync(skillDir, { withFileTypes: true });
    for (const entry of directoryEntries) {
      if (!entry.isDirectory()) {
        continue;
      }

      const skillPath = path.join(skillDir, entry.name, "SKILL.md");
      if (!fs.existsSync(skillPath)) {
        continue;
      }

      results.push({
        kind: "skills",
        name: entry.name,
        lookup: [entry.name, path.join(path.basename(skillDir), entry.name)],
        path: skillPath,
        relativePath: skillPath.startsWith(targetDir) ? toDisplayPath(targetDir, skillPath) : skillPath,
        source: skillPath.startsWith(targetDir) ? "workspace" : "external",
      });
    }
  }

  return results.sort((left, right) => left.name.localeCompare(right.name));
}

function handleSkillsCommand(rest, targetDir) {
  const action = rest.find((value) => !value.startsWith("--")) || "";

  if (action === "agents") {
    printSupportedSkillAgents();
    return;
  }

  if (action === "install") {
    const actionIndex = rest.indexOf("install");
    installSkill(targetDir, rest.slice(actionIndex + 1));
    return;
  }

  handleCatalogCommand("skills", rest, targetDir);
}

function collectTools() {
  return TOOL_DEFINITIONS.map((tool) => ({
    kind: "tools",
    name: tool.name,
    lookup: [tool.name],
    description: tool.description,
    usage: tool.usage,
  }));
}

function getCatalogEntries(kind, targetDir) {
  const absTarget = path.resolve(targetDir || process.cwd());

  if (kind === "agents") {
    return collectAgents(absTarget);
  }
  if (kind === "workflows") {
    return collectWorkflows(absTarget);
  }
  if (kind === "skills") {
    return collectSkills(absTarget);
  }
  if (kind === "contracts") {
    return collectContracts(absTarget);
  }
  if (kind === "tools") {
    return collectTools();
  }

  return [];
}

function printCatalog(kind, targetDir) {
  const entries = getCatalogEntries(kind, targetDir);
  const title = kind[0].toUpperCase() + kind.slice(1);

  console.log(`${title} (${entries.length})`);
  if (entries.length === 0) {
    console.log(`No ${kind} found.`);
    return;
  }

  for (const entry of entries) {
    if (kind === "tools") {
      console.log(`- ${entry.name}: ${entry.description}`);
      continue;
    }

    const suffix = entry.source === "external" ? ` [external]` : "";
    console.log(`- ${entry.name}: ${entry.relativePath}${suffix}`);
  }
}

function printHub(targetDir) {
  const absTarget = path.resolve(targetDir || process.cwd());
  console.log(`Orqestra Hub for ${absTarget}`);
  console.log("");
  printCatalog("agents", absTarget);
  console.log("");
  printCatalog("workflows", absTarget);
  console.log("");
  printCatalog("skills", absTarget);
  console.log("");
  printCatalog("contracts", absTarget);
  console.log("");
  printCatalog("tools", absTarget);
  console.log("");
  console.log("Quick actions:");
  console.log("- orqestra-dev-agents agents orchestrator");
  console.log("- orqestra-dev-agents workflows autonomous-webapp-loop");
  console.log("- orqestra-dev-agents skills georithm");
  console.log("- orqestra-dev-agents tools handoff --from orchestrator --to webapp-builder --epic compact-cli");
  console.log("- orqestra-dev-agents tools validate-contracts");
}

function findCatalogMatches(kind, targetDir, query) {
  const needle = normalizeLookupKey(query);
  return getCatalogEntries(kind, targetDir).filter((entry) =>
    entry.lookup.some((candidate) => normalizeLookupKey(candidate) === needle)
  );
}

function openFileInEditor(targetDir, fullPath) {
  const codeCmd = detectVSCodeCommand(targetDir);
  if (!codeCmd) {
    console.log(fullPath);
    return;
  }

  const result = runCommand(codeCmd, ["-g", fullPath], targetDir, { stdio: "inherit" });
  if (result.status !== 0) {
    process.exitCode = result.status || 1;
  }
}

function handleCatalogCommand(kind, rest, targetDir) {
  const printMode = rest.includes("--print") || rest.includes("--show");
  const pathMode = rest.includes("--path");
  const name = rest.find((value) => !value.startsWith("--") && value !== "list");
  const absTarget = path.resolve(targetDir || process.cwd());

  if (!name) {
    printCatalog(kind, absTarget);
    return;
  }

  const matches = findCatalogMatches(kind, absTarget, name);
  if (matches.length === 0) {
    console.error(`No ${kind} entry matched '${name}'.`);
    process.exitCode = 1;
    return;
  }

  if (matches.length > 1) {
    console.error(`Multiple ${kind} entries matched '${name}':`);
    for (const match of matches) {
      console.error(`- ${match.name}: ${match.relativePath}`);
    }
    process.exitCode = 1;
    return;
  }

  const entry = matches[0];
  if (pathMode) {
    console.log(entry.path);
    return;
  }
  if (printMode) {
    console.log(`# ${entry.name}`);
    console.log(`path: ${entry.path}`);
    console.log("");
    console.log(fs.readFileSync(entry.path, "utf8"));
    return;
  }

  openFileInEditor(absTarget, entry.path);
}

function handleToolsCommand(rest, targetDir) {
  const name = rest.find((value) => !value.startsWith("--") && value !== "list");

  if (!name) {
    printCatalog("tools", targetDir);
    return;
  }

  const tool = TOOL_MAP.get(name);
  if (!tool) {
    console.error(`Unknown tool: ${name}`);
    printCatalog("tools", targetDir);
    process.exitCode = 1;
    return;
  }

  const nameIndex = rest.indexOf(name);
  const toolArgs = rest.slice(nameIndex + 1);
  if (toolArgs.includes("--help") || toolArgs.includes("-h") || toolArgs.includes("--print") || toolArgs.includes("--show")) {
    console.log(`${tool.name}: ${tool.description}`);
    console.log(`usage: ${tool.usage}`);
    return;
  }

  tool.run(targetDir, toolArgs);
}

function installVSCodeExtensions(checkOnly) {
  const cwd = process.cwd();
  const codeCmd = detectVSCodeCommand(cwd);
  if (!codeCmd) {
    console.error("VS Code CLI was not found in PATH (code or code-insiders).");
    console.error("Open VS Code and run: Command Palette -> 'Shell Command: Install code command in PATH'.");
    process.exitCode = 1;
    return;
  }

  const list = runCommand(codeCmd, ["--list-extensions"], cwd);
  const installed = new Set(
    (list.stdout || "")
      .split(/\r?\n/)
      .map((line) => line.trim().toLowerCase())
      .filter(Boolean)
  );

  const missing = VSCODE_REQUIRED_EXTENSIONS.filter(
    (ext) => !installed.has(ext.id.toLowerCase())
  );

  if (checkOnly) {
    if (missing.length === 0) {
      console.log("VS Code extensions check passed.");
      for (const ext of VSCODE_REQUIRED_EXTENSIONS) {
        console.log(`- installed: ${ext.id}`);
      }
      return;
    }

    console.log("VS Code extensions check found missing items:");
    for (const ext of missing) {
      console.log(`- missing: ${ext.id} (${ext.name})`);
    }
    console.log("Run: orqestra-dev-agents install-vscode");
    process.exitCode = 1;
    return;
  }

  if (missing.length === 0) {
    console.log("All required VS Code extensions are already installed.");
    for (const ext of VSCODE_REQUIRED_EXTENSIONS) {
      console.log(`- installed: ${ext.id}`);
    }
    return;
  }

  console.log(`Using VS Code CLI command: ${codeCmd}`);
  for (const ext of missing) {
    console.log(`Installing: ${ext.id} (${ext.name})`);
    const install = runCommand(codeCmd, ["--install-extension", ext.id], cwd, { stdio: "inherit" });
    if (install.status !== 0) {
      console.error(`Failed to install extension: ${ext.id}`);
      process.exitCode = 1;
      return;
    }
  }

  console.log("VS Code extension installation completed.");
}

function detectPythonCommand(cwd) {
  const candidates = ["python3", "python"];
  for (const cmd of candidates) {
    const version = getPythonMajorMinorVersion(cwd, cmd);
    if (version && isSupportedPythonVersion(version)) {
      return cmd;
    }
  }
  return null;
}

function getPythonMajorMinorVersion(cwd, cmd) {
  const result = runCommand(
    cmd,
    ["-c", "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"],
    cwd
  );
  if (result.status !== 0) {
    return null;
  }

  const raw = String(result.stdout || "").trim();
  const match = raw.match(/^(\d+)\.(\d+)$/);
  if (!match) {
    return null;
  }

  return {
    major: Number.parseInt(match[1], 10),
    minor: Number.parseInt(match[2], 10),
  };
}

function isSupportedPythonVersion(version) {
  if (!version) {
    return false;
  }
  return (
    version.major > MIN_PYTHON_MAJOR ||
    (version.major === MIN_PYTHON_MAJOR && version.minor >= MIN_PYTHON_MINOR)
  );
}

function isProcessAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (_err) {
    return false;
  }
}

function getRuntimePidFile(targetDir) {
  return path.join(targetDir, RUNTIME_PID_FILE);
}

function getRuntimeMetaFile(targetDir) {
  return path.join(targetDir, RUNTIME_META_FILE);
}

function readRuntimeMeta(targetDir) {
  const metaFile = getRuntimeMetaFile(targetDir);
  if (!fs.existsSync(metaFile)) {
    return null;
  }
  try {
    const raw = fs.readFileSync(metaFile, "utf8");
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return null;
    }
    return parsed;
  } catch (_err) {
    return null;
  }
}

function writeRuntimeMeta(targetDir, payload) {
  const metaFile = getRuntimeMetaFile(targetDir);
  fs.writeFileSync(metaFile, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function clearRuntimeMeta(targetDir) {
  const metaFile = getRuntimeMetaFile(targetDir);
  if (fs.existsSync(metaFile)) {
    fs.unlinkSync(metaFile);
  }
}

function readRuntimePid(targetDir) {
  const pidFile = getRuntimePidFile(targetDir);
  if (!fs.existsSync(pidFile)) {
    return null;
  }
  const raw = fs.readFileSync(pidFile, "utf8").trim();
  const pid = Number.parseInt(raw, 10);
  if (!Number.isInteger(pid) || pid <= 0) {
    return null;
  }
  return pid;
}

function requireRuntimeFiles(targetDir) {
  const required = ["runtime/main.py", "scripts/memory_cli.py", "requirements.txt"];
  const missing = required.filter((relPath) => !fs.existsSync(path.join(targetDir, relPath)));
  if (missing.length > 0) {
    console.error("Runtime files are missing. Run: orqestra-dev-agents init --with-runtime");
    for (const file of missing) {
      console.error(`- ${file}`);
    }
    process.exitCode = 1;
    return false;
  }
  return true;
}

function ensurePythonRequirements(targetDir) {
  const pythonCmd = detectPythonCommand(targetDir);
  if (!pythonCmd) {
    console.error(
      `Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ was not found in PATH. Install Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ and retry.`
    );
    process.exitCode = 1;
    return null;
  }

  const importCheck = runCommand(
    pythonCmd,
    ["-c", "import fastapi, uvicorn, pydantic"],
    targetDir
  );

  if (importCheck.status !== 0) {
    console.log("Python runtime dependencies are missing. Installing from requirements.txt...");
    const install = runCommand(pythonCmd, ["-m", "pip", "install", "-r", "requirements.txt"], targetDir, {
      stdio: "inherit",
    });
    if (install.status !== 0) {
      console.error("Failed to install Python dependencies.");
      process.exitCode = 1;
      return null;
    }
  }

  return pythonCmd;
}

function resolveRuntimeStartPort(targetDir, pythonCmd, requestedPort) {
  const snippet = [
    "import socket, sys",
    "start = int(sys.argv[1])",
    "for candidate in range(start, 65536):",
    "    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)",
    "    try:",
    "        sock.bind(('127.0.0.1', candidate))",
    "        print(candidate)",
    "        sys.exit(0)",
    "    except OSError:",
    "        pass",
    "    finally:",
    "        sock.close()",
    "sys.exit(1)",
  ].join("\n");

  const result = runCommand(pythonCmd, ["-c", snippet, String(requestedPort)], targetDir);
  if (result.status !== 0) {
    return 0;
  }

  const selected = Number.parseInt(String(result.stdout || "").trim(), 10);
  if (!Number.isInteger(selected) || selected <= 0 || selected > 65535) {
    return 0;
  }
  return selected;
}

function runtimeStatus(targetDir) {
  const absTarget = path.resolve(targetDir || process.cwd());
  const pid = readRuntimePid(absTarget);
  if (!pid) {
    console.log("Runtime status: stopped");
    return;
  }
  if (!isProcessAlive(pid)) {
    clearRuntimeMeta(absTarget);
    console.log("Runtime status: stopped (stale PID file found)");
    return;
  }
  const meta = readRuntimeMeta(absTarget);
  const port = Number.parseInt(String(meta && meta.port ? meta.port : ""), 10);
  if (Number.isInteger(port) && port > 0) {
    console.log(`Runtime status: running (pid ${pid}) on http://127.0.0.1:${port}`);
    return;
  }
  console.log(`Runtime status: running (pid ${pid})`);
}

function runtimeStart(targetDir, portArg, strictPort = false) {
  const absTarget = path.resolve(targetDir || process.cwd());
  if (!requireRuntimeFiles(absTarget)) {
    return;
  }

  const currentPid = readRuntimePid(absTarget);
  if (currentPid && isProcessAlive(currentPid)) {
    const meta = readRuntimeMeta(absTarget);
    const currentPort = Number.parseInt(String(meta && meta.port ? meta.port : ""), 10);
    if (Number.isInteger(currentPort) && currentPort > 0) {
      console.log(`Runtime is already running (pid ${currentPid}) on http://127.0.0.1:${currentPort}`);
      return;
    }
    console.log(`Runtime is already running (pid ${currentPid})`);
    return;
  }

  if (currentPid && !isProcessAlive(currentPid)) {
    const pidFile = getRuntimePidFile(absTarget);
    if (fs.existsSync(pidFile)) {
      fs.unlinkSync(pidFile);
    }
    clearRuntimeMeta(absTarget);
  }

  const pythonCmd = ensurePythonRequirements(absTarget);
  if (!pythonCmd) {
    return;
  }

  const initMemory = runCommand(pythonCmd, ["scripts/memory_cli.py", "init"], absTarget, {
    stdio: "inherit",
  });
  if (initMemory.status !== 0) {
    console.error("Failed to initialize runtime memory DB.");
    process.exitCode = 1;
    return;
  }

  const requestedPort = Number.parseInt(portArg || DEFAULT_RUNTIME_PORT, 10);
  if (!Number.isInteger(requestedPort) || requestedPort <= 0 || requestedPort > 65535) {
    console.error("Invalid --port value. Use an integer port in range 1..65535.");
    process.exitCode = 1;
    return;
  }

  const port = resolveRuntimeStartPort(absTarget, pythonCmd, requestedPort);
  if (!port) {
    console.error("No free port was found in range 1..65535.");
    process.exitCode = 1;
    return;
  }

  if (strictPort && port !== requestedPort) {
    console.error(`Requested port ${requestedPort} is in use and --port-strict is set.`);
    process.exitCode = 1;
    return;
  }

  if (port !== requestedPort) {
    console.log(`Requested port ${requestedPort} is in use. Using available port ${port} instead.`);
  }

  const child = spawn(
    pythonCmd,
    ["-m", "uvicorn", "runtime.main:app", "--host", "127.0.0.1", "--port", String(port)],
    {
      cwd: absTarget,
      detached: true,
      stdio: "ignore",
      shell: false,
    }
  );
  child.unref();

  fs.writeFileSync(getRuntimePidFile(absTarget), String(child.pid), "utf8");
  writeRuntimeMeta(absTarget, {
    pid: child.pid,
    port,
    startedAt: new Date().toISOString(),
  });
  console.log(`Runtime started in background (pid ${child.pid}) on http://127.0.0.1:${port}`);
}

function runtimeStop(targetDir) {
  const absTarget = path.resolve(targetDir || process.cwd());
  const pidFile = getRuntimePidFile(absTarget);
  const pid = readRuntimePid(absTarget);

  if (!pid) {
    clearRuntimeMeta(absTarget);
    console.log("Runtime is not running.");
    return;
  }

  if (!isProcessAlive(pid)) {
    if (fs.existsSync(pidFile)) {
      fs.unlinkSync(pidFile);
    }
    clearRuntimeMeta(absTarget);
    console.log("Runtime is already stopped. Removed stale PID file.");
    return;
  }

  try {
    process.kill(pid);
    if (fs.existsSync(pidFile)) {
      fs.unlinkSync(pidFile);
    }
    clearRuntimeMeta(absTarget);
    console.log(`Runtime stopped (pid ${pid}).`);
  } catch (err) {
    console.error(`Failed to stop runtime process ${pid}: ${err.message}`);
    process.exitCode = 1;
  }
}

function getArgValue(args, flag) {
  const index = args.indexOf(flag);
  if (index < 0) {
    return "";
  }
  return args[index + 1] || "";
}

function getPositionalArgs(args, flagsWithValues = []) {
  const valueFlags = new Set(flagsWithValues);
  const positional = [];

  for (let index = 0; index < args.length; index += 1) {
    const value = args[index];
    if (valueFlags.has(value)) {
      index += 1;
      continue;
    }
    if (value.startsWith("--")) {
      continue;
    }
    positional.push(value);
  }

  return positional;
}

function parseRuntimeApiKeys(raw) {
  const mapping = {};
  const value = String(raw || "").trim();
  if (!value) {
    return mapping;
  }

  for (const pair of value.split(",")) {
    const item = pair.trim();
    if (!item || !item.includes(":")) {
      continue;
    }
    const [tenant, key] = item.split(":", 2).map((part) => part.trim());
    if (tenant && key) {
      mapping[tenant] = key;
    }
  }

  return mapping;
}

function resolveRuntimeAuth(args) {
  const envMap = parseRuntimeApiKeys(process.env.AGENT_RUNTIME_API_KEYS);
  const tenantFromArgs = getArgValue(args, "--tenant");
  const tenantFromEnv = String(process.env.AGENT_RUNTIME_TENANT || "").trim();
  const tenant = tenantFromArgs || tenantFromEnv || DEFAULT_RUNTIME_TENANT;

  const apiKeyFromArgs = getArgValue(args, "--api-key");
  const apiKeyFromEnv = String(process.env.AGENT_RUNTIME_API_KEY || "").trim();
  const apiKey = apiKeyFromArgs || apiKeyFromEnv || envMap[tenant] || DEFAULT_RUNTIME_API_KEY;

  return { tenant, apiKey };
}

function normalizeRuntimeBaseUrl(args, targetDir) {
  const urlArg = getArgValue(args, "--url");
  const portArg = getArgValue(args, "--port");

  if (urlArg) {
    return urlArg.replace(/\/$/, "");
  }

  if (!portArg) {
    const meta = readRuntimeMeta(targetDir);
    const metaPort = Number.parseInt(String(meta && meta.port ? meta.port : ""), 10);
    if (Number.isInteger(metaPort) && metaPort > 0) {
      return `http://127.0.0.1:${metaPort}`;
    }
  }

  const port = portArg || DEFAULT_RUNTIME_PORT;
  return `http://127.0.0.1:${port}`;
}

async function fetchJson(url, options = {}) {
  if (typeof fetch !== "function") {
    throw new Error("Fetch API is unavailable. Use Node.js 18+.");
  }

  const response = await fetch(url, options);
  const text = await response.text();
  let data = {};

  if (text.trim()) {
    try {
      data = JSON.parse(text);
    } catch (_err) {
      data = { raw: text };
    }
  }

  if (!response.ok) {
    const message = data && typeof data === "object" ? data.detail || data.raw || text : text;
    throw new Error(`HTTP ${response.status} ${response.statusText}${message ? `: ${message}` : ""}`);
  }

  return data;
}

function summarizeTaskStates(tasks) {
  const counts = { queued: 0, running: 0, completed: 0, failed: 0 };
  for (const task of tasks) {
    const status = String(task.status || "");
    if (Object.prototype.hasOwnProperty.call(counts, status)) {
      counts[status] += 1;
    }
  }
  return counts;
}

function sortRunsNewestFirst(runs) {
  return [...runs].sort((a, b) => String(b.updated_at || "").localeCompare(String(a.updated_at || "")));
}

function formatIso(iso) {
  if (!iso) {
    return "n/a";
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return String(iso);
  }
  return date.toLocaleString();
}

function renderRuntimeProgressSnapshot(payload) {
  const { baseUrl, tenant, runs, taskMap, health, generatedAt, limit } = payload;
  console.log(`Runtime progress @ ${generatedAt}`);
  console.log(`Runtime: ${baseUrl}`);
  console.log(`Tenant: ${tenant}`);
  console.log(`Health: ${health.status || "unknown"}`);
  console.log("");

  if (!runs.length) {
    console.log("No runs found yet.");
    console.log("Plain Copilot chat messages are not automatically tracked as runtime runs.");
    console.log(`Create a tracked run by calling POST ${baseUrl}/runs with runtime tenant headers.`);
    return;
  }

  console.log(`Showing latest ${Math.min(limit, runs.length)} run(s):`);
  console.log("");

  for (const run of runs.slice(0, limit)) {
    const tasks = taskMap.get(run.run_id) || [];
    const counts = summarizeTaskStates(tasks);
    console.log(`- run_id: ${run.run_id}`);
    console.log(`  objective: ${run.objective || "(no objective)"}`);
    console.log(`  status: ${run.status}`);
    console.log(
      `  tasks: queued=${counts.queued} running=${counts.running} completed=${counts.completed} failed=${counts.failed}`
    );
    console.log(`  last_update: ${formatIso(run.updated_at)}`);

    const running = tasks.filter((task) => task.status === "running");
    if (running.length > 0) {
      const preview = running.slice(0, 2).map((task) => `${task.role}:${task.task_type}`).join(", ");
      console.log(`  active: ${preview}`);
    }

    const failed = tasks.find((task) => task.status === "failed");
    if (failed) {
      console.log(`  last_error: ${failed.error || "unknown error"}`);
    }
    console.log("");
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function runtimeProgress(targetDir, args) {
  const absTarget = path.resolve(targetDir || process.cwd());
  if (!requireRuntimeFiles(absTarget)) {
    return;
  }

  const watch = args.includes("--watch");
  const intervalRaw = getArgValue(args, "--interval") || String(DEFAULT_PROGRESS_INTERVAL_SEC);
  const limitRaw = getArgValue(args, "--limit") || String(DEFAULT_PROGRESS_LIMIT);
  const intervalSec = Number.parseInt(intervalRaw, 10);
  const limit = Number.parseInt(limitRaw, 10);

  if (!Number.isInteger(intervalSec) || intervalSec <= 0) {
    console.error("Invalid --interval value. Use an integer greater than 0.");
    process.exitCode = 1;
    return;
  }

  if (!Number.isInteger(limit) || limit <= 0 || limit > 50) {
    console.error("Invalid --limit value. Use an integer in range 1..50.");
    process.exitCode = 1;
    return;
  }

  const baseUrl = normalizeRuntimeBaseUrl(args, absTarget) || DEFAULT_RUNTIME_BASE_URL;
  const { tenant, apiKey } = resolveRuntimeAuth(args);
  const headers = {
    "X-Tenant-Id": tenant,
    "X-Api-Key": apiKey,
  };

  if (watch) {
    console.log("Runtime progress watch started. Press Ctrl+C to stop.");
    console.log("");
  }

  while (true) {
    try {
      const health = await fetchJson(`${baseUrl}/health`);
      const runsRaw = await fetchJson(`${baseUrl}/runs`, { headers });
      const runs = Array.isArray(runsRaw) ? sortRunsNewestFirst(runsRaw) : [];
      const taskMap = new Map();

      for (const run of runs.slice(0, limit)) {
        const tasksRaw = await fetchJson(`${baseUrl}/runs/${run.run_id}/tasks`, { headers });
        taskMap.set(run.run_id, Array.isArray(tasksRaw) ? tasksRaw : []);
      }

      if (watch && process.stdout.isTTY) {
        process.stdout.write("\x1Bc");
      }

      renderRuntimeProgressSnapshot({
        baseUrl,
        tenant,
        health,
        runs,
        taskMap,
        generatedAt: new Date().toLocaleString(),
        limit,
      });
    } catch (err) {
      console.error(`Runtime progress failed: ${err.message}`);
      console.error("Tip: ensure runtime is running and auth values match AGENT_RUNTIME_API_KEYS.");
      process.exitCode = 1;
      if (!watch) {
        return;
      }
    }

    if (!watch) {
      return;
    }

    await delay(intervalSec * 1000);
  }
}

function hasAnyGeneratedFiles(targetDir) {
  const absTarget = path.resolve(targetDir || process.cwd());
  return REQUIRED_MINIMAL_FILES.some((relativePath) => fs.existsSync(path.join(absTarget, relativePath)));
}

function printNotInitializedHint(targetDir) {
  const absTarget = path.resolve(targetDir || process.cwd());
  const initialized = hasAnyGeneratedFiles(absTarget);
  console.log(`Installed CLI detected in ${absTarget}`);
  if (!initialized) {
    console.log("No Orqestra agent files were detected in this directory.");
  }
  console.log("To scaffold files here, run: orqestra-dev-agents init");
  console.log("To verify expected files, run: orqestra-dev-agents doctor");
}

function printOnboarding(targetDir) {
  const absTarget = path.resolve(targetDir || process.cwd());
  const hasPrompts = fs.existsSync(path.join(absTarget, "agents", "orchestrator.agents.md"));
  const hasRuntime = fs.existsSync(path.join(absTarget, "runtime", "main.py"));
  const hasContracts = fs.existsSync(path.join(absTarget, "agents", "contracts", "handoff-contract.md"));

  console.log(`Onboarding guide for ${absTarget}`);
  console.log("");
  console.log("1) Install in this repo (if not installed yet):");
  console.log("   npm install -D orqestra-dev-agents@latest");
  console.log("");

  if (hasPrompts && hasRuntime && hasContracts) {
    console.log("2) Scaffold status: detected agent specs + runtime + contracts.");
    console.log("   Validation command: orqestra-dev-agents doctor --with-runtime --with-contracts");
  } else if (hasPrompts) {
    console.log("2) Scaffold status: core agent specs detected, runtime/contracts may be missing.");
    console.log("   Recommended: orqestra-dev-agents init --with-runtime --with-contracts --force");
  } else {
    console.log("2) Initialize production scaffold:");
    console.log("   orqestra-dev-agents init --with-runtime --with-contracts");
  }

  console.log("");
  console.log("3) Validate scaffold:");
  console.log("   orqestra-dev-agents doctor --with-runtime --with-contracts");
  console.log("");
  console.log("4) Install VS Code dependencies:");
  console.log("   orqestra-dev-agents install-vscode");
  console.log("");
  console.log("5) Start runtime for autonomous execution:");
  console.log("   npm run runtime -- start");
  console.log("");
  console.log("6) Open your preferred coding assistant:");
  console.log("   - Open Copilot Chat in Agent mode");
  console.log("   - Select chat mode: Orqestra Orchestrator");
  console.log("   - If the mode is not listed yet, run: Developer: Reload Window");
  console.log("   - Fallback: use agents/orchestrator.agents.md as the orchestrator agent spec");
  console.log("   - For Claude, Codex, OpenCode, and similar assistants: start from AGENTS.md or .github/skills/orqestra-workflow/SKILL.md");
  console.log("");
  console.log("7) Single prompt for automation building:");
  console.log(
    '   Build and automate a production-ready MVP with signup/login, project creation, tests, docs updates, and memory snapshots. Execute in thin vertical slices until a releasable first version is ready, and report progress after each slice.'
  );
  console.log("");
  console.log("Optional VS Code check after init/re-init:");
  console.log("- orqestra-dev-agents vscode-check");
  console.log("- after reloading VS Code, confirm and clear reminder: orqestra-dev-agents vscode-check --ack");
  console.log("");
  console.log("Optional runtime start:");
  console.log("- Windows PowerShell: powershell -ExecutionPolicy Bypass -File scripts/run_runtime.ps1");
  console.log("- Ubuntu/macOS: bash scripts/run_runtime.sh");
}

function getVSCodeReloadMarkerFile(targetDir) {
  return path.join(targetDir, VSCODE_RELOAD_MARKER_FILE);
}

function setVSCodeReloadMarker(targetDir) {
  const markerPath = getVSCodeReloadMarkerFile(targetDir);
  const payload = {
    generatedAt: new Date().toISOString(),
    reason: "chatmode-updated",
    chatmodePath: CHATMODE_FILE,
  };
  fs.writeFileSync(markerPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function clearVSCodeReloadMarker(targetDir) {
  const markerPath = getVSCodeReloadMarkerFile(targetDir);
  if (fs.existsSync(markerPath)) {
    fs.unlinkSync(markerPath);
    return true;
  }
  return false;
}

function vscodeCheck(targetDir, acknowledge) {
  const absTarget = path.resolve(targetDir || process.cwd());
  const chatmodePath = path.join(absTarget, CHATMODE_FILE);
  const markerPath = getVSCodeReloadMarkerFile(absTarget);

  if (!fs.existsSync(chatmodePath)) {
    console.error("Chat mode file is missing.");
    console.error("Run: orqestra-dev-agents init --with-runtime --with-contracts");
    console.error(`Expected file: ${CHATMODE_FILE}`);
    process.exitCode = 1;
    return;
  }

  if (acknowledge) {
    const removed = clearVSCodeReloadMarker(absTarget);
    if (removed) {
      console.log("VS Code reload reminder cleared.");
      console.log("Orqestra Orchestrator mode should now be available in Copilot Chat mode selector.");
      return;
    }
    console.log("No pending VS Code reload reminder was found.");
    return;
  }

  if (fs.existsSync(markerPath)) {
    console.log("VS Code chat mode update detected.");
    console.log("Action needed: run 'Developer: Reload Window' in VS Code.");
    console.log("After reloading, run: orqestra-dev-agents vscode-check --ack");
    process.exitCode = 1;
    return;
  }

  console.log("VS Code chat mode check passed.");
  console.log("Orqestra Orchestrator chat mode file is present with no pending reload reminder.");
}

function ensureDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function normalizeRelativePath(relativePath) {
  return relativePath.split(path.sep).join("/");
}

function collectFilesRecursively(baseDir, currentDir, outMap) {
  const entries = fs.readdirSync(currentDir, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.name === "__pycache__") {
      continue;
    }

    const fullPath = path.join(currentDir, entry.name);
    if (entry.isDirectory()) {
      collectFilesRecursively(baseDir, fullPath, outMap);
      continue;
    }

    const relPath = normalizeRelativePath(path.relative(baseDir, fullPath));
    outMap.set(relPath, fs.readFileSync(fullPath, "utf8"));
  }
}

function loadBundledAssets(withRuntime, withContracts) {
  const files = new Map();

  function addPath(relativeAssetPath) {
    const assetPath = path.join(BUNDLED_ASSET_ROOT, ...relativeAssetPath.split("/"));
    if (!fs.existsSync(assetPath)) {
      return;
    }
    const stat = fs.statSync(assetPath);
    if (stat.isDirectory()) {
      collectFilesRecursively(BUNDLED_ASSET_ROOT, assetPath, files);
      return;
    }
    files.set(normalizeRelativePath(relativeAssetPath), fs.readFileSync(assetPath, "utf8"));
  }

  if (withRuntime) {
    addPath("runtime");
    addPath("scripts");
    addPath("templates");
    addPath("agents/memory/memory-schema.sql");
    addPath("requirements.txt");
  }

  if (withContracts) {
    addPath("agents/contracts");
    addPath("templates/handoff-ticket.template.md");
  }

  return files;
}

function slugifyPackageName(text) {
  const normalized = String(text || "")
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return normalized || "orqestra-workspace";
}

function ensurePackageJson(targetDir) {
  const pkgPath = path.join(targetDir, "package.json");
  if (fs.existsSync(pkgPath)) {
    return { created: false, path: pkgPath };
  }

  const baseName = path.basename(path.resolve(targetDir));
  const pkg = {
    name: slugifyPackageName(baseName),
    version: "1.0.0",
    private: true,
    scripts: {},
  };

  fs.writeFileSync(pkgPath, `${JSON.stringify(pkg, null, 2)}\n`, "utf8");
  return { created: true, path: pkgPath };
}

function ensureNpmRuntimeScripts(targetDir) {
  const pkgPath = path.join(targetDir, "package.json");
  if (!fs.existsSync(pkgPath)) {
    return {
      updated: false,
      reason: "missing-package-json",
      added: [],
      kept: [],
    };
  }

  let pkg;
  try {
    pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
  } catch (_err) {
    return {
      updated: false,
      reason: "invalid-package-json",
      added: [],
      kept: [],
    };
  }

  if (!pkg.scripts || typeof pkg.scripts !== "object") {
    pkg.scripts = {};
  }

  const desiredScripts = {
    runtime: "npx orqestra-dev-agents runtime",
    "orqestra:hub": "npx orqestra-dev-agents hub",
    "orqestra:agents": "npx orqestra-dev-agents agents",
    "orqestra:workflows": "npx orqestra-dev-agents workflows",
    "orqestra:skills": "npx orqestra-dev-agents skills",
    "orqestra:tools": "npx orqestra-dev-agents tools",
    "orqestra:start": "npx orqestra-dev-agents runtime start; npx orqestra-dev-agents runtime progress --watch",
    "orqestra:status": "npx orqestra-dev-agents runtime status",
    "orqestra:stop": "npx orqestra-dev-agents runtime stop",
    "orqestra:progress": "npx orqestra-dev-agents runtime progress --watch",
    "orqestra:doctor": "npx orqestra-dev-agents doctor --with-runtime --with-contracts",
  };

  const added = [];
  const kept = [];

  for (const [key, value] of Object.entries(desiredScripts)) {
    if (typeof pkg.scripts[key] === "string" && pkg.scripts[key].trim().length > 0) {
      kept.push(key);
      continue;
    }
    pkg.scripts[key] = value;
    added.push(key);
  }

  if (added.length > 0) {
    fs.writeFileSync(pkgPath, `${JSON.stringify(pkg, null, 2)}\n`, "utf8");
    return {
      updated: true,
      reason: "ok",
      added,
      kept,
    };
  }

  return {
    updated: false,
    reason: "already-present",
    added,
    kept,
  };
}

function syncPackageVersionInTarget(targetDir) {
  const pkgPath = path.join(targetDir, "package.json");
  if (!fs.existsSync(pkgPath)) {
    return {
      updated: false,
      reason: "missing-package-json",
      previous: "",
      next: "",
      section: "",
    };
  }

  let targetPkg;
  try {
    targetPkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
  } catch (_err) {
    return {
      updated: false,
      reason: "invalid-package-json",
      previous: "",
      next: "",
      section: "",
    };
  }

  let cliPkg;
  try {
    const cliPkgPath = path.join(__dirname, "..", "package.json");
    cliPkg = JSON.parse(fs.readFileSync(cliPkgPath, "utf8"));
  } catch (_err) {
    return {
      updated: false,
      reason: "missing-cli-package-json",
      previous: "",
      next: "",
      section: "",
    };
  }

  const packageName = "orqestra-dev-agents";
  const currentVersion = String(cliPkg.version || "").trim();
  if (!currentVersion) {
    return {
      updated: false,
      reason: "missing-cli-version",
      previous: "",
      next: "",
      section: "",
    };
  }

  let section = "devDependencies";
  let previous = "";

  if (targetPkg.dependencies && typeof targetPkg.dependencies === "object" && targetPkg.dependencies[packageName]) {
    section = "dependencies";
    previous = String(targetPkg.dependencies[packageName]);
  } else {
    if (!targetPkg.devDependencies || typeof targetPkg.devDependencies !== "object") {
      targetPkg.devDependencies = {};
    }
    previous = String(targetPkg.devDependencies[packageName] || "");
  }

  if (previous === currentVersion) {
    return {
      updated: false,
      reason: "already-synced",
      previous,
      next: currentVersion,
      section,
    };
  }

  if (section === "dependencies") {
    targetPkg.dependencies[packageName] = currentVersion;
  } else {
    targetPkg.devDependencies[packageName] = currentVersion;
  }

  fs.writeFileSync(pkgPath, `${JSON.stringify(targetPkg, null, 2)}\n`, "utf8");
  return {
    updated: true,
    reason: "ok",
    previous,
    next: currentVersion,
    section,
  };
}

function initRepo(targetDir, force, minimal, withRuntime, withContracts) {
  const absTarget = path.resolve(targetDir || process.cwd());
  const packageJsonState = ensurePackageJson(absTarget);
  const templateFiles = minimal ? MINIMAL_TEMPLATE_FILES : TEMPLATE_FILES;
  const filesToWrite = new Map(Object.entries(templateFiles));
  const bundledAssets = loadBundledAssets(withRuntime, withContracts);

  for (const [relativePath, content] of bundledAssets.entries()) {
    filesToWrite.set(relativePath, content);
  }

  let written = 0;
  let skipped = 0;
  let chatmodeWritten = false;

  for (const [relativePath, content] of filesToWrite.entries()) {
    const fullPath = path.join(absTarget, relativePath);
    if (fs.existsSync(fullPath) && !force) {
      skipped += 1;
      continue;
    }
    ensureDir(fullPath);
    fs.writeFileSync(fullPath, content, "utf8");
    written += 1;
    if (relativePath === CHATMODE_FILE) {
      chatmodeWritten = true;
    }
  }

  if (chatmodeWritten) {
    setVSCodeReloadMarker(absTarget);
  }

  console.log(`Initialized agents in ${absTarget}`);
  console.log(`Mode: ${minimal ? "minimal" : "full"}`);
  if (withRuntime || withContracts) {
    console.log(
      `Extra assets: ${[
        withRuntime ? "runtime" : null,
        withContracts ? "contracts" : null,
      ]
        .filter(Boolean)
        .join(", ")}`
    );
  }
  console.log(`Files written: ${written}`);
  console.log(`Files skipped: ${skipped}`);
  if (!force) {
    console.log("Tip: use --force to overwrite existing files.");
  }

  if (packageJsonState.created) {
    console.log("package.json: created (minimal npm project scaffold)");
  }

  const npmScripts = ensureNpmRuntimeScripts(absTarget);
  if (npmScripts.reason === "invalid-package-json") {
    console.log("npm scripts: skipped (package.json is invalid JSON)");
  } else if (npmScripts.updated) {
    console.log(`npm scripts: added ${npmScripts.added.join(", ")}`);
  } else {
    console.log("npm scripts: already configured");
  }

  const versionSync = syncPackageVersionInTarget(absTarget);
  if (versionSync.reason === "invalid-package-json") {
    console.log("package version sync: skipped (package.json is invalid JSON)");
  } else if (versionSync.reason === "missing-cli-package-json" || versionSync.reason === "missing-cli-version") {
    console.log("package version sync: skipped (unable to resolve CLI package version)");
  } else if (versionSync.updated) {
    const previous = versionSync.previous ? versionSync.previous : "(empty)";
    console.log(
      `package version sync: ${versionSync.section}.orqestra-dev-agents ${previous} -> ${versionSync.next}`
    );
  } else {
    console.log("package version sync: already synced");
  }

  console.log("\nNext steps:");
  console.log(`1) Validate scaffold: orqestra-dev-agents doctor ${minimal ? "--minimal" : ""}${
    withRuntime || withContracts
      ? ` ${[withRuntime ? "--with-runtime" : null, withContracts ? "--with-contracts" : null]
          .filter(Boolean)
          .join(" ")}`
      : ""
  }`.trim());
  console.log("2) Install VS Code dependencies: orqestra-dev-agents install-vscode");
  console.log("3) Start runtime (recommended for autonomous mode): npm run orqestra:start");
  console.log("4) Open this folder in VS Code.");
  console.log("5) Open your preferred coding assistant.");
  console.log("6) For Copilot, select chat mode: Orqestra Orchestrator.");
  console.log("   If not visible yet, run: Developer: Reload Window.");
  console.log("   Optional check: orqestra-dev-agents vscode-check");
  console.log("   After reload: orqestra-dev-agents vscode-check --ack");
  console.log("   For Claude, Codex, OpenCode, and similar assistants: start from AGENTS.md or .github/skills/orqestra-workflow/SKILL.md.");
  console.log("   Fallback: use agents/orchestrator.agents.md as your orchestrator entrypoint.");
  console.log("7) Send one single objective prompt, for example:");
  console.log(
    '   "Build and automate a production-ready MVP with signup/login, project creation, tests, docs updates, and memory snapshots. Execute in thin vertical slices until a releasable first version is ready, and report progress after each slice."'
  );
  console.log("8) Watch runtime progress from CLI: npm run orqestra:progress");
}

function doctor(targetDir, minimal, withRuntime, withContracts) {
  const absTarget = path.resolve(targetDir || process.cwd());
  const requiredFiles = [...(minimal ? REQUIRED_MINIMAL_FILES : REQUIRED_FILES)];
  if (withRuntime) {
    requiredFiles.push(...RUNTIME_REQUIRED_FILES);
  }
  if (withContracts) {
    requiredFiles.push(...CONTRACT_REQUIRED_FILES);
  }
  const missing = [];

  for (const relativePath of requiredFiles) {
    const fullPath = path.join(absTarget, relativePath);
    if (!fs.existsSync(fullPath)) {
      missing.push(relativePath);
    }
  }

  if (missing.length === 0) {
    const extras = [withRuntime ? "runtime" : null, withContracts ? "contracts" : null]
      .filter(Boolean)
      .join(", ");
    console.log(
      `Doctor check passed for ${absTarget} (${minimal ? "minimal" : "full"} mode${
        extras ? `, ${extras}` : ""
      })`
    );
    return;
  }

  console.log(`Doctor check found missing files in ${absTarget} (${minimal ? "minimal" : "full"} mode):`);
  for (const file of missing) {
    console.log(`- ${file}`);
  }
  process.exitCode = 1;
}

function run(args) {
  const [command, ...rest] = args;

  if (!command) {
    printHelp();
    printNotInitializedHint(process.cwd());
    return;
  }

  if (command === "--help" || command === "-h") {
    printHelp();
    return;
  }

  if (command === "--version" || command === "-v") {
    const pkgPath = path.join(__dirname, "..", "package.json");
    const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
    console.log(pkg.version);
    return;
  }

  if (command === "hub") {
    printHub(process.cwd());
    return;
  }

  if (command === "agents" || command === "agent") {
    handleCatalogCommand("agents", rest, process.cwd());
    return;
  }

  if (command === "workflows" || command === "workflow") {
    handleCatalogCommand("workflows", rest, process.cwd());
    return;
  }

  if (command === "skills" || command === "skill") {
    handleSkillsCommand(rest, process.cwd());
    return;
  }

  if (command === "contracts" || command === "contract") {
    handleCatalogCommand("contracts", rest, process.cwd());
    return;
  }

  if (command === "tools" || command === "tool") {
    handleToolsCommand(rest, process.cwd());
    return;
  }

  if (command === "init") {
    const force = rest.includes("--force");
    const minimal = rest.includes("--minimal");
    const withRuntime = rest.includes("--with-runtime");
    const withContracts = rest.includes("--with-contracts");
    const target = rest.find((item) => !item.startsWith("--")) || process.cwd();
    initRepo(target, force, minimal, withRuntime, withContracts);
    return;
  }

  if (command === "onboarding") {
    const target = rest.find((item) => !item.startsWith("--")) || process.cwd();
    printOnboarding(target);
    return;
  }

  if (command === "doctor") {
    const minimal = rest.includes("--minimal");
    const withRuntime = rest.includes("--with-runtime");
    const withContracts = rest.includes("--with-contracts");
    const target = rest.find((item) => !item.startsWith("--")) || process.cwd();
    doctor(target, minimal, withRuntime, withContracts);
    return;
  }

  if (command === "vscode-check") {
    const acknowledge = rest.includes("--ack");
    const target = rest.find((item) => !item.startsWith("--")) || process.cwd();
    vscodeCheck(target, acknowledge);
    return;
  }

  if (command === "install-vscode") {
    const checkOnly = rest.includes("--check");
    installVSCodeExtensions(checkOnly);
    return;
  }

  if (command === "runtime") {
    TOOL_MAP.get("runtime").run(process.cwd(), rest);
    return;
  }

  console.error(`Unknown command: ${command}`);
  printHelp();
  printNotInitializedHint(process.cwd());
  process.exitCode = 1;
}

module.exports = {
  run,
};
