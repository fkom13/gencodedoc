"""Tests for documentation generator"""
import pytest
from pathlib import Path
from gencodedoc.core.documentation import DocumentationGenerator
from gencodedoc.models.config import ProjectConfig


def test_documentation_generator_initialization(tmp_path):
    """Test documentation generator initialization"""
    config = ProjectConfig(project_path=tmp_path)
    doc_gen = DocumentationGenerator(config)

    assert doc_gen.config == config
    assert doc_gen.tree_gen is not None
    assert doc_gen.filter is not None


def test_generate_markdown(tmp_path):
    """Test markdown documentation generation"""
    # Create test structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "README.md").write_text("# Test Project")

    config = ProjectConfig(
        project_name="test-project",
        project_path=tmp_path
    )
    doc_gen = DocumentationGenerator(config)

    output = doc_gen.generate()

    assert output.exists()
    assert output.suffix == '.md'

    content = output.read_text()
    assert "test-project" in content
    assert "Structure du projet" in content


def test_generate_with_custom_output(tmp_path):
    """Test documentation with custom output path"""
    (tmp_path / "test.py").write_text("# test")

    config = ProjectConfig(project_path=tmp_path)
    doc_gen = DocumentationGenerator(config)

    output_path = tmp_path / "custom_doc.md"
    result = doc_gen.generate(output_path=output_path)

    assert result == output_path
    assert output_path.exists()


def test_generate_with_filters(tmp_path):
    """Test documentation with include/exclude filters"""
    # Create test files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "include.py").write_text("# include")
    (tmp_path / "src" / "exclude.py").write_text("# exclude")

    config = ProjectConfig(project_path=tmp_path)
    doc_gen = DocumentationGenerator(config)

    output = doc_gen.generate(
        include_paths=["src/include.py"]
    )

    content = output.read_text()
    assert "include.py" in content


def test_generate_tree_only(tmp_path):
    """Test documentation with tree only"""
    (tmp_path / "test.py").write_text("# test")

    config = ProjectConfig(project_path=tmp_path)
    doc_gen = DocumentationGenerator(config)

    output = doc_gen.generate(
        include_tree=True,
        include_code=False
    )

    content = output.read_text()
    assert "Structure du projet" in content
    assert "Contenu des fichiers" not in content


def test_language_detection(tmp_path):
    """Test language detection in code blocks"""
    (tmp_path / "test.py").write_text("print('test')")
    (tmp_path / "test.js").write_text("console.log('test')")

    config = ProjectConfig(project_path=tmp_path)
    doc_gen = DocumentationGenerator(config)

    output = doc_gen.generate()
    content = output.read_text()

    assert "```python" in content or "```$python" in content
    assert "```javascript" in content or "```$javascript" in content
