"""Generate architecture diagram for repominify.

This script creates a visualization of repominify's architecture using graphviz.
"""

import graphviz

def create_architecture_diagram(output_dir: str = "benchmark_results/visualizations"):
    """Create architecture diagram."""
    dot = graphviz.Digraph(
        'repominify_architecture',
        comment='Repominify Architecture',
        format='png'
    )
    
    # Set graph attributes
    dot.attr(rankdir='LR')
    dot.attr('node', shape='box', style='rounded')
    
    # Add nodes
    with dot.subgraph(name='cluster_input') as s:
        s.attr(label='Input')
        s.node('files', 'Project Files')
        s.node('imports', 'Import Statements')
        s.node('deps', 'Dependencies')
    
    with dot.subgraph(name='cluster_processing') as s:
        s.attr(label='Processing')
        s.node('parser', 'Parser')
        s.node('graph', 'Graph Builder')
        s.node('analyzer', 'Dependency Analyzer')
    
    with dot.subgraph(name='cluster_output') as s:
        s.attr(label='Output')
        s.node('context', 'Enhanced Context')
        s.node('stats', 'Statistics')
        s.node('viz', 'Visualizations')
    
    with dot.subgraph(name='cluster_llm') as s:
        s.attr(label='LLM Integration')
        s.node('prompt', 'Prompt Engineering')
        s.node('llm', 'LLM Interface')
        s.node('code', 'Generated Code')
    
    # Add edges
    dot.edge('files', 'parser')
    dot.edge('imports', 'parser')
    dot.edge('deps', 'parser')
    dot.edge('parser', 'graph')
    dot.edge('graph', 'analyzer')
    dot.edge('analyzer', 'context')
    dot.edge('analyzer', 'stats')
    dot.edge('analyzer', 'viz')
    dot.edge('context', 'prompt')
    dot.edge('prompt', 'llm')
    dot.edge('llm', 'code')
    
    # Save diagram
    dot.render(f"{output_dir}/architecture", cleanup=True)

if __name__ == "__main__":
    create_architecture_diagram() 