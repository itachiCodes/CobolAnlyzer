"""
COBOL Analysis Framework - A comprehensive tool for analyzing Micro Focus COBOL programs

This framework provides functionality to:
1. Parse and tokenize COBOL source code
2. Extract program dependencies
3. Identify input/output files
4. Detect resource usage
5. Map calling and called programs
6. Generate structured representation of program logic
7. Export analysis results for LLM processing
"""

import os
import re
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Any, Tuple
from enum import Enum, auto
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TokenType(Enum):
    """Enum representing different COBOL token types"""
    KEYWORD = auto()
    IDENTIFIER = auto()
    LITERAL = auto()
    NUMBER = auto()
    OPERATOR = auto()
    PUNCTUATION = auto()
    COMMENT = auto()
    DIVISION = auto()
    SECTION = auto()
    PARAGRAPH = auto()
    STATEMENT = auto()
    SPECIAL = auto()
    UNKNOWN = auto()


@dataclass
class Token:
    """Represents a COBOL token with type, value, and position information"""
    type: TokenType
    value: str
    line: int
    column: int

    def __str__(self):
        return f"{self.type.name}: '{self.value}' at line {self.line}, column {self.column}"


@dataclass
class FileReference:
    """Represents a file referenced in a COBOL program"""
    name: str
    access_mode: str  # READ, WRITE, I-O
    organization: Optional[str] = None  # SEQUENTIAL, INDEXED, etc.
    record_key: Optional[str] = None
    location: Tuple[int, int] = (0, 0)  # Line, column


@dataclass
class ProgramCall:
    """Represents a call to another program"""
    target: str
    is_dynamic: bool = False
    parameters: List[str] = field(default_factory=list)
    location: Tuple[int, int] = (0, 0)  # Line, column


@dataclass
class DataItem:
    """Represents a data item defined in the DATA DIVISION"""
    name: str
    level: int
    picture: Optional[str] = None
    usage: Optional[str] = None
    value: Optional[str] = None
    redefines: Optional[str] = None
    occurs: Optional[int] = None
    indexed_by: List[str] = field(default_factory=list)
    location: Tuple[int, int] = (0, 0)  # Line, column


@dataclass
class Paragraph:
    """Represents a paragraph in the PROCEDURE DIVISION"""
    name: str
    start_line: int
    end_line: int
    statements: List[Any] = field(default_factory=list)
    calls: List[ProgramCall] = field(default_factory=list)


@dataclass
class Section:
    """Represents a section in a COBOL division"""
    name: str
    start_line: int
    end_line: int
    paragraphs: Dict[str, Paragraph] = field(default_factory=dict)


@dataclass
class Division:
    """Represents a division in a COBOL program"""
    name: str
    start_line: int
    end_line: int
    sections: Dict[str, Section] = field(default_factory=dict)


@dataclass
class Resource:
    """Represents a system resource used by the program"""
    name: str
    type: str  # DB2, CICS, MQ, etc.
    operation: str
    location: Tuple[int, int] = (0, 0)  # Line, column


@dataclass
class CobolProgram:
    """Main class representing a parsed COBOL program"""
    name: str
    source_path: str
    divisions: Dict[str, Division] = field(default_factory=dict)
    data_items: Dict[str, DataItem] = field(default_factory=dict)
    files: List[FileReference] = field(default_factory=list)
    calls: List[ProgramCall] = field(default_factory=list)
    resources: List[Resource] = field(default_factory=list)
    called_by: Set[str] = field(default_factory=set)
    maps_used: Set[str] = field(default_factory=set)
    copybooks: Set[str] = field(default_factory=set)

    def to_dict(self):
        """Convert program analysis to dictionary"""
        return asdict(self)

    def to_json(self, pretty=True):
        """Convert program analysis to JSON string"""
        indent = 2 if pretty else None
        return json.dumps(self.to_dict(), indent=indent)

    def save_analysis(self, output_path=None):
        """Save program analysis to JSON file"""
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(self.source_path))[0]
            output_path = f"{base_name}_analysis.json"

        with open(output_path, 'w') as f:
            f.write(self.to_json())

        logger.info(f"Analysis saved to {output_path}")
        return output_path


