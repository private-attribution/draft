from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .command import Command


def get_branch_commit_hash(local_ipa_path: Path, branch: str) -> str:
    command = Command(cmd=f"git -C {local_ipa_path} fetch --all")
    result = command.run_blocking()
    command = Command(cmd=f"git -C {local_ipa_path} rev-parse origin/{branch}")
    result = command.run_blocking()
    return result.stdout.strip()


@dataclass
class Paths:
    repo_path: Path
    config_path: Path
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    _test_data_path: Optional[Path] = None

    def __post_init__(self):
        if self.branch and not self.commit_hash:
            self.commit_hash = get_branch_commit_hash(self.repo_path, self.branch)

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
