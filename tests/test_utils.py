import pytest
from gencodedoc.utils.filters import FileFilter
from gencodedoc.utils.tree import TreeGenerator
from gencodedoc.models.config import IgnoreConfig

def test_file_filter(temp_project):
    ignore_config = IgnoreConfig(
        dirs=["venv"],
        files=[".env"],
        extensions=[".pyc"]
    )
    f = FileFilter(ignore_config, temp_project)
    
    # Directory check needs is_directory=True
    assert f.should_ignore(temp_project / "venv", is_directory=True) is True
    assert f.should_ignore(temp_project / ".env") is True
    assert f.should_ignore(temp_project / "main.pyc") is True
    assert f.should_ignore(temp_project / "src/main.py") is False

def test_tree_generator(temp_project):
    gen = TreeGenerator()
    tree = gen.generate(temp_project)
    
    assert "src" in tree
    assert "main.py" in tree
    assert "README.md" in tree