class CobolTokenizer:
    """Tokenizes COBOL source code into a stream of tokens"""

    # COBOL keywords
    KEYWORDS = {
        'ACCEPT', 'ACCESS', 'ADD', 'ADDRESS', 'ADVANCING', 'AFTER', 'ALL', 'ALPHABET',
        'ALPHABETIC', 'ALPHABETIC-LOWER', 'ALPHABETIC-UPPER', 'ALPHANUMERIC', 'ALPHANUMERIC-EDITED',
        'ALSO', 'ALTER', 'ALTERNATE', 'AND', 'ANY', 'APPLY', 'ARE', 'AREA', 'AREAS', 'ASCENDING',
        'ASSIGN', 'AT', 'AUTHOR', 'BASIS', 'BEFORE', 'BEGINNING', 'BINARY', 'BLANK', 'BLOCK',
        'BOTTOM', 'BY', 'CALL', 'CANCEL', 'CBL', 'CD', 'CF', 'CH', 'CHARACTER', 'CHARACTERS',
        'CLASS', 'CLOCK-UNITS', 'CLOSE', 'COBOL', 'CODE', 'CODE-SET', 'COLLATING', 'COLUMN',
        'COMMA', 'COMMON', 'COMMUNICATION', 'COMP', 'COMP-1', 'COMP-2', 'COMP-3', 'COMP-4',
        'COMPUTATIONAL', 'COMPUTATIONAL-1', 'COMPUTATIONAL-2', 'COMPUTATIONAL-3', 'COMPUTATIONAL-4',
        'COMPUTE', 'CONFIGURATION', 'CONTAINS', 'CONTENT', 'CONTINUE', 'CONTROL', 'CONTROLS',
        'CONVERTING', 'COPY', 'CORR', 'CORRESPONDING', 'COUNT', 'CURRENCY', 'DATA', 'DATE',
        'DATE-COMPILED', 'DATE-WRITTEN', 'DAY', 'DAY-OF-WEEK', 'DB', 'DB-ACCESS-CONTROL-KEY',
        'DB-DATA-NAME', 'DB-EXCEPTION', 'DB-RECORD-NAME', 'DB-SET-NAME', 'DB-STATUS', 'DBCS',
        'DE', 'DEBUG-CONTENTS', 'DEBUG-ITEM', 'DEBUG-LINE', 'DEBUG-NAME', 'DEBUG-SUB-1',
        'DEBUG-SUB-2', 'DEBUG-SUB-3', 'DEBUGGING', 'DECIMAL-POINT', 'DECLARATIVES', 'DELETE',
        'DELIMITED', 'DELIMITER', 'DEPENDING', 'DESCENDING', 'DESTINATION', 'DETAIL', 'DISABLE',
        'DISPLAY', 'DIVIDE', 'DIVISION', 'DOWN', 'DUPLICATES', 'DYNAMIC', 'EGI', 'ELSE', 'EMI',
        'ENABLE', 'ENCRYPTION', 'END', 'END-ADD', 'END-CALL', 'END-COMPUTE', 'END-DELETE',
        'END-DIVIDE', 'END-EVALUATE', 'END-EXEC', 'END-IF', 'END-MULTIPLY', 'END-OF-PAGE',
        'END-PERFORM', 'END-READ', 'END-RECEIVE', 'END-RETURN', 'END-REWRITE', 'END-SEARCH',
        'END-START', 'END-STRING', 'END-SUBTRACT', 'END-UNSTRING', 'END-WRITE', 'ENDING', 'ENTER',
        'ENTRY', 'ENVIRONMENT', 'EOP', 'EQUAL', 'ERROR', 'ESI', 'EVALUATE', 'EVERY', 'EXCEPTION',
        'EXEC', 'EXECUTE', 'EXIT', 'EXTEND', 'EXTERNAL', 'FALSE', 'FD', 'FILE', 'FILE-CONTROL',
        'FILLER', 'FINAL', 'FIRST', 'FOOTING', 'FOR', 'FROM', 'FUNCTION', 'GENERATE', 'GIVING',
        'GLOBAL', 'GO', 'GOBACK', 'GREATER', 'GROUP', 'HEADING', 'HIGH-VALUE', 'HIGH-VALUES',
        'I-O', 'I-O-CONTROL', 'ID', 'IDENTIFICATION', 'IF', 'IN', 'INDEX', 'INDEXED', 'INDICATE',
        'INITIAL', 'INITIALIZE', 'INITIATE', 'INPUT', 'INPUT-OUTPUT', 'INSPECT', 'INSTALLATION',
        'INTO', 'INVALID', 'INVOKE', 'IS', 'JUST', 'JUSTIFIED', 'KEY', 'LABEL', 'LAST', 'LEADING',
        'LEFT', 'LENGTH', 'LESS', 'LIMIT', 'LIMITS', 'LINAGE', 'LINAGE-COUNTER', 'LINE',
        'LINE-COUNTER', 'LINES', 'LINKAGE', 'LOCAL-STORAGE', 'LOCK', 'LOW-VALUE', 'LOW-VALUES',
        'MEMORY', 'MERGE', 'MESSAGE', 'METACLASS', 'METHOD', 'METHOD-ID', 'MODE', 'MODULES',
        'MORE-LABELS', 'MOVE', 'MULTIPLE', 'MULTIPLY', 'NATIVE', 'NEGATIVE', 'NEXT', 'NO',
        'NOT', 'NULL', 'NULLS', 'NUMBER', 'NUMERIC', 'NUMERIC-EDITED', 'OBJECT', 'OBJECT-COMPUTER',
        'OCCURS', 'OF', 'OFF', 'OMITTED', 'ON', 'OPEN', 'OPTIONAL', 'OR', 'ORDER', 'ORGANIZATION',
        'OTHER', 'OUTPUT', 'OVERFLOW', 'OVERRIDE', 'PACKED-DECIMAL', 'PADDING', 'PAGE',
        'PAGE-COUNTER', 'PASSWORD', 'PERFORM', 'PF', 'PH', 'PIC', 'PICTURE', 'PLUS', 'POINTER',
        'POSITION', 'POSITIVE', 'PRINTING', 'PROCEDURE', 'PROCEDURES', 'PROCEED', 'PROGRAM',
        'PROGRAM-ID', 'PROPERTY', 'PROTOTYPE', 'PURGE', 'QUEUE', 'QUOTE', 'QUOTES', 'RANDOM',
        'RD', 'READ', 'READY', 'RECEIVE', 'RECORD', 'RECORDING', 'RECORDS', 'RECURSIVE',
        'REDEFINES', 'REEL', 'REFERENCE', 'REFERENCES', 'RELATIVE', 'RELEASE', 'RELOAD',
        'REMAINDER', 'REMOVAL', 'RENAMES', 'REPLACE', 'REPLACING', 'REPORT', 'REPORTING',
        'REPORTS', 'REPOSITORY', 'RERUN', 'RESERVE', 'RESET', 'RETURN', 'RETURNING', 'REVERSED',
        'REWIND', 'REWRITE', 'RF', 'RH', 'RIGHT', 'ROUNDED', 'RUN', 'SAME', 'SD', 'SEARCH',
        'SECTION', 'SECURITY', 'SEGMENT', 'SEGMENT-LIMIT', 'SELECT', 'SELF', 'SEND', 'SENTENCE',
        'SEPARATE', 'SEQUENCE', 'SEQUENTIAL', 'SERVICE', 'SET', 'SHIFT-IN', 'SHIFT-OUT', 'SIGN',
        'SIZE', 'SKIP1', 'SKIP2', 'SKIP3', 'SORT', 'SORT-CONTROL', 'SORT-CORE-SIZE',
        'SORT-FILE-SIZE', 'SORT-MERGE', 'SORT-MESSAGE', 'SORT-MODE-SIZE', 'SORT-RETURN',
        'SOURCE', 'SOURCE-COMPUTER', 'SPACE', 'SPACES', 'SPECIAL-NAMES', 'STANDARD',
        'STANDARD-1', 'STANDARD-2', 'START', 'STATUS', 'STOP', 'STRING', 'SUB-QUEUE-1',
        'SUB-QUEUE-2', 'SUB-QUEUE-3', 'SUBTRACT', 'SUM', 'SUPER', 'SUPPRESS', 'SYMBOLIC',
        'SYNC', 'SYNCHRONIZED', 'TABLE', 'TALLY', 'TALLYING', 'TAPE', 'TERMINAL', 'TERMINATE',
        'TEST', 'TEXT', 'THAN', 'THEN', 'THROUGH', 'THRU', 'TIME', 'TIMES', 'TITLE', 'TO',
        'TOP', 'TRACE', 'TRAILING', 'TRUE', 'TYPE', 'UNIT', 'UNSTRING', 'UNTIL', 'UP', 'UPON',
        'USAGE', 'USE', 'USING', 'VALUE', 'VALUES', 'VARYING', 'WHEN', 'WITH', 'WORDS',
        'WORKING-STORAGE', 'WRITE', 'ZERO', 'ZEROES', 'ZEROS'
    }

    # COBOL divisions
    DIVISIONS = {'IDENTIFICATION', 'ENVIRONMENT', 'DATA', 'PROCEDURE'}

    # Regular expressions for token patterns
    PATTERNS = {
        'comment': re.compile(r'^\*.*$|^/.+/$'),
        'string_literal': re.compile(r'"([^"]*)"'),
        'number': re.compile(r'\d+(\.\d+)?'),
        'identifier': re.compile(r'[A-Za-z0-9][-A-Za-z0-9]*'),
        'whitespace': re.compile(r'\s+'),
        'operator': re.compile(r'[+\-*/=<>]'),
        'punctuation': re.compile(r'[.,;:]'),
        'special': re.compile(r'[(){}[\]]')
    }

    def __init__(self):
        self.current_line = 0
        self.current_column = 0

    def tokenize(self, source_code: str) -> List[Token]:
        """
        Tokenize COBOL source code into a list of tokens

        Args:
            source_code: String containing COBOL source code

        Returns:
            List of Token objects
        """
        tokens = []
        lines = source_code.splitlines()

        for line_num, line in enumerate(lines, 1):
            self.current_line = line_num
            self.current_column = 1

            # Skip line number area (columns 1-6) and handle continuation
            if len(line) > 6:
                # Check for comment indicator in column 7
                if len(line) > 7 and line[6] == '*':
                    tokens.append(Token(
                        TokenType.COMMENT,
                        line[7:].strip(),
                        line_num,
                        7
                    ))
                    continue

                # Process the line from column 7 onwards
                self.current_column = 7
                line_content = line[6:].rstrip()
                line_tokens = self._tokenize_line(line_content)
                tokens.extend(line_tokens)

        return tokens

    def _tokenize_line(self, line: str) -> List[Token]:
        """Tokenize a single line of COBOL code"""
        tokens = []
        position = 0
        line_length = len(line)

        while position < line_length:
            # Skip whitespace
            match = self.PATTERNS['whitespace'].match(line[position:])
            if match:
                whitespace_length = match.end()
                self.current_column += whitespace_length
                position += whitespace_length
                continue

            # Check for comment
            match = self.PATTERNS['comment'].match(line[position:])
            if match:
                tokens.append(Token(
                    TokenType.COMMENT,
                    match.group(0),
                    self.current_line,
                    self.current_column
                ))
                self.current_column += match.end()
                position += match.end()
                continue

            # Check for string literal
            match = self.PATTERNS['string_literal'].match(line[position:])
            if match:
                tokens.append(Token(
                    TokenType.LITERAL,
                    match.group(1),
                    self.current_line,
                    self.current_column
                ))
                self.current_column += match.end()
                position += match.end()
                continue

            # Check for number
            match = self.PATTERNS['number'].match(line[position:])
            if match:
                tokens.append(Token(
                    TokenType.NUMBER,
                    match.group(0),
                    self.current_line,
                    self.current_column
                ))
                self.current_column += match.end()
                position += match.end()
                continue

            # Check for identifier or keyword
            match = self.PATTERNS['identifier'].match(line[position:])
            if match:
                text = match.group(0)
                token_type = TokenType.KEYWORD if text.upper() in self.KEYWORDS else TokenType.IDENTIFIER

                # Check if it's a division
                if text.upper() in self.DIVISIONS:
                    token_type = TokenType.DIVISION

                tokens.append(Token(
                    token_type,
                    text,
                    self.current_line,
                    self.current_column
                ))
                self.current_column += match.end()
                position += match.end()
                continue

            # Check for operator
            match = self.PATTERNS['operator'].match(line[position:])
            if match:
                tokens.append(Token(
                    TokenType.OPERATOR,
                    match.group(0),
                    self.current_line,
                    self.current_column
                ))
                self.current_column += match.end()
                position += match.end()
                continue

            # Check for punctuation
            match = self.PATTERNS['punctuation'].match(line[position:])
            if match:
                tokens.append(Token(
                    TokenType.PUNCTUATION,
                    match.group(0),
                    self.current_line,
                    self.current_column
                ))
                self.current_column += match.end()
                position += match.end()
                continue

            # Check for special characters
            match = self.PATTERNS['special'].match(line[position:])
            if match:
                tokens.append(Token(
                    TokenType.SPECIAL,
                    match.group(0),
                    self.current_line,
                    self.current_column
                ))
                self.current_column += match.end()
                position += match.end()
                continue

            # If no match, skip the character
            tokens.append(Token(
                TokenType.UNKNOWN,
                line[position],
                self.current_line,
                self.current_column
            ))
            self.current_column += 1
            position += 1

        return tokens


