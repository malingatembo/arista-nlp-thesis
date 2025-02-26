import re  
import json  
import yaml  
from pathlib import Path  
from typing import List, Dict  

class ManualParser:  
    def __init__(self):  
        self.base_dir = self._load_paths_config()  
        self.raw_dir = self.base_dir.parent / "raw"  
        self.current_section = None  
        self.current_content = []  
        self.parent_stack = []  
        self.code_counter = 0  
        self.table_counter = 0  
        self._parsing_metadata = False  

    def _load_paths_config(self) -> Path:  
        with open("configs/paths.yaml") as f:  
            config = yaml.safe_load(f)  
            return Path(config["paths"]["processed_data"])  

    def parse(self, input_filename: str):  
        input_path = self.raw_dir / input_filename  
        self._prepare_directories()  

        with open(input_path, 'r', encoding='utf-8') as f:  
            for line in f:  
                line = line.rstrip('\n')  
                self._process_line(line)  
            self._finalize_section()  

    def _prepare_directories(self):  
        Path(self.base_dir / "text").mkdir(exist_ok=True, parents=True)  
        Path(self.base_dir / "code_snippets").mkdir(exist_ok=True, parents=True)  
        Path(self.base_dir / "tables").mkdir(exist_ok=True, parents=True)  

    def _process_line(self, line: str):  
        if re.match(r'^### (CHAPTER|SUBSECTION|SUBSUBSECTION|SUBSUBSUBSECTION)', line):  
            self._finalize_section()  
            self._parse_section_header(line)  
            self._parsing_metadata = True  
        elif self._parsing_metadata:  
            if line.startswith('--'):  
                self._parse_metadata(line)  
            elif line.strip() == '':  
                self._parsing_metadata = False  
        elif line.strip() == '<!-- CODE:START -->':  
            self.code_counter = 0  
            self.current_code = []  
        elif line.strip() == '<!-- CODE:END -->':  
            self._save_code()  
        elif line.strip() == '<!-- TABLE:START -->':  
            self.table_counter = 0  
            self.current_table = []  
        elif line.strip() == '<!-- TABLE:END -->':  
            self._save_table()  
        else:  
            self._capture_content(line)  

    def _parse_section_header(self, line: str):  
        match = re.match(  
            r'^### (CHAPTER|SUBSECTION|SUBSUBSECTION|SUBSUBSUBSECTION) (\d+(?:\.\d+)*): (.+) ###',  
            line  
        )  
        if not match:  
            raise ValueError(f"Invalid section header: {line}")  

        section_type, section_num, title = match.groups()  
        section_id = f"{section_type.lower()}_{section_num.replace('.', '_')}"  

        self.current_section = {  
            "id": section_id,  
            "type": section_type.lower(),  
            "title": title,  
            "parents": [],  
            "code_refs": [],  
            "table_refs": []  
        }  

    def _parse_metadata(self, line: str):  
        key, value = map(str.strip, line.split(':', 1))  
        key = key.lstrip('-').lower()  
        
        if key == "parent":  
            if value not in [s["id"] for s in self.parent_stack]:  
                self.parent_stack.append({"id": value})  
            self.current_section["parents"].append(value)  
        else:  
            self.current_section[key] = value  

    def _capture_content(self, line: str):  
        if hasattr(self, 'current_code'):  
            self.current_code.append(line)  
        elif hasattr(self, 'current_table'):  
            self.current_table.append(line)  
        else:  
            line = re.sub(r'\[\[(CODE|TABLE):(.*?)\]\]', r'[[\1:\2]]', line)  
            self.current_content.append(line)  

    def _save_code(self):  
        code_id = f"code_{self.current_section['id']}_{self.code_counter}"  
        self.current_content.append(f"[[CODE:{code_id}]]")  
        self.current_section["code_refs"].append(code_id)  

        code_path = self.base_dir / "code_snippets" / f"{code_id}.json"  
        with open(code_path, 'w') as f:  
            json.dump({  
                "id": code_id,  
                "parent": self.current_section["id"],  
                "content": "\n".join(self.current_code)  
            }, f, indent=2)  

        self.code_counter += 1  
        del self.current_code  

    def _save_table(self):  
        table_id = f"table_{self.current_section['id']}_{self.table_counter}"  
        self.current_content.append(f"[[TABLE:{table_id}]]")  
        self.current_section["table_refs"].append(table_id)  

        table_path = self.base_dir / "tables" / f"{table_id}.json"  
        with open(table_path, 'w') as f:  
            json.dump({  
                "id": table_id,  
                "parent": self.current_section["id"],  
                "content": "\n".join(self.current_table)  
            }, f, indent=2)  

        self.table_counter += 1  
        del self.current_table  

    def _finalize_section(self):  
        if self.current_section:  
            self._save_text_section()  
            self.parent_stack = self.parent_stack[:-1] if self.parent_stack else []  
            self.current_section = None  
            self.current_content = []  

    def _save_text_section(self):  
        text_path = self.base_dir / "text" / f"{self.current_section['id']}.json"  
        with open(text_path, 'w') as f:  
            json.dump({  
                "id": self.current_section["id"],  
                "content": "\n".join(self.current_content),  
                "metadata": self.current_section  
            }, f, indent=2)  

if __name__ == "__main__":  
    parser = ManualParser()  
    parser.parse("arista_Ch2-Ch9_annotated.txt")
