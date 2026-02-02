# NLPS Language Specification

**NLPS** = **Never Liie Package Script**

## Overview

NLPS is a domain-specific scripting language designed for the NeverLiie Package Manager (NLPM). It provides a natural, English-like syntax for automating package management workflows, build scripts, and system automation tasks.

**File Extension**: `.nlps`

---

## Language Design Principles

- **Natural Syntax**: Commands read like English sentences
- **Shell Integration**: Seamless execution of shell commands
- **Cross-Platform**: First-class support for Windows and Unix
- **Minimal Boilerplate**: Expressive with minimal syntax overhead

---

## Lexical Elements

### Comments

```nlps
# This is a single-line comment
# Comments extend to end of line
```

### Literals

#### Strings
- Double quotes: `"hello world"`
- Single quotes: `'hello world'`
- Escape sequences: `\n` (newline), `\t` (tab), `\r` (carriage return), `\\` (backslash), `\"` (double quote), `\'` (single quote)

#### Numbers
- Integers: `42`, `-10`
- Floats: `3.14`, `-0.5`

#### Booleans
- `true`, `false`

#### Arrays
```nlps
["item1", "item2", "item3"]
```

### Identifiers

- Alphanumeric characters plus underscore: `my_var`, `item2`, `camelCase`
- Path characters allowed in identifiers: `_./-`

---

## Variables

### Variable Declaration and Assignment

```nlps
# Using $ prefix for variable names
$name = "value"
$count = 42
$items = ["a", "b", "c"]

# Without $ in assignment target (also valid)
name = "value"
```

### Variable References

```nlps
run echo $name              # Reference variable
run echo "Hello ${name}"    # Interpolation in strings
```

**Important**: Bare variable references (`$var`) only work in `run` commands. In other contexts (like assignments), use `${var}` syntax:

```nlps
# CORRECT: Use ${} syntax in assignments
$x = "${some_var}"

# WRONG: Bare $var doesn't work in assignments
$x = $some_var  # Error!
```

### Special Variables (Read-only)

| Variable | Description |
|----------|-------------|
| `$CWD` | Current working directory |
| `$HOME` | User's home directory |
| `$NLPM_HOME` | NLPM configuration directory (`~/.nlpm`) |
| `$SCRIPT_DIR` | Directory containing the current script |
| `$OS` | Operating system (`"windows"` or `"unix"`) |

### Command-Line Arguments

| Reference | Description |
|-----------|-------------|
| `$1`, `$2`, ... | Positional arguments (1-indexed) |
| `$@` | All arguments as array |
| `$#` | Number of arguments |

```nlps
# script.nlps with args: foo bar baz
run echo $1        # Output: foo
run echo $2        # Output: bar
run echo $#        # Output: 3
```

---

## String Interpolation

NLPS supports variable interpolation within strings using `${}` syntax:

```nlps
$name = "World"
run echo "Hello, ${name}!"      # Output: Hello, World!
run echo "Current dir: ${CWD}"  # Output: Current dir: /path/to/dir
run echo "Args: ${@}"           # Output: Args: arg1 arg2 arg3
```

---

## Commands

### Run Command

Execute shell commands with the `run` keyword:

```nlps
run echo "Hello World"
run ls -la
run npm install
run python script.py
```

Commands support variable interpolation:

```nlps
$filename = "data.txt"
run cat ${filename}
```

### Change Directory

```nlps
cd "/path/to/directory"
cd $HOME
cd ${SCRIPT_DIR}/../config
```

**Important**: The `cd` command changes the NLPS interpreter's working directory persistently. Do NOT use `run cd` - that only changes the directory in a subprocess which immediately exits.

```nlps
# CORRECT: Changes interpreter's working directory
cd "my-project"
run py script.py  # Runs from my-project/

# WRONG: cd runs in subprocess, doesn't affect interpreter
run cd "my-project"
run py script.py  # Runs from original directory (unexpected!)
```

---

## Control Flow

### If/Else Statements

```nlps
if $OS == "windows" {
    run echo "Running on Windows"
} else {
    run echo "Running on Unix"
}

if $count > 10 {
    run echo "Count is greater than 10"
}

if $name == "test" {
    run echo "Name is test"
}
```

**Comparison Operators**:
- `==` : Equal to
- `>` : Greater than
- `<` : Less than

### For Loops

Iterate over arrays:

```nlps
$files = ["a.txt", "b.txt", "c.txt"]

for $file in $files {
    run echo "Processing: ${file}"
}
```

---

## Functions

### Function Definition

```nlps
fn greet($name) {
    run echo "Hello, ${name}!"
}

fn build($target, $config) {
    run echo "Building ${target} with ${config}"
    run make ${target}
}
```