class CobolParser:
    """Parser for COBOL programs that builds a structured representation"""

    def __init__(self):
        self.tokenizer = CobolTokenizer()
        self.tokens = []
        self.current_index = 0
        self.program = None
        self.source_path = ""
        self.source_code = ""

    def parse(self, source_path: str) -> CobolProgram:
        """
        Parse a COBOL source file and return a structured representation

        Args:
            source_path: Path to the COBOL source file

        Returns:
            CobolProgram object containing the parsed program structure
        """
        self.source_path = source_path

        # Read the source file
        try:
            with open(source_path, 'r', encoding='utf-8', errors='replace') as f:
                self.source_code = f.read()
        except Exception as e:
            logger.error(f"Error reading file {source_path}: {e}")
            raise

        # Extract program name from path
        program_name = os.path.splitext(os.path.basename(source_path))[0]

        # Create program object
        self.program = CobolProgram(name=program_name, source_path=source_path)

        # Tokenize the source code
        self.tokens = self.tokenizer.tokenize(self.source_code)
        self.current_index = 0

        # Parse the program structure
        self._parse_program()

        return self.program

    def _parse_program(self):
        """Parse the overall program structure"""
        # Extract divisions
        self._parse_divisions()

        # Extract file references
        self._extract_file_references()

        # Extract program calls
        self._extract_program_calls()

        # Extract resources used
        self._extract_resources()

        # Extract copybooks
        self._extract_copybooks()

        # Extract BMS maps
        self._extract_maps()

    def _parse_divisions(self):
        """Parse the main divisions of the COBOL program"""
        current_division = None
        current_section = None
        current_paragraph = None

        division_start_line = 0
        section_start_line = 0
        paragraph_start_line = 0

        i = 0
        while i < len(self.tokens):
            token = self.tokens[i]

            # Look for divisions
            if token.type == TokenType.DIVISION:
                if current_division:
                    # End the previous division
                    if current_section:
                        if current_paragraph:
                            # End the current paragraph
                            current_paragraph.end_line = token.line - 1
                            current_section.paragraphs[current_paragraph.name] = current_paragraph
                            current_paragraph = None

                        # End the current section
                        current_section.end_line = token.line - 1
                        current_division.sections[current_section.name] = current_section
                        current_section = None

                    # End the division
                    current_division.end_line = token.line - 1
                    self.program.divisions[current_division.name] = current_division

                # Start a new division
                division_name = token.value.upper()
                division_start_line = token.line
                current_division = Division(name=division_name, start_line=division_start_line, end_line=0)
                current_section = None
                current_paragraph = None

            # Look for sections
            elif token.type == TokenType.SECTION:
                if i > 0 and self.tokens[i - 1].type == TokenType.IDENTIFIER:
                    section_name = self.tokens[i - 1].value.upper()

                    if current_division:
                        if current_section:
                            if current_paragraph:
                                # End the current paragraph
                                current_paragraph.end_line = token.line - 1
                                current_section.paragraphs[current_paragraph.name] = current_paragraph
                                current_paragraph = None

                            # End the current section
                            current_section.end_line = token.line - 1
                            current_division.sections[current_section.name] = current_section

                        # Start a new section
                        section_start_line = token.line
                        current_section = Section(name=section_name, start_line=section_start_line, end_line=0)
                        current_paragraph = None

            # Look for paragraphs (identifiers at the start of a line in the PROCEDURE DIVISION)
            elif (token.type == TokenType.IDENTIFIER and
                  current_division and
                  current_division.name == "PROCEDURE" and
                  (i == 0 or self.tokens[i - 1].line != token.line) and
                  (i + 1 < len(self.tokens) and self.tokens[i + 1].value != 'SECTION')):

                paragraph_name = token.value.upper()

                if current_section:
                    if current_paragraph:
                        # End the current paragraph
                        current_paragraph.end_line = token.line - 1
                        current_section.paragraphs[current_paragraph.name] = current_paragraph

                    # Start a new paragraph
                    paragraph_start_line = token.line
                    current_paragraph = Paragraph(name=paragraph_name, start_line=paragraph_start_line, end_line=0)

            # Process data items if in the DATA DIVISION
            elif (current_division and current_division.name == "DATA" and
                  token.type == TokenType.NUMBER and
                  i + 1 < len(self.tokens) and
                  self.tokens[i + 1].type == TokenType.IDENTIFIER):

                try:
                    level = int(token.value)
                    name = self.tokens[i + 1].value.upper()

                    data_item = DataItem(
                        name=name,
                        level=level,
                        location=(token.line, token.column)
                    )

                    # Look ahead for PICTURE/PIC clause
                    j = i + 2
                    while j < len(self.tokens) and self.tokens[j].line == token.line:
                        if self.tokens[j].value.upper() in ['PIC', 'PICTURE'] and j + 1 < len(self.tokens):
                            data_item.picture = self.tokens[j + 1].value
                            j += 2
                        elif self.tokens[j].value.upper() == 'USAGE' and j + 1 < len(self.tokens):
                            data_item.usage = self.tokens[j + 1].value
                            j += 2
                        elif self.tokens[j].value.upper() == 'VALUE' and j + 1 < len(self.tokens):
                            data_item.value = self.tokens[j + 1].value
                            j += 2
                        elif self.tokens[j].value.upper() == 'REDEFINES' and j + 1 < len(self.tokens):
                            data_item.redefines = self.tokens[j + 1].value
                            j += 2
                        elif self.tokens[j].value.upper() == 'OCCURS' and j + 1 < len(self.tokens):
                            try:
                                data_item.occurs = int(self.tokens[j + 1].value)
                            except ValueError:
                                data_item.occurs = 0
                            j += 2
                        else:
                            j += 1

                    self.program.data_items[name] = data_item

                except ValueError:
                    pass

            i += 1

        # Close any open structures
        if current_division:
            if current_section:
                if current_paragraph:
                    # End the current paragraph
                    current_paragraph.end_line = self.tokens[-1].line if self.tokens else 0
                    current_section.paragraphs[current_paragraph.name] = current_paragraph

                # End the current section
                current_section.end_line = self.tokens[-1].line if self.tokens else 0
                current_division.sections[current_section.name] = current_section

            # End the division
            current_division.end_line = self.tokens[-1].line if self.tokens else 0
            self.program.divisions[current_division.name] = current_division

    def _extract_file_references(self):
        """Extract file references from the program"""
        # Look for SELECT statements in the ENVIRONMENT DIVISION
        i = 0
        while i < len(self.tokens):
            if (self.tokens[i].type == TokenType.KEYWORD and
                    self.tokens[i].value.upper() == 'SELECT' and
                    i + 1 < len(self.tokens) and
                    self.tokens[i + 1].type == TokenType.IDENTIFIER):

                file_name = self.tokens[i + 1].value.upper()
                access_mode = "SEQUENTIAL"  # Default
                organization = None
                record_key = None
                location = (self.tokens[i].line, self.tokens[i].column)

                # Look ahead for ORGANIZATION, ACCESS MODE, etc.
                j = i + 2
                while j < len(self.tokens) and self.tokens[j].value.upper() != 'SELECT':
                    if (self.tokens[j].value.upper() == 'ORGANIZATION' and
                            j + 1 < len(self.tokens)):
                        organization = self.tokens[j + 1].value.upper()

                    elif (self.tokens[j].value.upper() == 'ACCESS' and
                          j + 1 < len(self.tokens) and
                          self.tokens[j + 1].value.upper() == 'MODE' and
                          j + 2 < len(self.tokens)):
                        access_mode = self.tokens[j + 2].value.upper()

                    elif (self.tokens[j].value.upper() == 'RECORD' and
                          j + 1 < len(self.tokens) and
                          self.tokens[j + 1].value.upper() == 'KEY' and
                          j + 2 < len(self.tokens)):
                        record_key = self.tokens[j + 2].value.upper()

                    j += 1
                    if j >= len(self.tokens) or self.tokens[j].value.upper() == '.':
                        break

                file_ref = FileReference(
                    name=file_name,
                    access_mode=access_mode,
                    organization=organization,
                    record_key=record_key,
                    location=location
                )

                self.program.files.append(file_ref)

            i += 1

        # Also look for file operations in the PROCEDURE DIVISION
        i = 0
        while i < len(self.tokens):
            if self.tokens[i].type == TokenType.KEYWORD and self.tokens[i].value.upper() in ['OPEN', 'CLOSE', 'READ', 'WRITE',
                                                                                             'REWRITE', 'DELETE', 'START']:
                operation = self.tokens[i].value.upper()

                # Look ahead for file names
                j = i + 1
                while j < len(self.tokens) and self.tokens[j].line == self.tokens[i].line:
                    if self.tokens[j].type == TokenType.IDENTIFIER:
                        # Check if this identifier is already in our files list
                        file_name = self.tokens[j].value.upper()
                        file_exists = False

                        for file_ref in self.program.files:
                            if file_ref.name == file_name:
                                file_exists = True
                                break

                        if not file_exists:
                            # This might be a file that wasn't properly declared in SELECT
                            file_ref = FileReference(
                                name=file_name,
                                access_mode="UNKNOWN",
                                location=(self.tokens[i].line, self.tokens[i].column)
                            )
                            self.program.files.append(file_ref)

                    j += 1

            i += 1


    def _extract_program_calls(self):
        """Extract calls to other programs"""
        i = 0
        while i < len(self.tokens):
            if self.tokens[i].type == TokenType.KEYWORD and self.tokens[i].value.upper() == 'CALL':
                is_dynamic = False
                target = None
                parameters = []
                location = (self.tokens[i].line, self.tokens[i].column)

                # Check if the next token is a literal (static call) or identifier (potentially dynamic)
                if i + 1 < len(self.tokens):
                    if self.tokens[i + 1].type == TokenType.LITERAL:
                        target = self.tokens[i + 1].value
                    elif self.tokens[i + 1].type == TokenType.IDENTIFIER:
                        target = self.tokens[i + 1].value.upper()
                        is_dynamic = True

                # Look for USING clause to extract parameters
                j = i + 2
                using_found = False

                while j < len(self.tokens) and self.tokens[j].line == self.tokens[i].line:
                    if self.tokens[j].type == TokenType.KEYWORD and self.tokens[j].value.upper() == 'USING':
                        using_found = True
                        j += 1
                        continue

                    if using_found and self.tokens[j].type == TokenType.IDENTIFIER:
                        parameters.append(self.tokens[j].value.upper())

                    j += 1

                if target:
                    call = ProgramCall(
                        target=target,
                        is_dynamic=is_dynamic,
                        parameters=parameters,
                        location=location
                    )
                    self.program.calls.append(call)

            i += 1


    def _extract_resources(self):
        """Extract system resources used by the program (DB2, CICS, MQ, etc.)"""
        # Look for EXEC statements
        i = 0
        while i < len(self.tokens):
            if (self.tokens[i].type == TokenType.KEYWORD and
                    self.tokens[i].value.upper() == 'EXEC' and
                    i + 1 < len(self.tokens)):

                resource_type = self.tokens[i + 1].value.upper()
                operation = None
                resource_name = None
                location = (self.tokens[i].line, self.tokens[i].column)

                # DB2 operations
                if resource_type == 'SQL':
                    j = i + 2
                    while j < len(self.tokens) and self.tokens[j].value.upper() != 'END-EXEC':
                        if self.tokens[j].type == TokenType.KEYWORD:
                            if operation is None:  # First keyword is usually the operation
                                operation = self.tokens[j].value.upper()

                            # Look for table names after FROM, INTO, UPDATE, etc.
                            if self.tokens[j].value.upper() in ['FROM', 'INTO', 'UPDATE', 'TABLE'] and j + 1 < len(
                                    self.tokens):
                                resource_name = self.tokens[j + 1].value.upper()

                        j += 1

                # CICS operations
                elif resource_type == 'CICS':
                    j = i + 2
                    while j < len(self.tokens) and self.tokens[j].value.upper() != 'END-EXEC':
                        if self.tokens[j].type == TokenType.KEYWORD:
                            if operation is None:  # First keyword is usually the operation
                                operation = self.tokens[j].value.upper()

                            # Look for resource names in various CICS commands
                            if self.tokens[j].value.upper() in ['PROGRAM', 'TRANSID', 'QUEUE', 'FILE'] and j + 1 < len(
                                    self.tokens):
                                resource_name = self.tokens[j + 1].value.upper()

                        j += 1

                # MQ operations
                elif resource_type == 'MQ':
                    j = i + 2
                    while j < len(self.tokens) and self.tokens[j].value.upper() != 'END-EXEC':
                        if self.tokens[j].type == TokenType.KEYWORD:
                            if operation is None:  # First keyword is usually the operation
                                operation = self.tokens[j].value.upper()

                            # Look for queue names
                            if self.tokens[j].value.upper() in ['QNAME', 'QUEUE'] and j + 1 < len(self.tokens):
                                resource_name = self.tokens[j + 1].value.upper()

                        j += 1

                if resource_type and operation:
                    resource = Resource(
                        name=resource_name if resource_name else "UNKNOWN",
                        type=resource_type,
                        operation=operation,
                        location=location
                    )
                    self.program.resources.append(resource)

                # Skip to after END-EXEC
                while i < len(self.tokens) and self.tokens[i].value.upper() != 'END-EXEC':
                    i += 1

            i += 1


    def _extract_copybooks(self):
        """Extract copybook references"""
        i = 0
        while i < len(self.tokens):
            if self.tokens[i].type == TokenType.KEYWORD and self.tokens[i].value.upper() == 'COPY':
                if i + 1 < len(self.tokens) and self.tokens[i + 1].type in [TokenType.IDENTIFIER, TokenType.LITERAL]:
                    copybook_name = self.tokens[i + 1].value.upper()
                    self.program.copybooks.add(copybook_name)

            i += 1


    def _extract_maps(self):
        """Extract BMS map references"""
        i = 0
        while i < len(self.tokens):
            # Look for SEND MAP, RECEIVE MAP in CICS programs
            if (self.tokens[i].type == TokenType.KEYWORD and
                    self.tokens[i].value.upper() in ['SEND', 'RECEIVE'] and
                    i + 1 < len(self.tokens) and
                    self.tokens[i + 1].type == TokenType.KEYWORD and
                    self.tokens[i + 1].value.upper() == 'MAP' and
                    i + 2 < len(self.tokens)):

                map_name = self.tokens[i + 2].value.upper()
                self.program.maps_used.add(map_name)

            # Also look for EXEC CICS SEND MAP
            elif (self.tokens[i].type == TokenType.KEYWORD and
                  self.tokens[i].value.upper() == 'EXEC' and
                  i + 1 < len(self.tokens) and
                  self.tokens[i + 1].value.upper() == 'CICS'):

                j = i + 2
                map_found = False
                while j < len(self.tokens) and self.tokens[j].value.upper() != 'END-EXEC':
                    if (self.tokens[j].value.upper() in ['SEND', 'RECEIVE'] and
                            j + 1 < len(self.tokens) and
                            self.tokens[j + 1].value.upper() == 'MAP' and
                            j + 2 < len(self.tokens)):
                        map_name = self.tokens[j + 2].value.upper()
                        self.program.maps_used.add(map_name)
                        map_found = True

                    j += 1

                # If we found a map, skip to after END-EXEC
                if map_found:
                    while i < len(self.tokens) and self.tokens[i].value.upper() != 'END-EXEC':
                        i += 1

            i += 1


