from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Paths:
    repo_path: Path
    config_path: Path
    commit_hash: str
    _test_data_path: Optional[Path] = None

    @property
    def test_data_path(self) -> Path:
        if self._test_data_path is None:
            return self.repo_path / Path("test_data/input")
        return self._test_data_path

    @test_data_path.setter
    def test_data_path(self, test_data_path: Path):
        self._test_data_path = test_data_path

    @property
    def target_path(self) -> Path:
        return self.repo_path / Path(f"target-{self.commit_hash}")

    @property
    def helper_binary_path(self) -> Path:
        return self.target_path / Path("release/helper")

    @property
    def report_collector_binary_path(self) -> Path:
        return self.target_path / Path("release/report_collector")
