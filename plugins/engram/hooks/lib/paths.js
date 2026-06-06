'use strict';
// Cross-platform path resolution for Engram. Honors env + config file,
// falls back to a sensible default. Never throws.

const os = require('os');
const path = require('path');
const fs = require('fs');

const HOME = os.homedir();

/** Claude Code config dir (honors CLAUDE_CONFIG_DIR). */
function claudeConfigDir() {
  return process.env.CLAUDE_CONFIG_DIR || path.join(HOME, '.claude');
}

/** Where Engram's per-user config.json lives (XDG on *nix, APPDATA on win). */
function configFile() {
  const base =
    process.env.XDG_CONFIG_HOME ||
    (process.platform === 'win32' && process.env.APPDATA) ||
    path.join(HOME, '.config');
  return path.join(base, 'engram', 'config.json');
}

/**
 * Resolve the Obsidian vault root, in priority order:
 *   1. ENGRAM_VAULT env var
 *   2. "vault" field in the Engram config file
 *   3. ~/claude-code-memory  (default)
 */
function resolveVault() {
  if (process.env.ENGRAM_VAULT) return process.env.ENGRAM_VAULT;
  try {
    const cfg = JSON.parse(fs.readFileSync(configFile(), 'utf8'));
    if (cfg && cfg.vault) return cfg.vault;
  } catch {
    /* no config file — fine */
  }
  return path.join(HOME, 'claude-code-memory');
}

function vaultPaths(vault = resolveVault()) {
  return {
    vault,
    sessions: path.join(vault, 'Sessions'),
    daily: path.join(vault, 'Sessions', 'Daily'),
    memory: path.join(vault, 'Memory'),
    errorLog: path.join(vault, '_engram-errors.log'),
  };
}

module.exports = { HOME, claudeConfigDir, configFile, resolveVault, vaultPaths };
