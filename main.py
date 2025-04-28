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
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Any, Tuple
from enum import Enum, auto
import logging

from CobolAnalyzer import CobolAnalyzer
from CobolDocumentationGenerator import CobolDocumentationGenerator
from CobolLLMIntegration import CobolLLMIntegration

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