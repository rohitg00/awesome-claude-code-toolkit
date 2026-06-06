#!/usr/bin/env bash
set -euo pipefail

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_DIR="$HOME/.claude"
CLAUDE_COMMANDS="$CLAUDE_DIR/commands"
CLAUDE_HOOKS="$CLAUDE_DIR"

detect_os() {
  case "$(uname -s)" in
    Darwin) echo "macos" ;;
    Linux)  echo "linux" ;;
    *)      echo "unknown" ;;
  esac
}

print_header() {
  echo ""
  echo "========================================"
  echo "  Claude Code Toolkit Installer"
  echo "========================================"
  echo ""
  echo "OS: $(detect_os)"
  echo "Toolkit: $TOOLKIT_DIR"
  echo "Target:  $CLAUDE_DIR"
  echo ""
}

prompt_yn() {
  local prompt="$1"
  local default="${2:-n}"
  local reply
  if [[ "$default" == "y" ]]; then
    read -rp "$prompt [Y/n]: " reply
    reply="${reply:-y}"
  else
    read -rp "$prompt [y/N]: " reply
    reply="${reply:-n}"
  fi
  [[ "$reply" =~ ^[Yy]$ ]]
}

install_commands() {
  echo "--- Installing Commands ---"
  local categories=("git" "testing" "architecture" "documentation" "security" "refactoring" "devops")
  local installed=0

  for category in "${categories[@]}"; do
    local src="$TOOLKIT_DIR/commands/$category"
    if [[ ! -d "$src" ]]; then
      continue
    fi

    local dest="$CLAUDE_COMMANDS/$category"
    mkdir -p "$dest"

    for cmd_file in "$src"/*.md; do
      [[ -f "$cmd_file" ]] || continue
      local name
      name="$(basename "$cmd_file")"
      cp "$cmd_file" "$dest/$name"
      installed=$((installed + 1))
    done
  done

  echo "Installed $installed command files."
}

install_hooks() {
  echo "--- Installing Hooks ---"
  local hooks_src="$TOOLKIT_DIR/hooks"

  if [[ ! -f "$hooks_src/hooks.json" ]]; then
    echo "No hooks.json found. Skipping."
    return
  fi

  local scripts_dest="$CLAUDE_DIR/hooks/scripts"
  mkdir -p "$scripts_dest"

  cp "$hooks_src/hooks.json" "$CLAUDE_DIR/hooks.json"
  echo "Installed hooks.json"

  if [[ -d "$hooks_src/scripts" ]]; then
    local script_count=0
    for script in "$hooks_src/scripts"/*.js; do
      [[ -f "$script" ]] || continue
      cp "$script" "$scripts_dest/"
      script_count=$((script_count + 1))
    done
    echo "Installed $script_count hook scripts."
  fi

  echo ""
  echo "NOTE: Update hook script paths in hooks.json to use absolute paths"
  echo "      pointing to $CLAUDE_DIR/hooks/scripts/ for production use."
}

install_rules() {
  echo "--- Installing Rules ---"
  local rules_src="$TOOLKIT_DIR/rules"
  local rules_dest="$CLAUDE_DIR/rules"
  mkdir -p "$rules_dest"

  local count=0
  for rule in "$rules_src"/*.md; do
    [[ -f "$rule" ]] || continue
    cp "$rule" "$rules_dest/"
    count=$((count + 1))
  done
  echo "Installed $count rule files."
}

install_templates() {
  echo "--- Installing Templates ---"
  local tpl_src="$TOOLKIT_DIR/templates/claude-md"
  local tpl_dest="$CLAUDE_DIR/templates"
  mkdir -p "$tpl_dest"

  local count=0
  for tpl in "$tpl_src"/*.md; do
    [[ -f "$tpl" ]] || continue
    cp "$tpl" "$tpl_dest/"
    count=$((count + 1))
  done
  echo "Installed $count CLAUDE.md templates."
}

install_mcp_config() {
  echo "--- MCP Configuration ---"
  local mcp_src="$TOOLKIT_DIR/mcp-configs/recommended.json"

  if [[ ! -f "$mcp_src" ]]; then
    echo "No MCP config found. Skipping."
    return
  fi

  local mcp_dest="$CLAUDE_DIR/mcp-configs"
  mkdir -p "$mcp_dest"
  cp "$mcp_src" "$mcp_dest/recommended.json"
  echo "Copied recommended MCP config to $mcp_dest/"
  echo ""
  echo "To use: copy the servers you need from recommended.json"
  echo "into your project's .mcp.json or ~/.claude/mcp.json"
  echo "and replace placeholder values with your actual credentials."
}

main() {
  print_header

  mkdir -p "$CLAUDE_DIR"

  if prompt_yn "Install slash commands?" "y"; then
    install_commands
    echo ""
  fi

  if prompt_yn "Install hooks?" "y"; then
    install_hooks
    echo ""
  fi

  if prompt_yn "Install rules?" "y"; then
    install_rules
    echo ""
  fi

  if prompt_yn "Install CLAUDE.md templates?" "y"; then
    install_templates
    echo ""
  fi

  if prompt_yn "Copy MCP server config reference?" "y"; then
    install_mcp_config
    echo ""
  fi

  echo "========================================"
  echo "  Installation Complete"
  echo "========================================"
  echo ""
  echo "Installed to: $CLAUDE_DIR"
  echo ""
  echo "Next steps:"
  echo "  1. Review installed files in $CLAUDE_DIR"
  echo "  2. Customize rules and commands for your workflow"
  echo "  3. Configure MCP servers with your credentials"
  echo "  4. Use /git:commit, /testing:tdd, etc. in Claude Code"
  echo ""
}

main
