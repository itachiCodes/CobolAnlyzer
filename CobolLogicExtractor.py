from typing import Dict, Any
from CobolAnalyzer import CobolAnalyzer


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
                    if any(("READ " in line or "WRITE " in line or "REWRITE " in line) for line in
                           paragraph_lines):
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
