import re
import json
import yaml
from pathlib import Path
from typing import Dict, List

class ManualParser:
    def __init__(self):
        self.base_dir = self._load_paths_config()
        self.raw_dir = self.base_dir.parent / "raw"
        self.sections = {'text': [], 'code': [], 'table': []}
        self.current_text_id = None
        self.current_text_metadata = {}
        self.current_text_content = []
        self.current_code = None
        self.current_table = None
        self.code_counter = 0
        self.table_counter = 0

    def _load_paths_config(self) -> Path:
        """Load output directory from configs/paths.yaml"""
        with open("configs/paths.yaml") as f:
            config = yaml.safe_load(f)
            return Path(config["paths"]["processed_data"])

    def parse(self, input_filename: str):
        """Parse text with nested code/tables, preserving relationships"""
        input_path = self.raw_dir / input_filename
        Path(self.base_dir / "text").mkdir(parents=True, exist_ok=True)
        Path(self.base_dir / "code_snippets").mkdir(parents=True, exist_ok=True)
        Path(self.base_dir / "tables").mkdir(parents=True, exist_ok=True)

        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')

                # Start new text section
                if line.startswith("### TEXT"):
                    self._finalize_text_section()
                    self._parse_text_header(line)
                
                # Start code block
                elif line.strip() == "<!-- CODE:START -->":
                    self.current_code = []
                
                # Start table block
                elif line.strip() == "<!-- TABLE:START -->":
                    self.current_table = []
                
                # End code/table block
                elif line.strip() == "<!-- CODE:END -->":
                    self._save_code_block()
                elif line.strip() == "<!-- TABLE:END -->":
                    self._save_table_block()
                
                # Collect content
                else:
                    if self.current_code is not None:
                        self.current_code.append(line)
                    elif self.current_table is not None:
                        self.current_table.append(line)
                    else:
                        self.current_text_content.append(line)

            self._finalize_text_section()

    def _parse_text_header(self, line: str):
        """Extract metadata from text section header"""
        self.current_text_metadata = {}
        self.code_counter = 0
        self.table_counter = 0
        match = re.search(r'### TEXT \((.*?)\) - Page (\d+) ###', line)
        if match:
            self.current_text_metadata.update({
                "source": match.group(1),
                "page": int(match.group(2)),
                "section": None,
                "content_type": "text",
                "code_children": [],
                "table_children": []
            })
        # Parse additional metadata lines (e.g., --SECTION:)
        self.current_text_id = f"section_{self.current_text_metadata['page']}_{len(self.sections['text'])}"

    def _save_code_block(self):
        """Save code block linked to parent text section"""
        code_id = f"code_{self.current_text_id}_{self.code_counter}"
        code_content = "\n".join(self.current_code)
        
        code_path = self.base_dir / "code_snippets" / f"{code_id}.json"
        with open(code_path, 'w') as f:
            json.dump({
                "id": code_id,
                "parent": self.current_text_id,
                "content": code_content,
                "metadata": self.current_text_metadata
            }, f, indent=2)

        self.current_text_metadata["code_children"].append(code_id)
        self.code_counter += 1
        self.current_code = None

    def _save_table_block(self):
        """Save table block linked to parent text section"""
        table_id = f"table_{self.current_text_id}_{self.table_counter}"
        table_content = "\n".join(self.current_table)
        
        table_path = self.base_dir / "tables" / f"{table_id}.json"
        with open(table_path, 'w') as f:
            json.dump({
                "id": table_id,
                "parent": self.current_text_id,
                "content": table_content,
                "metadata": self.current_text_metadata
            }, f, indent=2)

        self.current_text_metadata["table_children"].append(table_id)
        self.table_counter += 1
        self.current_table = None

    def _finalize_text_section(self):
        """Save completed text section with embedded references"""
        if self.current_text_metadata:
            text_content = "\n".join(self.current_text_content)
            
            text_path = self.base_dir / "text" / f"{self.current_text_id}.json"
            with open(text_path, 'w') as f:
                json.dump({
                    "id": self.current_text_id,
                    "content": text_content,
                    "metadata": self.current_text_metadata
                }, f, indent=2)
            
            self.sections['text'].append(self.current_text_id)
            self.current_text_content = []
            self.current_text_metadata = {}
            self.current_text_id = None

if __name__ == "__main__":
    parser = ManualParser()
    parser.parse("arista.txt")
