import pytest

from music_ml.data import generate
from music_ml.training import train


@pytest.fixture(scope="session")
def trained(tmp_path_factory):
    directory = tmp_path_factory.mktemp("pipeline")
    generate(directory / "data")
    report = train(directory / "data", directory / "artifacts")
    return directory, report
