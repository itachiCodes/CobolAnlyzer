import os
import json


def process_cobol_file(file_path):
    """
    Process a COBOL file and return a dictionary with paragraph names as keys
    and paragraph content as values.
    """
    paragraphs = {}
    procedure_found = "n"
    current_paragraph = None
    paragraph_content = []

    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        for line in file:
            # Skip lines shorter than 7 characters
            if len(line) < 7:
                continue

            # Skip empty lines
            if line[8:].strip() == '':
                continue

            # Skip commented lines (lines with * in 7th position)
            if line[6] == '*':
                continue

            if "PROCEDURE" in line:
                procedure_found = 'y'

            if procedure_found != 'y' or "PROCEDURE" in line:
                continue

            # Replace first 6 characters with spaces
            processed_line = "      " + line[6:]

            if processed_line[8] != " ":
                end_position = line.index('.', 7)
                paragraph_match = line[7:end_position]
            else:
                paragraph_match = ""


            if paragraph_match:
                # If we've been collecting content for a previous paragraph, save it
                if current_paragraph:
                    paragraphs[current_paragraph] = ''.join(paragraph_content).rstrip()

                # Start new paragraph
                current_paragraph = paragraph_match
                paragraph_content = []
            elif current_paragraph and processed_line.strip():
                # Add non-empty line to current paragraph content
                paragraph_content.append(processed_line)

            # Save the last paragraph
            if current_paragraph and paragraph_content:
                paragraphs[current_paragraph] = ''.join(paragraph_content).rstrip()

    return paragraphs


def process_single_file(input_file, output_file):
    """
    Process a single COBOL file and save the result as JSON.
    """
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return

    paragraphs = process_cobol_file(input_file)

    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(paragraphs, f, indent=2)

    print(f"Conversion complete. Output saved to {output_file}")
    print(f"Total paragraphs processed: {len(paragraphs)}")

def process_file(input_file, output_file):
    """
    Process a single COBOL file and save the result as JSON.
    """
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return

    paragraphs = process_cobol_file(input_file)

    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(paragraphs, f, indent=2)

    print(f"Conversion complete. Output saved to {output_file}")
    print(f"Total paragraphs processed: {len(paragraphs)}")

def main():
    input_file = r"C:\Users\rrajm\git\testdata\input\cobol\ESCAL056.scb"
    output_file = r"C:\Users\rrajm\git\testdata\input\cobol\test3.json"
    process_file(input_file, output_file)

if __name__ == "__main__":
    main()