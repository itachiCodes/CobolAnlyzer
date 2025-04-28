from CobolTokenizer import CobolTokenizer
import os
from main import CobolProgram, logger, TokenType, Division, Section, Paragraph, DataItem, FileReference, ProgramCall, \
    Resource


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
            if self.tokens[i].type == TokenType.KEYWORD and self.tokens[i].value.upper() in['OPEN', 'CLOSE', 'READ', 'WRITE', 'REWRITE', 'DELETE', 'START']:
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
                            if self.tokens[j].value.upper() in ['FROM', 'INTO', 'UPDATE',
                                                                'TABLE'] and j + 1 < len(self.tokens):
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
                            if self.tokens[j].value.upper() in ['PROGRAM', 'TRANSID', 'QUEUE',
                                                                'FILE'] and j + 1 < len(self.tokens):
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
                if i + 1 < len(self.tokens) and self.tokens[i + 1].type in [TokenType.IDENTIFIER,
                                                                            TokenType.LITERAL]:
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