class CobolAnalyzer:
    """
    Main analyzer class that orchestrates the parsing and analysis of COBOL programs
    """

    def __init__(self, copybook_paths=None):
        """
        Initialize the analyzer with optional paths to copybook directories

        Args:
            copybook_paths: List of directory paths to search for copybooks
        """
        self.parser = CobolParser()
        self.copybook_paths = copybook_paths or []
        self.analyzed_programs = {}
        self.call_graph = {}
        self.resource_usage = {}

    def analyze_program(self, program_path: str) -> CobolProgram:
        """
        Analyze a single COBOL program

        Args:
            program_path: Path to the COBOL program file

        Returns:
            CobolProgram object containing the analyzed program structure
        """
        logger.info(f"Analyzing program: {program_path}")

        program = self.parser.parse(program_path)
        self.analyzed_programs[program.name] = program

        # Update call graph
        self.call_graph[program.name] = set()
        for call in program.calls:
            self.call_graph[program.name].add(call.target)

            # Mark this program as a caller of the target program
            if call.target not in self.call_graph:
                self.call_graph[call.target] = set()

        # Update resource usage
        for resource in program.resources:
            resource_key = f"{resource.type}:{resource.name}"
            if resource_key not in self.resource_usage:
                self.resource_usage[resource_key] = set()
            self.resource_usage[resource_key].add(program.name)

        return program

    def analyze_directory(self, directory_path: str) -> Dict[str, CobolProgram]:
        """
        Analyze all COBOL programs in a directory

        Args:
            directory_path: Path to the directory containing COBOL programs

        Returns:
            Dictionary mapping program names to CobolProgram objects
        """
        logger.info(f"Analyzing directory: {directory_path}")

        # Find all COBOL files in the directory
        cobol_files = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(('.cbl', '.cob', '.cobol')):
                    cobol_files.append(os.path.join(root, file))

        # Analyze each file
        for file_path in cobol_files:
            self.analyze_program(file_path)

        return self.analyzed_programs

    def find_caller_programs(self, program_name: str) -> Set[str]:
        """
        Find all programs that call the specified program

        Args:
            program_name: Name of the program to find callers for

        Returns:
            Set of program names that call the specified program
        """
        callers = set()

        for caller, callees in self.call_graph.items():
            if program_name in callees:
                callers.add(caller)

        return callers

    def find_called_programs(self, program_name: str) -> Set[str]:
        """
        Find all programs called by the specified program

        Args:
            program_name: Name of the program to find callees for

        Returns:
            Set of program names called by the specified program
        """
        if program_name in self.call_graph:
            return self.call_graph[program_name]
        return set()

    def generate_call_graph(self, output_path: str = None) -> str:
        """
        Generate a call graph visualization using Mermaid syntax

        Args:
            output_path: Optional path to save the visualization

        Returns:
            String containing the Mermaid diagram code
        """
        mermaid_code = "graph TD\n"

        # Add nodes and edges
        for caller, callees in self.call_graph.items():
            for callee in callees:
                mermaid_code += f"    {caller}[{caller}] --> {callee}[{callee}]\n"

        # Save to file if requested
        if output_path:
            with open(output_path, 'w') as f:
                f.write(mermaid_code)

        return mermaid_code

    def generate_resource_usage_report(self, output_path: str = None) -> str:
        """
        Generate a report of resource usage across all analyzed programs

        Args:
            output_path: Optional path to save the report

        Returns:
            String containing the report
        """
        report = "# Resource Usage Report\n\n"

        # Group resources by type
        resources_by_type = {}
        for resource_key, programs in self.resource_usage.items():
            resource_type, resource_name = resource_key.split(':', 1)

            if resource_type not in resources_by_type:
                resources_by_type[resource_type] = {}

            resources_by_type[resource_type][resource_name] = programs

        # Generate report
        for resource_type, resources in resources_by_type.items():
            report += f"## {resource_type} Resources\n\n"

            for resource_name, programs in resources.items():
                report += f"### {resource_name}\n\n"
                report += "Used by the following programs:\n\n"

                for program in programs:
                    report += f"- {program}\n"

                report += "\n"

        # Save to file if requested
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report)

        return report

    def generate_program_summary(self, program_name: str, output_path: str = None) -> str:
        """
        Generate a summary report for a specific program

        Args:
            program_name: Name of the program to summarize
            output_path: Optional path to save the report

        Returns:
            String containing the summary report
        """
        if program_name not in self.analyzed_programs:
            return f"Program {program_name} not found in analyzed programs."

        program = self.analyzed_programs[program_name]

        # Generate report
        report = f"# Program Summary: {program_name}\n\n"

        # Basic information
        report += "## Basic Information\n\n"
        report += f"- Source File: {program.source_path}\n"
        report += f"- Copybooks Used: {', '.join(program.copybooks) if program.copybooks else 'None'}\n"
        report += f"- Maps Used: {', '.join(program.maps_used) if program.maps_used else 'None'}\n\n"

        # Call hierarchy
        report += "## Call Hierarchy\n\n"
        report += "### Called By\n\n"
        callers = self.find_caller_programs(program_name)
        if callers:
            for caller in callers:
                report += f"- {caller}\n"
        else:
            report += "- No calling programs found\n"

        report += "\n### Calls\n\n"
        if program.calls:
            for call in program.calls:
                report += f"- {call.target} {'(Dynamic)' if call.is_dynamic else ''}\n"
                if call.parameters:
                    report += f"  - Parameters: {', '.join(call.parameters)}\n"
        else:
            report += "- No called programs found\n"

        # File usage
        if program.files:
            report += "\n## File Usage\n\n"
            for file_ref in program.files:
                report += f"- {file_ref.name}\n"
                report += f"  - Access Mode: {file_ref.access_mode}\n"
                if file_ref.organization:
                    report += f"  - Organization: {file_ref.organization}\n"
                if file_ref.record_key:
                    report += f"  - Record Key: {file_ref.record_key}\n"

        # Resources
        if program.resources:
            report += "\n## Resource Usage\n\n"

            # Group resources by type
            resources_by_type = {}
            for resource in program.resources:
                if resource.type not in resources_by_type:
                    resources_by_type[resource.type] = []
                resources_by_type[resource.type].append(resource)

            for resource_type, resources in resources_by_type.items():
                report += f"### {resource_type}\n\n"
                for resource in resources:
                    report += f"- {resource.operation} {resource.name}\n"
                report += "\n"

        # Data items
        if program.data_items:
            report += "\n## Key Data Items\n\n"

            # Filter just the main data structures (level 01)
            main_items = [item for item in program.data_items.values() if item.level == 1]
            for item in main_items:
                report += f"- {item.name}\n"
                if item.picture:
                    report += f"  - Picture: {item.picture}\n"
                if item.usage:
                    report += f"  - Usage: {item.usage}\n"

            report += "\n"

        # Save to file if requested
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report)

        return report

    def prepare_for_llm(self, program_name: str) -> Dict[str, Any]:
        """
        Prepare a structured representation of a program for LLM analysis

        Args:
            program_name: Name of the program to prepare

        Returns:
            Dictionary containing structured data about the program
        """
        if program_name not in self.analyzed_programs:
            return {"error": f"Program {program_name} not found in analyzed programs."}

        program = self.analyzed_programs[program_name]

        # Create a dictionary with all relevant program information
        llm_data = {
            "program_name": program.name,
            "source_path": program.source_path,
            "copybooks": list(program.copybooks),
            "maps_used": list(program.maps_used),
            "called_by": list(self.find_caller_programs(program_name)),
            "calls": [
                {
                    "target": call.target,
                    "is_dynamic": call.is_dynamic,
                    "parameters": call.parameters
                }
                for call in program.calls
            ],
            "files": [
                {
                    "name": file_ref.name,
                    "access_mode": file_ref.access_mode,
                    "organization": file_ref.organization,
                    "record_key": file_ref.record_key
                }
                for file_ref in program.files
            ],
            "resources": [
                {
                    "name": resource.name,
                    "type": resource.type,
                    "operation": resource.operation
                }
                for resource in program.resources
            ],
            "data_items": {
                name: {
                    "level": item.level,
                    "picture": item.picture,
                    "usage": item.usage,
                    "value": item.value,
                    "redefines": item.redefines,
                    "occurs": item.occurs,
                    "indexed_by": item.indexed_by
                }
                for name, item in program.data_items.items()
            },
            "divisions": {
                name: {
                    "start_line": div.start_line,
                    "end_line": div.end_line,
                    "sections": {
                        sec_name: {
                            "start_line": sec.start_line,
                            "end_line": sec.end_line,
                            "paragraphs": {
                                para_name: {
                                    "start_line": para.start_line,
                                    "end_line": para.end_line
                                }
                                for para_name, para in sec.paragraphs.items()
                            }
                        }
                        for sec_name, sec in div.sections.items()
                    }
                }
                for name, div in program.divisions.items()
            }
        }

        return llm_data


