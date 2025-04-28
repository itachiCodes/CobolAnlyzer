import os
import re
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Any, Tuple
from main import logger, import_time


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