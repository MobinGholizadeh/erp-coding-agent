import pytest
from erp_coding_agent.execution.parsers.generic import GenericBuildParser, GenericTestParser
from erp_coding_agent.execution.parsers.csharp import CSharpBuildParser, CSharpTestParser
from erp_coding_agent.execution.parsers.typescript import TypeScriptBuildParser, TypeScriptTestParser

def test_generic_build_parser():
    parser = GenericBuildParser()
    stdout = "Compiling...\nError: Something failed\nDone."
    stderr = ""
    errors = parser.parse(stdout, stderr)
    assert len(errors) == 1
    assert errors[0].message == "Something failed"

def test_csharp_build_parser():
    parser = CSharpBuildParser()
    stdout = "Program.cs(12,34): error CS0103: The name 'xyz' does not exist in the current context"
    stderr = ""
    errors = parser.parse(stdout, stderr)
    assert len(errors) == 1
    assert errors[0].file == "Program.cs"
    assert errors[0].line == 12
    assert errors[0].column == 34
    assert errors[0].code == "CS0103"
    assert errors[0].message == "The name 'xyz' does not exist in the current context"

def test_csharp_test_parser():
    parser = CSharpTestParser()
    stdout = """
Failed Test.Namespace.Method [100 ms]
Error Message:
 System.Exception : ...
Stack Trace:
 at ...

Failed!  - Failed:     1, Passed:    10, Skipped:     2, Total:    13, Duration: 100 ms
    """
    stderr = ""
    passed, failed, skipped, failures = parser.parse(stdout, stderr)
    assert passed == 10
    assert failed == 1
    assert skipped == 2
    assert len(failures) == 1
    assert failures[0].name == "Test.Namespace.Method"

def test_typescript_build_parser():
    parser = TypeScriptBuildParser()
    stdout = "src/file.ts(10,5): error TS2322: Type 'string' is not assignable to type 'number'."
    stderr = ""
    errors = parser.parse(stdout, stderr)
    assert len(errors) == 1
    assert errors[0].file == "src/file.ts"
    assert errors[0].line == 10
    assert errors[0].column == 5
    assert errors[0].code == "TS2322"
    assert errors[0].message == "Type 'string' is not assignable to type 'number'."

def test_typescript_test_parser():
    parser = TypeScriptTestParser()
    stdout = """
 FAIL  src/App.test.tsx
  ● renders learn react link
  
Tests:       1 failed, 2 passed, 3 total
    """
    stderr = ""
    passed, failed, skipped, failures = parser.parse(stdout, stderr)
    assert passed == 2
    assert failed == 1
    assert skipped == 0
    assert len(failures) == 1
    assert failures[0].name == "renders learn react link"