### Function Calls

```nlps
greet("World")
build("app", "release")
```

**Important Scope Note**: Inside functions, `$1`, `$@`, and `$#` refer to **script-level arguments**, not function parameters. Use parameter names (`$param`) to access function arguments:

```nlps
fn greet($name) {
    # Inside function:
    run echo $1      # Shows SCRIPT'S first arg, NOT $name!
    run echo $name   # Shows function parameter (correct)
}

# Called as: nlpm my-script foo arg1
# Output:
# arg1       (from $1 - script arg)
# foo        (from $name - function param)
```

---

## Platform-Specific Code

Execute code only on specific operating systems:

```nlps
on windows {
    run echo "Windows-specific setup"
    run cmd /c dir
}

on unix {
    run echo "Unix-specific setup"
    run ls -la
}
```

---

## Parallel Execution

Execute statements concurrently:

```nlps
parallel {
    run echo "Task 1"
    run echo "Task 2"
    run echo "Task 3"
}
```

Each statement in a `parallel` block runs in a separate thread.

**Warning**: Parallel statements share variables. Modifying the same variable from multiple parallel statements can cause race conditions:

```nlps
# DON'T DO THIS - race condition!
$counter = 0
parallel {
    $counter = $counter + 1  # Unpredictable result
    $counter = $counter + 1
}
run echo $counter  # Could be 0, 1, or 2
```

Use parallel only for independent operations.

---

## Complete Example

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

---

## Error Handling

NLPS reports errors with line and column information:

```
Line 5, Column 12: Undefined variable: foo
Line 10, Column 3: Expected {, got run
```

Command failures are reported but don't stop script execution (non-zero exit codes are printed as warnings).

---

## Best Practices

1. **Quote paths with spaces**: `cd "/path/with spaces"`
2. **Use string interpolation**: `run echo "Value: ${var}"` instead of `run echo Value: $var`
3. **Leverage platform blocks**: Use `on windows`/`on unix` for OS-specific commands
4. **Use functions**: Break complex scripts into reusable functions
5. **Comment liberally**: Use `#` to document intent
6. **Use `cd` not `run cd`**: The `cd` command changes the interpreter's working directory; `run cd` only affects a temporary subprocess
7. **Use `${var}` syntax in assignments**: Bare `$var` only works in `run` commands, not in `$x = $var`
8. **Use function parameter names, not `$1`**: Inside functions, `$1` refers to script args, use `$param` instead
9. **Don't modify shared variables in parallel blocks**: Parallel execution has race conditions for variable writes
10. **Functions don't return values**: They can only execute statements, not return computed results

---

## Grammar Reference (EBNF)

```ebnf
program         ::= statement*

statement       ::= assignment
                  | run_command
                  | cd_command
                  | if_statement
                  | for_loop
                  | function_def
                  | function_call
                  | os_block
                  | parallel_block
                  | comment

assignment      ::= (identifier | var_ref) "=" expression

run_command     ::= "run" command_string

cd_command      ::= "cd" expression

if_statement    ::= "if" expression "{" statement* "}" [ "else" "{" statement* "}" ]

for_loop        ::= "for" var_ref "in" expression "{" statement* "}"

function_def    ::= "fn" identifier "(" [param_list] ")" "{" statement* "}"
param_list      ::= (identifier | var_ref) { "," (identifier | var_ref) }

function_call   ::= identifier "(" [arg_list] ")"
arg_list        ::= expression { "," expression }

os_block        ::= "on" ("windows" | "unix") "{" statement* "}"

parallel_block  ::= "parallel" "{" statement* "}"

expression      ::= comparison
                  | primary

comparison      ::= primary (">" | "<" | "==") primary

primary         ::= string
                  | number
                  | boolean
                  | var_ref
                  | special_var
                  | arg_ref
                  | array
                  | function_call

array           ::= "[" [expression { "," expression }] "]"

var_ref         ::= "$" identifier
special_var     ::= "$" ("CWD" | "HOME" | "NLPM_HOME" | "SCRIPT_DIR" | "OS")
arg_ref         ::= "$" (digit+ | "@" | "#")

comment         ::= "#" text_until_newline
```

---

## Running NLPS Scripts

Scripts can be executed through NLPM:

```bash
# If registered as a command
nlpm my-script

# With arguments
nlpm my-script arg1 arg2

# Direct execution (future)
nlps script.nlps
```

---

## Version History

- **v0.1.0** - Initial release with basic commands, variables, and control flow
- **v0.2.0** - Added functions, parallel execution, and platform-specific blocks

---

*NLPS is part of the NeverLiie Package Manager ecosystem.*
