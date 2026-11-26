"""Tests PLCOpen XML parser."""
import json
import subprocess
import sys
import os

sys.path.append(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../src"))
from python.core import run_checker, binary_default  # noqa
from python.dump import DumpManager  # noqa

EXAMPLE = 'plcopen/example.xml'


def test_no_parser_errors():
    checker_warnings, rc = run_checker([EXAMPLE], args=['-i', 'xml'])
    assert rc == 0, f"Incorrect exit code for {EXAMPLE}"
    errors = [w for w in checker_warnings if w.id in ('ParserError', 'LexingError')]
    assert not errors, errors
    with DumpManager(f'{EXAMPLE}.dump.json'):
        pass


def test_json_output_is_only_json():
    """`-o json` prints the warnings and nothing else, also for XML input."""
    out = subprocess.run([binary_default, '-q', '-o', 'json', '-i', 'xml', EXAMPLE],
                         capture_output=True, check=True).stdout
    assert isinstance(json.loads(out), list)
