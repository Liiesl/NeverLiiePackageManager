# NLPS Language Support for VSCode

This extension provides language support for **NLPS (Never Liie Package Script)** - a domain-specific scripting language for the NeverLiie Package Manager (NLPM).

## Features

### Syntax Highlighting
- **Comments**: `# single-line comments`
- **Keywords**: `run`, `cd`, `if`, `else`, `for`, `fn`, `on`, `parallel`
- **Variables**: `$var`, `$1`, `$2`, `$@`, `$#`, `$CWD`, `$HOME`, `$NLPM_HOME`, `$SCRIPT_DIR`, `$OS`
- **Strings**: Single and double quotes with escape sequences (`\n`, `\t`, `\r`, `\\`)
- **String Interpolation**: `${variable}` syntax
- **Numbers**: Integers and floats
- **Booleans**: `true`, `false`
- **Platform Constants**: `windows`, `unix`
- **Operators**: `==`, `>`, `<`, `=`

### Editor Features
- **Comment toggling**: Use `Ctrl+/` (or `Cmd+/` on Mac) to toggle line comments
- **Auto-indentation**: Automatic indentation for `{}` blocks
- **Bracket matching**: Supports `{}`, `[]`, `()`
- **Auto-closing pairs**: Quotes and brackets auto-close

## Example

```nlps
# Build script for a Node.js project

$PROJECT_NAME = "my-app"
$BUILD_DIR = "dist"

run echo "Building ${PROJECT_NAME}..."

# Clean previous build
run rm -rf ${BUILD_DIR}

# Install dependencies
run npm ci

# Platform-specific build steps
on windows {
    run set NODE_ENV=production
    run npm run build:win
}

on unix {
    run export NODE_ENV=production
    run npm run build
}

# Verify build output
if $# > 0 {
    for $arg in $@ {
        run echo "Build arg: ${arg}"
    }
}

run echo "Build complete!"
```

## Installation

1. Copy this extension folder to your VSCode extensions directory:
   - Windows: `%USERPROFILE%\.vscode\extensions\`
   - macOS/Linux: `~/.vscode/extensions/`

2. Restart VSCode

3. Open any `.nlps` file to see syntax highlighting

## NLPS Language Reference

### Variables
- User-defined: `$name = "value"`
- Special variables: `$CWD`, `$HOME`, `$NLPM_HOME`, `$SCRIPT_DIR`, `$OS`
- Arguments: `$1`, `$2`, `$@` (all args), `$#` (arg count)

### Commands
- `run <command>` - Execute shell command
- `cd <path>` - Change directory

### Control Flow
- `if <condition> { ... } else { ... }`
- `for $var in $array { ... }`

### Functions
- `fn name($param) { ... }`
- Call: `name(arg)`

### Platform Blocks
- `on windows { ... }`
- `on unix { ... }`

### Parallel Execution
- `parallel { ... }`

## Requirements

- VSCode 1.60.0 or higher

## License

MIT

## More Information

For the full NLPS specification, see the [NLPS_SPEC.md](../NLPS_SPEC.md) file.

NLPS is part of the [NeverLiie Package Manager](https://github.com/neverliie/nlpm) ecosystem.
