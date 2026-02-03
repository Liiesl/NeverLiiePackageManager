import os
import sys
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from .parser import *
from .lexer import tokenize

class InterpreterError(Exception):
    pass

class ReturnValue(Exception):
    """Used to return values from functions"""
    def __init__(self, value: Any):
        self.value = value

class Interpreter:
    def __init__(self, script_path: str, args: List[str] = None):
        self.script_path = Path(script_path).resolve()
        self.args = args or []
        self.variables: Dict[str, Any] = {}
        self.functions: Dict[str, FunctionDef] = {}
        self.cwd = str(Path.cwd())
        self.environment = os.environ.copy()
        
    def error(self, msg: str):
        raise InterpreterError(msg)
    
    def get_special_var(self, name: str) -> Any:
        """Get value of special getter variables"""
        if name == 'CWD':
            return self.cwd
        elif name == 'HOME':
            return str(Path.home())
        elif name == 'NLPM_HOME':
            return str(Path.home() / '.nlpm')
        elif name == 'SCRIPT_DIR':
            return str(self.script_path.parent)
        elif name == 'OS':
            return 'windows' if os.name == 'nt' else 'unix'
        else:
            self.error(f"Unknown special variable: {name}")
    
    def evaluate(self, expr: Expression) -> Any:
        """Evaluate an expression and return its value"""
        if isinstance(expr, StringLiteral):
            # Handle string interpolations
            result = expr.value
            # Replace interpolations from right to left to preserve indices
            for start, end, var_name in reversed(expr.interpolations):
                # Check for argument references first
                if var_name == '@':
                    replacement = ' '.join(self.args)
                elif var_name == '#':
                    replacement = str(len(self.args))
                elif var_name.isdigit():
                    # Numbered argument $1, $2, etc.
                    idx = int(var_name) - 1
                    if 0 <= idx < len(self.args):
                        replacement = self.args[idx]
                    else:
                        replacement = ""
                elif var_name in self.variables:
                    replacement = str(self.variables[var_name])
                else:
                    # Try as special variable
                    try:
                        replacement = str(self.get_special_var(var_name))
                    except InterpreterError:
                        replacement = f"${{{var_name}}}"
                result = result[:start] + replacement + result[end:]
            return result
        
        elif isinstance(expr, NumberLiteral):
            return expr.value
        
        elif isinstance(expr, BoolLiteral):
            return expr.value
        
        elif isinstance(expr, VariableRef):
            if expr.name not in self.variables:
                self.error(f"Undefined variable: {expr.name}")
            return self.variables[expr.name]
        
        elif isinstance(expr, SpecialVarRef):
            return self.get_special_var(expr.name)
        
        elif isinstance(expr, ArgRef):
            if expr.index == '@':
                return self.args
            elif expr.index == '#':
                return len(self.args)
            elif isinstance(expr.index, int):
                idx = expr.index - 1  # $1 is index 0
                if idx < 0 or idx >= len(self.args):
                    return ""
                return self.args[idx]
            else:
                self.error(f"Invalid argument reference: {expr.index}")
        
        elif isinstance(expr, Comparison):
            left = self.evaluate(expr.left)
            right = self.evaluate(expr.right)
            
            if expr.operator == '>':
                return left > right
            elif expr.operator == '<':
                return left < right
            elif expr.operator == '==':
                return left == right
            else:
                self.error(f"Unknown operator: {expr.operator}")
        
        elif isinstance(expr, ArrayLiteral):
            return [self.evaluate(elem) for elem in expr.elements]
        
        elif isinstance(expr, FunctionCall):
            return self.call_function(expr)
        
        else:
            self.error(f"Unknown expression type: {type(expr).__name__}")
    
    def execute(self, statements: List[Statement]):
        """Execute a list of statements"""
        for stmt in statements:
            self.execute_statement(stmt)
    
    def execute_statement(self, stmt: Statement):
        """Execute a single statement"""
        if isinstance(stmt, Assignment):
            value = self.evaluate(stmt.value)
            self.variables[stmt.name] = value
            # Also export to environment
            self.environment[stmt.name] = str(value)
        
        elif isinstance(stmt, RunCommand):
            self.execute_run(stmt)
        
        elif isinstance(stmt, CdCommand):
            path = self.evaluate(stmt.path)
            new_path = Path(path)
            if not new_path.is_absolute():
                new_path = Path(self.cwd) / new_path
            new_path = new_path.resolve()
            
            if not new_path.exists():
                self.error(f"Directory does not exist: {path}")
            if not new_path.is_dir():
                self.error(f"Not a directory: {path}")
            
            self.cwd = str(new_path)
            os.chdir(self.cwd)
        
        elif isinstance(stmt, IfStatement):
            condition = self.evaluate(stmt.condition)
            if condition:
                self.execute(stmt.then_block)
            elif stmt.else_block:
                self.execute(stmt.else_block)
        
        elif isinstance(stmt, ForLoop):
            iterable = self.evaluate(stmt.iterable)
            if not isinstance(iterable, list):
                self.error(f"Cannot iterate over {type(iterable).__name__}")
            
            for item in iterable:
                self.variables[stmt.var_name] = item
                self.environment[stmt.var_name] = str(item)
                self.execute(stmt.body)
        
        elif isinstance(stmt, FunctionDef):
            self.functions[stmt.name] = stmt
        
        elif isinstance(stmt, FunctionCall):
            self.call_function(stmt)
        
        elif isinstance(stmt, OsBlock):
            current_os = 'windows' if os.name == 'nt' else 'unix'
            if stmt.os_name == current_os:
                self.execute(stmt.body)
        
        elif isinstance(stmt, ParallelBlock):
            self.execute_parallel(stmt.body)
        
        else:
            self.error(f"Unknown statement type: {type(stmt).__name__}")
    
    def execute_run(self, stmt: RunCommand):
        """Execute a run command via subprocess"""
        command = self.evaluate(stmt.command)
        
        if stmt.detach:
            print(f"[nlps] {command} (detached)")
        else:
            print(f"[nlps] {command}")
        
        # Execute command
        try:
            if stmt.detach:
                # Detached execution - run in background without waiting
                if os.name == 'nt':
                    # Windows: Use CREATE_NEW_PROCESS_GROUP for proper detachment
                    subprocess.Popen(
                        command,
                        shell=True,
                        cwd=self.cwd,
                        env=self.environment,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    # Unix: Run in background
                    args = shlex.split(command)
                    if args:
                        subprocess.Popen(
                            args,
                            cwd=self.cwd,
                            env=self.environment,
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
            elif os.name == 'nt':
                # Windows: use shell=True for proper terminal I/O
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.cwd,
                    env=self.environment
                )
                if result.returncode != 0:
                    print(f"[nlps] Command exited with code {result.returncode}")
            else:
                # Unix: parse and execute
                args = shlex.split(command)
                if not args:
                    return
                
                # Use subprocess for better control
                result = subprocess.run(
                    args,
                    cwd=self.cwd,
                    env=self.environment
                )
                if result.returncode != 0:
                    print(f"[nlps] Command exited with code {result.returncode}")
                    
        except Exception as e:
            self.error(f"Failed to execute command '{command}': {e}")
    
    def execute_parallel(self, statements: List[Statement]):
        """Execute statements in parallel using threads"""
        def execute_in_thread(stmt):
            try:
                # Each thread gets a copy of the interpreter state
                self.execute_statement(stmt)
                return None
            except Exception as e:
                return e
        
        errors = []
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(execute_in_thread, stmt): stmt for stmt in statements}
            for future in as_completed(futures):
                error = future.result()
                if error:
                    errors.append(error)
        
        if errors:
            for err in errors:
                print(f"[nlps] Parallel execution error: {err}")
    
    def call_function(self, call: FunctionCall) -> Any:
        """Call a user-defined function"""
        if call.name not in self.functions:
            self.error(f"Undefined function: {call.name}")
        
        func = self.functions[call.name]
        
        # Check argument count
        if len(call.args) != len(func.params):
            self.error(f"Function '{call.name}' expects {len(func.params)} arguments, got {len(call.args)}")
        
        # Save current scope
        old_vars = self.variables.copy()
        old_env = self.environment.copy()
        
        try:
            # Bind arguments to parameters
            for param, arg in zip(func.params, call.args):
                value = self.evaluate(arg)
                self.variables[param] = value
                self.environment[param] = str(value)
            
            # Execute function body
            for stmt in func.body:
                self.execute_statement(stmt)
            
        finally:
            # Restore scope (but keep any exported env vars)
            self.variables = old_vars
            for key, value in self.environment.items():
                if key not in old_env:
                    old_env[key] = value
            self.environment = old_env
        
        return None
    
    def run(self, source: str) -> int:
        """Parse and execute NLPS source code"""
        try:
            # Parse
            statements = parse(source)
            
            # Execute
            self.execute(statements)
            
            return 0
        except Exception as e:
            print(f"[nlps] Error: {e}", file=sys.stderr)
            return 1

def run_script(script_path: str, args: List[str] = None) -> int:
    """Run a .nlps script file"""
    script_path = Path(script_path)
    
    if not script_path.exists():
        print(f"[nlps] Script not found: {script_path}", file=sys.stderr)
        return 1
    
    try:
        source = script_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"[nlps] Failed to read script: {e}", file=sys.stderr)
        return 1
    
    interpreter = Interpreter(str(script_path), args)
    return interpreter.run(source)
