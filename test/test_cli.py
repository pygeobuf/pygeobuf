import os.path

from click.testing import CliRunner
import pytest

from geobuf.scripts.cli import cli


@pytest.fixture
def props_json():
    return open(
        os.path.join(os.path.dirname(__file__), "fixtures/props.json")).read()


def test_cli_roundtrip(props_json):
    runner = CliRunner()
    result = runner.invoke(cli, ['encode'], props_json)
    assert result.exit_code == 0
    pbf = result.output_bytes
    result = runner.invoke(cli, ['decode'], pbf)
    assert result.exit_code == 0
    assert "@context" in result.output
    assert result.output.count("Feature") == 6