class CobolLogicExtractor:
    """
    Extract business logic from COBOL programs in a format suitable for LLM processing
    """

    def __init__(self, analyzer: CobolAnalyzer):
        """
        Initialize the logic extractor

        Args:
            analyzer: Initialized CobolAnalyzer instance
        """
        self.analyzer = analyzer

    def extract_logic(self, program_name: str) -> str:
        """
        Extract business logic from a COBOL program

        Args:
            program_name: Name of the program to extract logic from

        Returns:
            String containing description of the program's business logic
        """
        if program_name not in self.analyzer.analyzed_programs:
            return f"Program {program_name} not found in analyzed programs."

        program = self.analyzer.analyzed_programs[program_name]

        # Read the source code
        with open(program.source_path, 'r', encoding='utf-8', errors='replace') as f:
            source_lines = f.readlines()

        # Extract procedure division
        proc_div = program.divisions.get('PROCEDURE')
        if not proc_div:
            return "No PROCEDURE DIVISION found in the program."

        # Build logic description
        logic = f"# Business Logic for {program_name}\n\n"

        # Describe main program flow
        logic += "## Main Program Flow\n\n"

        # If there are explicit sections in the procedure division, describe them
        if proc_div.sections:
            for section_name, section in proc_div.sections.items():
                logic += f"### Section: {section_name}\n\n"

                for para_name, para in section.paragraphs.items():
                    logic += f"#### Paragraph: {para_name}\n\n"

                    # Extract paragraph content
                    paragraph_lines = source_lines[para.start_line - 1:para.end_line]
                    paragraph_text = ''.join([line[6:] if len(line) > 6 else line for line in paragraph_lines])

                    logic += "```cobol\n"
                    logic += paragraph_text
                    logic += "```\n\n"

                    # Add description of what this paragraph does
                    logic += "This paragraph:\n"

                    # Check for common patterns in COBOL code
                    if any("IF " in line for line in paragraph_lines):
                        logic += "- Contains conditional logic\n"
                    if any("PERFORM " in line for line in paragraph_lines):
                        logic += "- Calls other paragraphs\n"
                    if any("MOVE " in line for line in paragraph_lines):
                        logic += "- Manipulates data\n"
                    if any("COMPUTE " in line for line in paragraph_lines):
                        logic += "- Performs calculations\n"
                    if any(("READ " in line or "WRITE " in line or "REWRITE " in line) for line in paragraph_lines):
                        logic += "- Performs file I/O operations\n"
                    if any("CALL " in line for line in paragraph_lines):
                        logic += "- Calls external programs\n"
                    if any("EXEC " in line for line in paragraph_lines):
                        logic += "- Interfaces with external systems\n"

                    logic += "\n"
        else:
            # If no sections, just describe the paragraphs directly
            for section_name, section in proc_div.sections.items():
                for para_name, para in section.paragraphs.items():
                    logic += f"### Paragraph: {para_name}\n\n"

                    # Extract paragraph content
                    paragraph_lines = source_lines[para.start_line - 1:para.end_line]
                    paragraph_text = ''.join([line[6:] if len(line) > 6 else line for line in paragraph_lines])

                    logic += "```cobol\n"
                    logic += paragraph_text
                    logic += "```\n\n"

        # Add information about key data structures
        logic += "## Key Data Structures\n\n"

        # Find main data items (level 01)
        main_items = [item for item in program.data_items.values() if item.level == 1]
        for item in main_items:
            logic += f"### {item.name}\n\n"
            if item.picture:
                logic += f"- Picture: {item.picture}\n"
            if item.usage:
                logic += f"- Usage: {item.usage}\n"

            # Find child items
            children = [child for child in program.data_items.values()
                        if child.level > 1 and child.name.startswith(item.name)]

            if children:
                logic += "- Child fields:\n"
                for child in children:
                    logic += f"  - {child.name} (Level {child.level})"
                    if child.picture:
                        logic += f", Picture: {child.picture}"
                    logic += "\n"

            logic += "\n"

        # Add information about external interfaces
        logic += "## External Interfaces\n\n"

        # Files
        if program.files:
            logic += "### Files\n\n"
            for file_ref in program.files:
                logic += f"- {file_ref.name}: {file_ref.access_mode} access"
                if file_ref.organization:
                    logic += f", {file_ref.organization} organization"
                logic += "\n"
            logic += "\n"

        # Calls to other programs
        if program.calls:
            logic += "### Program Calls\n\n"
            for call in program.calls:
                logic += f"- {call.target} {'(Dynamic)' if call.is_dynamic else '(Static)'}"
                if call.parameters:
                    logic += f", Parameters: {', '.join(call.parameters)}"
                logic += "\n"
            logic += "\n"

        # System interfaces
        if program.resources:
            logic += "### System Interfaces\n\n"

            # Group by type
            resources_by_type = {}
            for resource in program.resources:
                if resource.type not in resources_by_type:
                    resources_by_type[resource.type] = []
                resources_by_type[resource.type].append(resource)

            for resource_type, resources in resources_by_type.items():
                logic += f"#### {resource_type}\n\n"
                for resource in resources:
                    logic += f"- {resource.operation} {resource.name}\n"
                logic += "\n"

        return logic

    def extract_logic_for_llm(self, program_name: str) -> Dict[str, Any]:
        """
        Extract business logic in a structured format for LLM processing

        Args:
            program_name: Name of the program to extract logic from

        Returns:
            Dictionary containing structured data about the program's logic
        """
        if program_name not in self.analyzer.analyzed_programs:
            return {"error": f"Program {program_name} not found in analyzed programs."}

        program = self.analyzer.analyzed_programs[program_name]

        # Read the source code
        with open(program.source_path, 'r', encoding='utf-8', errors='replace') as f:
            source_lines = f.readlines()

        # Prepare basic program info
        logic_data = {
            "program_name": program.name,
            "source_path": program.source_path,
            "description": f"Analysis of {program.name} program logic",
            "paragraphs": [],
            "data_structures": [],
            "external_interfaces": {
                "files": [],
                "program_calls": [],
                "system_interfaces": []
            }
        }

        # Extract procedure division content
        proc_div = program.divisions.get('PROCEDURE')
        if proc_div:
            # Process paragraphs
            for section_name, section in proc_div.sections.items():
                for para_name, para in section.paragraphs.items():
                    # Extract paragraph content
                    paragraph_lines = source_lines[para.start_line - 1:para.end_line]
                    paragraph_text = ''.join([line[6:] if len(line) > 6 else line for line in paragraph_lines])

                    # Analyze paragraph content
                    contains_conditions = any("IF " in line for line in paragraph_lines)
                    contains_performs = any("PERFORM " in line for line in paragraph_lines)
                    contains_moves = any("MOVE " in line for line in paragraph_lines)
                    contains_computations = any("COMPUTE " in line for line in paragraph_lines)
                    contains_io = any(
                        ("READ " in line or "WRITE " in line or "REWRITE " in line) for line in paragraph_lines)
                    contains_calls = any("CALL " in line for line in paragraph_lines)
                    contains_execs = any("EXEC " in line for line in paragraph_lines)

                    # Add paragraph data
                    paragraph_data = {
                        "name": para_name,
                        "section": section_name,
                        "start_line": para.start_line,
                        "end_line": para.end_line,
                        "source_code": paragraph_text,
                        "analysis": {
                            "contains_conditions": contains_conditions,
                            "contains_performs": contains_performs,
                            "contains_moves": contains_moves,
                            "contains_computations": contains_computations,
                            "contains_io": contains_io,
                            "contains_calls": contains_calls,
                            "contains_execs": contains_execs
                        }
                    }

                    logic_data["paragraphs"].append(paragraph_data)

        # Process data structures
        main_items = [item for item in program.data_items.values() if item.level == 1]
        for item in main_items:
            # Find child items
            children = [child for child in program.data_items.values()
                        if child.level > 1 and child.name.startswith(item.name)]

            # Add data structure info
            data_structure = {
                "name": item.name,
                "level": item.level,
                "picture": item.picture,
                "usage": item.usage,
                "children": [
                    {
                        "name": child.name,
                        "level": child.level,
                        "picture": child.picture,
                        "usage": child.usage
                    }
                    for child in children
                ]
            }

            logic_data["data_structures"].append(data_structure)

        # Process external interfaces

        # Files
        for file_ref in program.files:
            file_data = {
                "name": file_ref.name,
                "access_mode": file_ref.access_mode,
                "organization": file_ref.organization,
                "record_key": file_ref.record_key
            }
            logic_data["external_interfaces"]["files"].append(file_data)

        # Program calls
        for call in program.calls:
            call_data = {
                "target": call.target,
                "is_dynamic": call.is_dynamic,
                "parameters": call.parameters
            }
            logic_data["external_interfaces"]["program_calls"].append(call_data)

        # System interfaces
        for resource in program.resources:
            resource_data = {
                "name": resource.name,
                "type": resource.type,
                "operation": resource.operation
            }
            logic_data["external_interfaces"]["system_interfaces"].append(resource_data)

        return logic_data


