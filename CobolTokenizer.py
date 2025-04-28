import re
from typing import List
from main import Token, TokenType


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