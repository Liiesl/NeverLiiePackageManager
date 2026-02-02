from dataclasses import dataclass
from typing import List, Optional, Union
from .lexer import Token, TokenType, tokenize

# AST Node Types
@dataclass
class StringLiteral:
    value: str
    interpolations: List[tuple]  # List of (start, end, var_name) for ${var} patterns

@dataclass
class NumberLiteral:
    value: Union[int, float]

@dataclass
class BoolLiteral:
    value: bool

@dataclass
class VariableRef:
    name: str

@dataclass
class SpecialVarRef:
    name: str  # CWD, HOME, NLPM_HOME, SCRIPT_DIR, OS

@dataclass
class ArgRef:
    index: Union[int, str]  # int for $1, $2, etc; '@' for $@, '#' for $#

@dataclass
class Assignment:
    name: str
    value: 'Expression'

@dataclass
class RunCommand:
    command: StringLiteral

@dataclass
class CdCommand:
    path: 'Expression'

@dataclass
class IfStatement:
    condition: 'Expression'
    then_block: List['Statement']
    else_block: Optional[List['Statement']]

@dataclass
class ForLoop:
    var_name: str
    iterable: 'Expression'
    body: List['Statement']

@dataclass
class FunctionDef:
    name: str
    params: List[str]
    body: List['Statement']

@dataclass
class FunctionCall:
    name: str
    args: List['Expression']

@dataclass
class OsBlock:
    os_name: str  # 'windows' or 'unix'
    body: List['Statement']

@dataclass
class ParallelBlock:
    body: List['Statement']

@dataclass
class Comparison:
    left: 'Expression'
    operator: str  # '>', '<', '=='
    right: 'Expression'

@dataclass
class ArrayLiteral:
    elements: List['Expression']

# Type alias for all expression types
Expression = Union[StringLiteral, NumberLiteral, BoolLiteral, VariableRef, 
                   SpecialVarRef, ArgRef, Comparison, ArrayLiteral, FunctionCall]

