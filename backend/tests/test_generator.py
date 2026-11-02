import hashlib
import pandas as pd
from generator.generate import make_data

def test_starter_generator_has_expected_volumes_and_unique_applications(tmp_path):
    output = tmp_path / "generated"
    tables = make_data(seed=20261022, scale="starter", output=output)
    assert len(tables["job_requisitions"]) == 8
    assert len(tables["candidates"]) == 100
    assert len(tables["applications"]) == 150
    apps = pd.DataFrame(tables["applications"])
    assert not apps.duplicated(["requisition_id", "candidate_id"]).any()

def test_fixed_seed_reproduces_csv_checksums(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    make_data(seed=20261022, scale="starter", output=first)
    make_data(seed=20261022, scale="starter", output=second)
    digest = lambda folder: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.glob("*.csv"))}
    assert digest(first) == digest(second)
