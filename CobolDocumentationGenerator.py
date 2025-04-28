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
