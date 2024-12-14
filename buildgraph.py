import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

import networkx as nx
import yaml


class CodeGraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.node_types = {
            'module': '#A5D6A7',  # Light green
            'class': '#90CAF9',   # Light blue
            'function': '#FFCC80', # Light orange
            'import': '#CE93D8'    # Light purple
        }
        
    def parse_repomix_file(self, file_path: str) -> Dict:
        """Parse a Repomix file and extract code content."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract file entries using the separator pattern
        file_entries = []
        current_file = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('File: '):
                if current_file:
                    file_entries.append({
                        'path': current_file,
                        'content': '\n'.join(current_content)
                    })
                current_file = line.replace('File: ', '').strip()
                current_content = []
            elif current_file and line != '================':
                current_content.append(line)
                
        if current_file:
            file_entries.append({
                'path': current_file,
                'content': '\n'.join(current_content)
            })
            
        return file_entries

    def analyze_imports(self, content: str) -> Set[str]:
        """Extract import statements from code."""
        imports = set()
        import_pattern = r'^(?:from\s+(\S+)\s+)?import\s+(.+)$'
        
        for line in content.split('\n'):
            line = line.strip()
            match = re.match(import_pattern, line)
            if match:
                from_module, imported = match.groups()
                if from_module:
                    imports.add(from_module)
                for item in imported.split(','):
                    item = item.strip().split()[0]  # Handle 'as' aliases
                    if from_module:
                        imports.add(f"{from_module}.{item}")
                    else:
                        imports.add(item)
        return imports

    def extract_classes_and_functions(self, content: str) -> Tuple[List[str], List[str]]:
        """Extract class and function definitions from code."""
        classes = []
        functions = []
        
        class_pattern = r'^\s*class\s+([^\(:]+)'
        function_pattern = r'^\s*def\s+([^\(:]+)'
        
        for line in content.split('\n'):
            class_match = re.match(class_pattern, line)
            if class_match:
                classes.append(class_match.group(1).strip())
                continue
                
            func_match = re.match(function_pattern, line)
            if func_match:
                functions.append(func_match.group(1).strip())
                
        return classes, functions

    def build_graph(self, file_entries: List[Dict]) -> nx.DiGraph:
        """Build a knowledge graph from the code analysis."""
        # First pass: Create nodes for all files
        for entry in file_entries:
            module_name = Path(entry['path']).stem
            self.graph.add_node(
                module_name,
                type='module',
                path=entry['path'],
                color=self.node_types['module']
            )
            
            # Add import nodes and relationships
            imports = self.analyze_imports(entry['content'])
            for imp in imports:
                if not self.graph.has_node(imp):
                    self.graph.add_node(
                        imp,
                        type='import',
                        color=self.node_types['import']
                    )
                self.graph.add_edge(module_name, imp, relationship='imports')
            
            # Add class and function nodes
            classes, functions = self.extract_classes_and_functions(entry['content'])
            
            for class_name in classes:
                full_class_name = f"{module_name}.{class_name}"
                self.graph.add_node(
                    full_class_name,
                    type='class',
                    color=self.node_types['class']
                )
                self.graph.add_edge(module_name, full_class_name, relationship='contains')
            
            for func_name in functions:
                full_func_name = f"{module_name}.{func_name}"
                self.graph.add_node(
                    full_func_name,
                    type='function',
                    color=self.node_types['function']
                )
                self.graph.add_edge(module_name, full_func_name, relationship='contains')
        
        return self.graph

    def generate_text_representation(self) -> str:
        """Generate a comprehensive text representation of the codebase context."""
        text_parts = []
        
        # Add graph overview
        text_parts.append("# Code Graph Overview")
        text_parts.append(f"Total nodes: {self.graph.number_of_nodes()}")
        text_parts.append(f"Total edges: {self.graph.number_of_edges()}\n")
        
        # Add node type statistics
        text_parts.append("## Node Type Distribution")
        for node_type, color in self.node_types.items():
            count = len([n for n, d in self.graph.nodes(data=True) if d.get('type') == node_type])
            text_parts.append(f"- {node_type}: {count}")
        text_parts.append("")
        
        # Add module information
        text_parts.append("## Module Structure")
        for node, data in sorted(self.graph.nodes(data=True)):
            if data.get('type') == 'module':
                text_parts.append(f"\n### Module: {node}")
                if 'path' in data:
                    text_parts.append(f"Path: {data['path']}")
                
                # List imports
                imports = [n for n in self.graph.neighbors(node) 
                          if self.graph.nodes[n].get('type') == 'import']
                if imports:
                    text_parts.append("\nImports:")
                    for imp in sorted(imports):
                        text_parts.append(f"- {imp}")
                
                # List classes
                classes = [n for n in self.graph.neighbors(node) 
                          if self.graph.nodes[n].get('type') == 'class']
                if classes:
                    text_parts.append("\nClasses:")
                    for class_name in sorted(classes):
                        text_parts.append(f"- {class_name.split('.')[-1]}")
                
                # List functions
                functions = [n for n in self.graph.neighbors(node) 
                           if self.graph.nodes[n].get('type') == 'function']
                if functions:
                    text_parts.append("\nFunctions:")
                    for func_name in sorted(functions):
                        text_parts.append(f"- {func_name.split('.')[-1]}")
        
        return '\n'.join(text_parts)

    def save_graph(self, output_dir: str):
        """Save the graph in multiple formats."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save as GraphML
        nx.write_graphml(self.graph, output_path / 'code_graph.graphml')
        
        # Save as JSON for visualization
        graph_data = {
            'nodes': [
                {
                    'id': node,
                    'type': data.get('type', 'unknown'),
                    'color': data.get('color', '#CCCCCC'),
                    'path': data.get('path', '')
                }
                for node, data in self.graph.nodes(data=True)
            ],
            'edges': [
                {
                    'source': source,
                    'target': target,
                    'relationship': data.get('relationship', 'unknown')
                }
                for source, target, data in self.graph.edges(data=True)
            ]
        }
        
        with open(output_path / 'code_graph.json', 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        # Save statistics
        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': {
                node_type: len([n for n, d in self.graph.nodes(data=True) 
                              if d.get('type') == node_type])
                for node_type in self.node_types
            }
        }
        
        with open(output_path / 'graph_statistics.yaml', 'w') as f:
            yaml.dump(stats, f, default_flow_style=False)
            
        # Save text representation
        text_content = self.generate_text_representation()
        with open(output_path / 'code_graph.txt', 'w') as f:
            f.write(text_content)


def main():
    parser = argparse.ArgumentParser(description='Build a knowledge graph from a Repomix codebase file.')
    parser.add_argument('--repomix-path', required=True, help='Path to the Repomix output file')
    parser.add_argument('--output-dir', default='code_graph_output', help='Output directory for graph files')
    
    args = parser.parse_args()
    
    builder = CodeGraphBuilder()
    file_entries = builder.parse_repomix_file(args.repomix_path)
    builder.build_graph(file_entries)
    builder.save_graph(args.output_dir)
    
    print(f"Graph has been built and saved to {args.output_dir}/")
    print(f"- GraphML file: {args.output_dir}/code_graph.graphml")
    print(f"- JSON file: {args.output_dir}/code_graph.json")
    print(f"- Statistics: {args.output_dir}/graph_statistics.yaml")
    print(f"- Text representation: {args.output_dir}/code_graph.txt")


if __name__ == '__main__':
    main()