# Type alias for all statement types
Statement = Union[Assignment, RunCommand, CdCommand, IfStatement, ForLoop,
                  FunctionDef, FunctionCall, OsBlock, ParallelBlock]

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        
    def error(self, msg: str):
        token = self.current()
        raise ParseError(f"Line {token.line}, Column {token.column}: {msg}")
    
    def current(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]
    
    def peek(self, offset: int = 0) -> Token:
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[pos]
    
    def advance(self) -> Token:
        token = self.current()
        self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        token = self.current()
        if token.type != token_type:
            self.error(f"Expected {token_type.name}, got {token.type.name}")
        return self.advance()
    
    def match(self, *types: TokenType) -> bool:
        return self.current().type in types
    
    def skip_newlines(self):
        while self.match(TokenType.NEWLINE, TokenType.COMMENT):
            self.advance()
    
    def parse(self) -> List[Statement]:
        statements = []
        self.skip_newlines()
        while not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        return statements
    
    def parse_statement(self) -> Optional[Statement]:
        self.skip_newlines()
        
        if self.match(TokenType.EOF):
            return None
        
        if self.match(TokenType.COMMENT):
            self.advance()
            return None
        
        if self.match(TokenType.RUN):
            return self.parse_run()
        
        if self.match(TokenType.CD):
            return self.parse_cd()
        
        if self.match(TokenType.IF):
            return self.parse_if()
        
        if self.match(TokenType.FOR):
            return self.parse_for()
        
        if self.match(TokenType.FN):
            return self.parse_function_def()
        
        if self.match(TokenType.ON):
            return self.parse_os_block()
        
        if self.match(TokenType.PARALLEL):
            return self.parse_parallel()
        
        if self.match(TokenType.IDENTIFIER):
            # Could be function call or assignment target
            next_tok = self.peek(1)
            if next_tok.type == TokenType.ASSIGN:
                return self.parse_assignment()
            elif next_tok.type == TokenType.LPAREN:
                return self.parse_function_call()
        
        if self.match(TokenType.VAR_REF):
            # Variable assignment: $NAME = value
            return self.parse_var_assignment()
        
        self.error(f"Unexpected token: {self.current().value}")
    
    def parse_run(self) -> RunCommand:
        self.advance()  # consume 'run'
        self.skip_newlines()
        
        # The rest of the line is the command string
        cmd_parts = []
        while not self.match(TokenType.NEWLINE, TokenType.EOF, TokenType.COMMENT):
            # Handle escaped quotes: backslash followed by a string token
            if self.match(TokenType.IDENTIFIER) and self.current().value == '\\':
                # Check if next token is a string (for escaped quotes)
                next_tok = self.peek(1)
                if next_tok.type == TokenType.STRING:
                    self.advance()  # consume backslash
                    str_val = self.advance().value  # consume string
                    # Prepend a quote to create escaped quote effect
                    str_val = '"' + str_val
                    # Convert bare $VAR patterns to ${VAR} for interpolation
                    str_val = self.convert_vars_to_interpolation(str_val)
                    cmd_parts.append(str_val)
                    continue
            
            if self.match(TokenType.STRING):
                str_val = self.advance().value
                # Convert bare $VAR patterns to ${VAR} for interpolation
                str_val = self.convert_vars_to_interpolation(str_val)
                # Wrap in quotes to preserve spaces and special chars
                cmd_parts.append(f'"{str_val}"')
            elif self.match(TokenType.NUMBER):
                cmd_parts.append(self.advance().value)
            elif self.match(TokenType.IDENTIFIER):
                cmd_parts.append(self.advance().value)
            elif self.match(TokenType.VAR_REF):
                cmd_parts.append(f"${{{self.advance().value}}}")
            elif self.match(TokenType.CWD, TokenType.HOME, TokenType.NLPM_HOME, 
                           TokenType.SCRIPT_DIR, TokenType.OS):
                cmd_parts.append(f"${{{self.advance().value}}}")
            elif self.match(TokenType.ARG_PREFIX):
                arg_tok = self.advance()
                if arg_tok.value == '@':
                    cmd_parts.append("${@}")
                elif arg_tok.value == '#':
                    cmd_parts.append("${#}")
                else:
                    cmd_parts.append(f"${{{arg_tok.value}}}")
            else:
                # Take the raw value for any other token
                cmd_parts.append(self.advance().value)
        
        command_str = ' '.join(cmd_parts)
        return RunCommand(self.create_string_literal(command_str))
    
    def parse_cd(self) -> CdCommand:
        self.advance()  # consume 'cd'
        self.skip_newlines()
        path = self.parse_expression()
        return CdCommand(path)
    
    def parse_assignment(self) -> Assignment:
        name = self.advance().value  # IDENTIFIER
        self.expect(TokenType.ASSIGN)
        value = self.parse_expression()
        return Assignment(name, value)
    
    def parse_var_assignment(self) -> Assignment:
        var_tok = self.advance()  # VAR_REF
        self.expect(TokenType.ASSIGN)
        value = self.parse_expression()
        return Assignment(var_tok.value, value)
    
    def parse_expression(self) -> Expression:
        return self.parse_comparison()
    
    def parse_comparison(self) -> Expression:
        left = self.parse_primary()
        
        if self.match(TokenType.GT, TokenType.LT, TokenType.EQ):
            op = self.advance().value
            right = self.parse_primary()
            return Comparison(left, op, right)
        
        return left
    
    def parse_primary(self) -> Expression:
        if self.match(TokenType.STRING):
            val = self.advance().value
            return self.create_string_literal(val)
        
        if self.match(TokenType.NUMBER):
            val = self.advance().value
            if '.' in val:
                return NumberLiteral(float(val))
            return NumberLiteral(int(val))
        
        if self.match(TokenType.BOOL):
            val = self.advance().value
            return BoolLiteral(val == 'true')
        
        if self.match(TokenType.VAR_REF):
            return VariableRef(self.advance().value)
        
        if self.match(TokenType.CWD, TokenType.HOME, TokenType.NLPM_HOME, 
                      TokenType.SCRIPT_DIR, TokenType.OS):
            return SpecialVarRef(self.advance().value)
        
        if self.match(TokenType.ARG_PREFIX):
            arg_tok = self.advance()
            if arg_tok.value in ('@', '#'):
                return ArgRef(arg_tok.value)
            return ArgRef(int(arg_tok.value))
        
        if self.match(TokenType.LBRACKET):
            return self.parse_array()
        
        if self.match(TokenType.IDENTIFIER):
            next_tok = self.peek(1)
            if next_tok.type == TokenType.LPAREN:
                return self.parse_function_call()
            # Just an identifier value
            return VariableRef(self.advance().value)
        
        self.error(f"Unexpected token in expression: {self.current().type.name}")
    
    def parse_array(self) -> ArrayLiteral:
        self.expect(TokenType.LBRACKET)
        elements = []
        
        while not self.match(TokenType.RBRACKET, TokenType.EOF):
            elements.append(self.parse_expression())
            
            if self.match(TokenType.COMMA):
                self.advance()  # consume comma
            elif self.match(TokenType.COMMENT):
                self.advance()  # consume comment
            elif self.match(TokenType.RBRACKET):
                break  # end of array
            else:
                # No comma but not at end - might be missing comma or end
                self.error("Expected comma or closing bracket in array")
        
        self.expect(TokenType.RBRACKET)
        return ArrayLiteral(elements)
    
    def parse_if(self) -> IfStatement:
        self.advance()  # consume 'if'
        condition = self.parse_expression()
        
        self.expect(TokenType.LBRACE)
        then_block = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        else_block = None
        if self.match(TokenType.ELSE):
            self.advance()
            self.expect(TokenType.LBRACE)
            else_block = self.parse_block()
            self.expect(TokenType.RBRACE)
        
        return IfStatement(condition, then_block, else_block)
    
    def parse_for(self) -> ForLoop:
        self.advance()  # consume 'for'
        
        if not self.match(TokenType.VAR_REF):
            self.error("Expected $variable after 'for'")
        var_name = self.advance().value
        
        self.expect(TokenType.IN)
        iterable = self.parse_expression()
        
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        return ForLoop(var_name, iterable, body)
    
    def parse_function_def(self) -> FunctionDef:
        self.advance()  # consume 'fn'
        
        if not self.match(TokenType.IDENTIFIER):
            self.error("Expected function name after 'fn'")
        name = self.advance().value
        
        self.expect(TokenType.LPAREN)
        params = []
        
        while not self.match(TokenType.RPAREN, TokenType.EOF):
            if self.match(TokenType.VAR_REF):
                params.append(self.advance().value)
            elif self.match(TokenType.IDENTIFIER):
                params.append(self.advance().value)
            else:
                self.error(f"Expected parameter name")
            
            if self.match(TokenType.COMMENT):
                self.advance()
        
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        return FunctionDef(name, params, body)
    
    def parse_function_call(self) -> FunctionCall:
        name = self.advance().value
        self.expect(TokenType.LPAREN)
        
        args = []
        while not self.match(TokenType.RPAREN, TokenType.EOF):
            args.append(self.parse_expression())
            if self.match(TokenType.COMMENT):
                self.advance()
        
        self.expect(TokenType.RPAREN)
        return FunctionCall(name, args)
    
    def parse_os_block(self) -> OsBlock:
        self.advance()  # consume 'on'
        
        if not self.match(TokenType.IDENTIFIER):
            self.error("Expected 'windows' or 'unix' after 'on'")
        os_name = self.advance().value
        
        if os_name not in ('windows', 'unix'):
            self.error(f"Expected 'windows' or 'unix', got '{os_name}'")
        
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        return OsBlock(os_name, body)
    
    def parse_parallel(self) -> ParallelBlock:
        self.advance()  # consume 'parallel'
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        return ParallelBlock(body)
    
    def parse_block(self) -> List[Statement]:
        statements = []
        self.skip_newlines()
        
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            if self.match(TokenType.COMMENT):
                self.advance()
                continue
            
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        
        return statements
    
    def convert_vars_to_interpolation(self, text: str) -> str:
        """Convert bare $VAR patterns to ${VAR} patterns for interpolation"""
        import re
        # Match $VAR where VAR is alphanumeric/underscore/@/#, but not already ${VAR}
        pattern = r'\$(?![{\(])(\w+|@|#)'
        return re.sub(pattern, r'${\1}', text)
    
    def create_string_literal(self, value: str) -> StringLiteral:
        # Parse interpolations like ${var}, ${@}, ${#}, ${1}, etc.
        interpolations = []
        import re
        pattern = r'\$\{(\w+|@|#)\}'
        for match in re.finditer(pattern, value):
            interpolations.append((match.start(), match.end(), match.group(1)))
        return StringLiteral(value, interpolations)

def parse(source: str) -> List[Statement]:
    tokens = tokenize(source)
    parser = Parser(tokens)
    return parser.parse()
