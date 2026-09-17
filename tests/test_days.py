"""Byte-for-byte regression: each tests/<day>/ folder holds GLSummary.pdf,
TrialBalance.pdf and expected_JJ<no>_Skyview_<MonDD>.csv."""
import glob
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(__file__)
SCRIPT = os.path.join(HERE, "..", "skyview_je.py")
DAYS = sorted(d for d in glob.glob(os.path.join(HERE, "*")) if os.path.isdir(d) and glob.glob(os.path.join(d, "expected_JJ*.csv")))


@pytest.mark.parametrize("day", DAYS, ids=os.path.basename)
def test_day(day, tmp_path):
    expected = glob.glob(os.path.join(day, "expected_JJ*.csv"))[0]
    journal = re.search(r"expected_JJ(\d+)_", expected).group(1)
    r = subprocess.run([sys.executable, SCRIPT, os.path.join(day, "GLSummary.pdf"),
                        os.path.join(day, "TrialBalance.pdf"), "--journal", journal,
                        "--out-dir", str(tmp_path), "--state", str(tmp_path / "state.json")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    out = tmp_path / os.path.basename(expected).replace("expected_", "")
    assert out.read_bytes() == open(expected, "rb").read()
