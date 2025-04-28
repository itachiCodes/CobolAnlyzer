from CobolParser import CobolParser
from main import CobolProgram, logger
import os
from typing import Dict, Set, Any

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
