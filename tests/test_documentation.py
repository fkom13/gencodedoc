import pytest
from gencodedoc.core.documentation import DocumentationGenerator

def test_doc_generation(temp_project, config_manager):
    config = config_manager.init_project()
    generator = DocumentationGenerator(config)
    
    output = generator.generate()
    
    assert output.exists()
    content = output.read_text()
    assert "# Test Project" in content  # From README.md
    assert "print('hello')" in content  # From src/main.py (if included)

def test_doc_custom_output(temp_project, config_manager):
    config = config_manager.init_project()
    generator = DocumentationGenerator(config)
    
    custom_path = temp_project / "docs/API.md"
    custom_path.parent.mkdir()
    
    generator.generate(output_path=custom_path)
    
    assert custom_path.exists()
