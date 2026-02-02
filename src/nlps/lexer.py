import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator, Optional

class TokenType(Enum):
    # Literals
    STRING = auto()
    NUMBER = auto()
    BOOL = auto()
    
    # Identifiers and variables
    IDENTIFIER = auto()
    VAR_REF = auto()  # $variable
    
    # Keywords
    RUN = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    IN = auto()
    FN = auto()
    CD = auto()
    ON = auto()
    PARALLEL = auto()
    
    # Special variables
    CWD = auto()
    HOME = auto()
    NLPM_HOME = auto()
    SCRIPT_DIR = auto()
    OS = auto()
    ARG_PREFIX = auto()  # $1, $2, etc
    
    # Operators
    ASSIGN = auto()  # =
    GT = auto()      # >
    LT = auto()      # <
    EQ = auto()      # ==
    
    # Delimiters
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    LBRACKET = auto() # [
    RBRACKET = auto() # ]
    COMMA = auto()    # ,
    
    # Other
    COMMENT = auto()
    NEWLINE = auto()
    EOF = auto()
    STRING_INTERP_START = auto()  # ${

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

class Lexer:
    KEYWORDS = {
        'run': TokenType.RUN,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'for': TokenType.FOR,
        'in': TokenType.IN,
        'fn': TokenType.FN,
        'cd': TokenType.CD,
        'on': TokenType.ON,
        'parallel': TokenType.PARALLEL,
        'true': TokenType.BOOL,
        'false': TokenType.BOOL,
    }
    
    SPECIAL_VARS = {
        'CWD': TokenType.CWD,
        'HOME': TokenType.HOME,
        'NLPM_HOME': TokenType.NLPM_HOME,
        'SCRIPT_DIR': TokenType.SCRIPT_DIR,
        'OS': TokenType.OS,
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
        
    def error(self, msg: str):
        raise SyntaxError(f"Line {self.line}, Column {self.column}: {msg}")
    
    def peek(self, offset: int = 0) -> str:
        pos = self.pos + offset
        if pos >= len(self.source):
            return '\0'
        return self.source[pos]
    
    def advance(self) -> str:
        char = self.peek()
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char
    
    def skip_whitespace(self):
        while self.peek() in ' \t\r':
            self.advance()
    
    def read_string(self) -> str:
        quote = self.advance()  # " or '
        result = ""
        while self.peek() != quote and self.peek() != '\0':
            result += self.advance()
        
        if self.peek() == quote:
            self.advance()
        else:
            self.error(f"Unterminated string literal")
        
        return result
    
    def read_number(self) -> str:
        result = ""
        while self.peek().isdigit():
            result += self.advance()
        if self.peek() == '.' and self.peek(1).isdigit():
            result += self.advance()  # .
            while self.peek().isdigit():
                result += self.advance()
        return result
    
    def read_identifier(self) -> str:
        result = ""
        # Allow alphanumeric, underscore, dot, hyphen, and forward slash for paths
        while self.peek().isalnum() or self.peek() in '_./-':
            result += self.advance()
        return result
    
    def read_comment(self) -> str:
        result = ""
        while self.peek() != '\n' and self.peek() != '\0':
            result += self.advance()
        return result
    
    def tokenize(self) -> list[Token]:
        while True:
            self.skip_whitespace()
            
            char = self.peek()
            line, column = self.line, self.column
            
            if char == '\0':
                self.tokens.append(Token(TokenType.EOF, '', line, column))
                break
            
            elif char == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\n', line, column))
                self.advance()
            
            elif char == '#':
                comment = self.read_comment()
                self.tokens.append(Token(TokenType.COMMENT, comment, line, column))
            
            elif char in '"\'':
                string = self.read_string()
                self.tokens.append(Token(TokenType.STRING, string, line, column))
            
            elif char.isdigit():
                number = self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, number, line, column))
            
            elif char == '$':
                self.advance()  # $
                if self.peek().isdigit():
                    # Argument reference $1, $2, etc
                    num = self.read_number()
                    self.tokens.append(Token(TokenType.ARG_PREFIX, num, line, column))
                elif self.peek() == '@':
                    self.advance()
                    self.tokens.append(Token(TokenType.ARG_PREFIX, '@', line, column))
                elif self.peek() == '#':
                    self.advance()
                    self.tokens.append(Token(TokenType.ARG_PREFIX, '#', line, column))
                elif self.peek().isalpha():
                    name = self.read_identifier()
                    if name in self.SPECIAL_VARS:
                        self.tokens.append(Token(self.SPECIAL_VARS[name], name, line, column))
                    else:
                        self.tokens.append(Token(TokenType.VAR_REF, name, line, column))
                elif self.peek() == '{':
                    self.advance()
                    self.tokens.append(Token(TokenType.STRING_INTERP_START, '${', line, column))
                else:
                    self.error(f"Unexpected character after $")
            
            elif char.isalpha() or char == '_' or char == '.' or (char == '-' and (self.peek(1).isalnum() or self.peek(1) == '-')):
                ident = self.read_identifier()
                if ident in self.KEYWORDS:
                    self.tokens.append(Token(self.KEYWORDS[ident], ident, line, column))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, ident, line, column))
            
            elif char == '{':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACE, '{', line, column))
            
            elif char == '}':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACE, '}', line, column))
            
            elif char == '(':
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, '(', line, column))
            
            elif char == ')':
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ')', line, column))
            
            elif char == '[':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACKET, '[', line, column))
            
            elif char == ']':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACKET, ']', line, column))
            
            elif char == ',':
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ',', line, column))
            
            elif char == '=':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.EQ, '==', line, column))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, '=', line, column))
            
            elif char == '>':
                self.advance()
                self.tokens.append(Token(TokenType.GT, '>', line, column))
            
            elif char == '<':
                self.advance()
                self.tokens.append(Token(TokenType.LT, '<', line, column))
            
            elif char == '\\':
                self.advance()
                self.tokens.append(Token(TokenType.IDENTIFIER, '\\', line, column))
            
            else:
                self.error(f"Unexpected character: {char}")
        
        return self.tokens

def tokenize(source: str) -> list[Token]:
    return Lexer(source).tokenize()