class CobolLLMIntegration:
    """
    Integrate COBOL analysis results with an LLM for advanced code understanding
    """

    def __init__(self, api_key=None, api_url=None, model_name=None):
        """
        Initialize the LLM integration

        Args:
            api_key: API key for the LLM service
            api_url: URL endpoint for the LLM service
            model_name: Name of the model to use
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model_name = model_name
        self.has_llm = api_key is not None and api_url is not None

    def analyze_with_llm(self, logic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send program logic data to LLM for analysis

        Args:
            logic_data: Structured data about the program's logic

        Returns:
            Dictionary containing the LLM's analysis results
        """
        if not self.has_llm:
            return {
                "error": "LLM integration not configured. Please provide API key and URL."
            }

        try:
            # Prepare prompt for LLM
            prompt = self._build_prompt(logic_data)

            # Make API call to LLM service (implementation would depend on the specific LLM API)
            response = self._call_llm_api(prompt)

            # Process and structure the LLM response
            analysis_results = self._process_llm_response(response, logic_data)

            return analysis_results

        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return {
                "error": f"LLM analysis failed: {str(e)}"
            }

    def _build_prompt(self, logic_data: Dict[str, Any]) -> str:
        """
        Build a prompt for the LLM based on the program's logic data

        Args:
            logic_data: Structured data about the program's logic

        Returns:
            String containing the prompt for the LLM
        """
        program_name = logic_data["program_name"]

        prompt = f"""Analyze the following COBOL program: {program_name}

## Program Structure

The program has {len(logic_data['paragraphs'])} paragraphs across multiple sections.

## Key Data Structures

The program has {len(logic_data['data_structures'])} main data structures:
"""

        # Add data structures
        for ds in logic_data['data_structures'][:5]:  # Limit to 5 for brevity
            prompt += f"- {ds['name']}"
            if ds['picture']:
                prompt += f" (PIC {ds['picture']})"
            prompt += "\n"

        if len(logic_data['data_structures']) > 5:
            prompt += f"- ... and {len(logic_data['data_structures']) - 5} more data structures\n"

        # Add external interfaces
        prompt += "\n## External Interfaces\n"

        # Files
        files = logic_data['external_interfaces']['files']
        if files:
            prompt += f"\nThe program uses {len(files)} files:\n"
            for file in files[:3]:  # Limit to 3 for brevity
                prompt += f"- {file['name']} ({file['access_mode']})\n"
            if len(files) > 3:
                prompt += f"- ... and {len(files) - 3} more files\n"

        # Program calls
        calls = logic_data['external_interfaces']['program_calls']
        if calls:
            prompt += f"\nThe program calls {len(calls)} other programs:\n"
            for call in calls[:3]:  # Limit to 3 for brevity
                prompt += f"- {call['target']} {'(Dynamic)' if call['is_dynamic'] else '(Static)'}\n"
            if len(calls) > 3:
                prompt += f"- ... and {len(calls) - 3} more program calls\n"

        # System interfaces
        sys_interfaces = logic_data['external_interfaces']['system_interfaces']
        if sys_interfaces:
            prompt += f"\nThe program interacts with {len(sys_interfaces)} system interfaces:\n"
            for intf in sys_interfaces[:3]:  # Limit to 3 for brevity
                prompt += f"- {intf['type']}: {intf['operation']} {intf['name']}\n"
            if len(sys_interfaces) > 3:
                prompt += f"- ... and {len(sys_interfaces) - 3} more system interfaces\n"

        # Add key paragraphs
        prompt += "\n## Key paragraphs code:\n\n"

        # Find 3 important paragraphs (those with calls, I/O, or execs)
        important_paras = [p for p in logic_data['paragraphs']
                           if p['analysis']['contains_calls'] or
                           p['analysis']['contains_io'] or
                           p['analysis']['contains_execs']]

        # If not enough important paragraphs, take the first few
        if len(important_paras) < 3:
            important_paras = logic_data['paragraphs'][:3]

        for para in important_paras[:3]:
            prompt += f"### {para['name']}\n"
            prompt += "```cobol\n"
            prompt += para['source_code']
            prompt += "\n```\n\n"

        # Add analysis instructions
        prompt += """
Based on the provided information, please analyze this COBOL program and provide:

1. A summary of the program's main purpose
2. The key business logic implemented in the program
3. The main data flow through the program
4. Any potential issues or areas for improvement
5. A modernization strategy if this code needed to be migrated to a more modern platform

Please be specific and refer to actual program elements in your analysis.
"""

        return prompt

    def _call_llm_api(self, prompt: str) -> str:
        """
        Make API call to LLM service

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            String containing the LLM's response
        """
        # This is a placeholder implementation - you would need to implement this
        # based on the specific LLM API you are using (OpenAI, Azure, etc.)

        # For example, with a generic API:
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model_name,
                "prompt": prompt,
                "max_tokens": 1500,
                "temperature": 0.7
            }

            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()

            return response.json().get("choices", [{}])[0].get("text", "")

        except ImportError:
            return "Error: requests module not available. Please install it using 'pip install requests'."
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            return f"Error calling LLM API: {str(e)}"

    def _process_llm_response(self, response: str, logic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and structure the LLM response

        Args:
            response: String containing the LLM's response
            logic_data: Original logic data sent to the LLM

        Returns:
            Dictionary containing the structured analysis results
        """
        # This is a simple implementation - you may want to enhance this with more
        # sophisticated parsing based on your LLM's response format

        analysis_results = {
            "program_name": logic_data["program_name"],
            "analysis_timestamp": import_time().isoformat(),
            "raw_llm_response": response,
            "structured_analysis": {}
        }

        # Try to extract sections from the response
        sections = {
            "purpose": "",
            "business_logic": "",
            "data_flow": "",
            "issues": "",
            "modernization": ""
        }

        current_section = None
        lines = response.split("\n")

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if "purpose" in line.lower() and line.startswith(("1", "#", "##")):
                current_section = "purpose"
                continue
            elif "business logic" in line.lower() and line.startswith(("2", "#", "##")):
                current_section = "business_logic"
                continue
            elif "data flow" in line.lower() and line.startswith(("3", "#", "##")):
                current_section = "data_flow"
                continue
            elif "issues" in line.lower() and line.startswith(("4", "#", "##")):
                current_section = "issues"
                continue
            elif "modernization" in line.lower() and line.startswith(("5", "#", "##")):
                current_section = "modernization"
                continue

            if current_section:
                sections[current_section] += line + "\n"

        # Trim and clean up sections
        for key, value in sections.items():
            sections[key] = value.strip()

        analysis_results["structured_analysis"] = sections

        return analysis_results


class CobolDocumentationGenerator:
    """
    Generate detailed documentation for COBOL programs based on analysis results
    """

    def __init__(self, analyzer: CobolAnalyzer, llm_integration: Optional[CobolLLMIntegration] = None):
        """
        Initialize the documentation generator

        Args:
            analyzer: Initialized CobolAnalyzer instance
            llm_integration: Optional CobolLLMIntegration instance for enhanced documentation
        """
        self.analyzer = analyzer
        self.llm_integration = llm_integration
        self.logic_extractor = CobolLogicExtractor(analyzer)

    def generate_documentation(self, program_name: str, output_path: str = None, use_llm: bool = False) -> str:
        """
        Generate comprehensive documentation for a COBOL program

        Args:
            program_name: Name of the program to document
            output_path: Optional path to save the documentation
            use_llm: Whether to use LLM for enhanced analysis

        Returns:
            String containing the generated documentation
        """
        if program_name not in self.analyzer.analyzed_programs:
            return f"Program {program_name} not found in analyzed programs."

        program = self.analyzer.analyzed_programs[program_name]

        # Extract program logic
        logic_data = self.logic_extractor.extract_logic_for_llm(program_name)

        # Get LLM analysis if requested
        llm_analysis = None
        if use_llm and self.llm_integration:
            llm_analysis = self.llm_integration.analyze_with_llm(logic_data)

        # Generate documentation
        doc = self._build_documentation(program, logic_data, llm_analysis)

        # Save to file if requested
        if output_path:
            with open(output_path, 'w') as f:
                f.write(doc)

        return doc

    def _build_documentation(self, program: CobolProgram, logic_data: Dict[str, Any],
                             llm_analysis: Optional[Dict[str, Any]] = None) -> str:
        """
        Build the documentation content

        Args:
            program: CobolProgram instance
            logic_data: Extracted logic data
            llm_analysis: Optional LLM analysis results

        Returns:
            String containing the documentation
        """
        doc = f"# {program.name} - COBOL Program Documentation\n\n"

        # Basic information
        doc += "## Program Overview\n\n"
        doc += f"- **Program Name:** {program.name}\n"
        doc += f"- **Source File:** {program.source_path}\n"

        # Add LLM-derived purpose if available
        if llm_analysis and "purpose" in llm_analysis.get("structured_analysis", {}):
            doc += "\n### Purpose\n\n"
            doc += llm_analysis["structured_analysis"]["purpose"]

        # Program structure
        doc += "\n## Program Structure\n\n"

        # Add divisions and sections
        for division_name, division in program.divisions.items():
            doc += f"### {division_name} DIVISION\n\n"

            if division.sections:
                for section_name, section in division.sections.items():
                    doc += f"#### {section_name} SECTION\n\n"

                    if section.paragraphs:
                        doc += "Paragraphs:\n\n"
                        for para_name in section.paragraphs:
                            doc += f"- {para_name}\n"
                        doc += "\n"
            else:
                doc += "No sections defined.\n\n"

        # Add business logic if LLM analysis is available
        if llm_analysis and "business_logic" in llm_analysis.get("structured_analysis", {}):
            doc += "\n## Business Logic\n\n"
            doc += llm_analysis["structured_analysis"]["business_logic"]

        # Data structures
        doc += "\n## Data Structures\n\n"

        # Group data items by level
        level_01_items = {name: item for name, item in program.data_items.items() if item.level == 1}

        if level_01_items:
            for name, item in level_01_items.items():
                doc += f"### {name}\n\n"

                if item.picture:
                    doc += f"- **Picture:** {item.picture}\n"
                if item.usage:
                    doc += f"- **Usage:** {item.usage}\n"
                if item.value:
                    doc += f"- **Value:** {item.value}\n"
                if item.redefines:
                    doc += f"- **Redefines:** {item.redefines}\n"

                # Find child items
                children = {name: item for name, item in program.data_items.items()
                            if item.level > 1 and name.startswith(item.name)}

                if children:
                    doc += "\nChild items:\n\n"
                    doc += "| Name | Level | Picture | Usage | Value |\n"
                    doc += "| ---- | ----- | ------- | ----- | ----- |\n"

                    for child_name, child in children.items():
                        doc += f"| {child_name} | {child.level} | {child.picture or ''} | {child.usage or ''} | {child.value or ''} |\n"

                doc += "\n"
        else:
            doc += "No level 01 data items defined.\n\n"

        # Add data flow if LLM analysis is available
        if llm_analysis and "data_flow" in llm_analysis.get("structured_analysis", {}):
            doc += "\n## Data Flow\n\n"
            doc += llm_analysis["structured_analysis"]["data_flow"]

        # Dependencies
        doc += "\n## Dependencies\n\n"

        # Copybooks
        if program.copybooks:
            doc += "### Copybooks\n\n"
            for copybook in program.copybooks:
                doc += f"- {copybook}\n"
            doc += "\n"
        else:
            doc += "### Copybooks\n\nNo copybooks used.\n\n"

        # Maps
        if program.maps_used:
            doc += "### BMS Maps\n\n"
            for map_name in program.maps_used:
                doc += f"- {map_name}\n"
            doc += "\n"
        else:
            doc += "### BMS Maps\n\nNo BMS maps used.\n\n"

        # Called programs
        if program.calls:
            doc += "### Called Programs\n\n"
            doc += "| Program | Call Type | Parameters |\n"
            doc += "| ------- | --------- | ---------- |\n"

            for call in program.calls:
                call_type = "Dynamic" if call.is_dynamic else "Static"
                parameters = ", ".join(call.parameters) if call.parameters else "None"
                doc += f"| {call.target} | {call_type} | {parameters} |\n"

            doc += "\n"
        else:
            doc += "### Called Programs\n\nNo programs called.\n\n"

        # Calling programs
        callers = self.analyzer.find_caller_programs(program.name)
        if callers:
            doc += "### Called By\n\n"
            for caller in callers:
                doc += f"- {caller}\n"
            doc += "\n"
        else:
            doc += "### Called By\n\nNo programs call this program (entry point).\n\n"

        # Files
        if program.files:
            doc += "### Files\n\n"
            doc += "| File Name | Access Mode | Organization | Record Key |\n"
            doc += "| --------- | ----------- | ------------ | ---------- |\n"

            for file_ref in program.files:
                organization = file_ref.organization or "N/A"
                record_key = file_ref.record_key or "N/A"
                doc += f"| {file_ref.name} | {file_ref.access_mode} | {organization} | {record_key} |\n"

            doc += "\n"
        else:
            doc += "### Files\n\nNo files used.\n\n"

        # Resources
        if program.resources:
            doc += "### External Resources\n\n"

            # Group by type
            resources_by_type = {}
            for resource in program.resources:
                if resource.type not in resources_by_type:
                    resources_by_type[resource.type] = []
                resources_by_type[resource.type].append(resource)

            for resource_type, resources in resources_by_type.items():
                doc += f"#### {resource_type}\n\n"
                doc += "| Resource Name | Operation |\n"
                doc += "| ------------- | --------- |\n"

                for resource in resources:
                    doc += f"| {resource.name} | {resource.operation} |\n"

                doc += "\n"
        else:
            doc += "### External Resources\n\nNo external resources used.\n\n"

        # Add issues and modernization if LLM analysis is available
        if llm_analysis:
            if "issues" in llm_analysis.get("structured_analysis", {}):
                doc += "\n## Potential Issues\n\n"
                doc += llm_analysis["structured_analysis"]["issues"]

            if "modernization" in llm_analysis.get("structured_analysis", {}):
                doc += "\n## Modernization Strategy\n\n"
                doc += llm_analysis["structured_analysis"]["modernization"]

        return doc


def import_time():
    """Helper function to import datetime and return current time"""
    from datetime import datetime
    return datetime.now()


def main():
    """Main function for CLI use"""
    parser = argparse.ArgumentParser(description="COBOL Analysis Framework")
    parser.add_argument("--program", help="Path to the COBOL program to analyze")
    parser.add_argument("--directory", help="Path to the directory containing COBOL programs")
    parser.add_argument("--copybooks", help="Path to the directory containing copybooks")
    parser.add_argument("--output", help="Path to save the analysis output")
    parser.add_argument("--call-graph", help="Generate call graph and save to the specified file")
    parser.add_argument("--resource-report", help="Generate resource usage report and save to the specified file")
    parser.add_argument("--llm-key", help="API key for LLM integration")
    parser.add_argument("--llm-url", help="API URL for LLM integration")
    parser.add_argument("--llm-model", help="Model name for LLM integration")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for enhanced analysis")
    parser.add_argument("--document", action="store_true", help="Generate documentation for the program")

    args = parser.parse_args()

    # Initialize the analyzer
    copybook_paths = [args.copybooks] if args.copybooks else []
    analyzer = CobolAnalyzer(copybook_paths=copybook_paths)

    # Initialize LLM integration if requested
    llm_integration = None
    if args.llm_key and args.llm_url:
        llm_integration = CobolLLMIntegration(
            api_key=args.llm_key,
            api_url=args.llm_url,
            model_name=args.llm_model
        )

    # Analyze program or directory
    if args.program:
        program = analyzer.analyze_program(args.program)

        # Save analysis output
        if args.output:
            program.save_analysis(args.output)

        # Generate documentation if requested
        if args.document:
            doc_generator = CobolDocumentationGenerator(analyzer, llm_integration)
            doc_path = f"{os.path.splitext(args.output)[0]}_documentation.md" if args.output else None
            doc_generator.generate_documentation(program.name, doc_path, args.use_llm)
            logger.info(f"Documentation generated and saved to {doc_path}")

    elif args.directory:
        programs = analyzer.analyze_directory(args.directory)

        # Save analysis output
        if args.output:
            os.makedirs(args.output, exist_ok=True)

            for program_name, program in programs.items():
                output_path = os.path.join(args.output, f"{program_name}_analysis.json")
                program.save_analysis(output_path)

                # Generate documentation if requested
                if args.document:
                    doc_generator = CobolDocumentationGenerator(analyzer, llm_integration)
                    doc_path = os.path.join(args.output, f"{program_name}_documentation.md")
                    doc_generator.generate_documentation(program_name, doc_path, args.use_llm)

    # Generate call graph if requested
    if args.call_graph:
        call_graph = analyzer.generate_call_graph(args.call_graph)
        logger.info(f"Call graph generated and saved to {args.call_graph}")

    # Generate resource report if requested
    if args.resource_report:
        resource_report = analyzer.generate_resource_usage_report(args.resource_report)
        logger.info(f"Resource usage report generated and saved to {args.resource_report}")


if __name__ == "__main__":
    main()