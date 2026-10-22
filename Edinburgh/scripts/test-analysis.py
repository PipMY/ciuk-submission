#!/usr/bin/env python3
import csv
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

class AnalysisTest(unittest.TestCase):
    def test_final_eligibility_and_missing_energy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / 'scripts'
            artifacts = root / 'artifacts/cirrus'
            scripts.mkdir()
            (artifacts / 'experiments').mkdir(parents=True)
            shutil.copy(Path(__file__).with_name('summarise-cirrus.py'), scripts)
            (artifacts / 'experiments/final-scaling-jobs.txt').write_text('1 101\n2 102\n3 103\n4 104\n')
            (artifacts / 'accounting.psv').write_text(
                'JobID|State|ElapsedRaw|AllocCPUS|NNodes|ConsumedEnergyRaw\n'
                '101|COMPLETED|1900|288|1|5000\n'
                '102|TIMEOUT|1900|576|2|7000\n'
                '103|PENDING|0|0|3|0\n'
                '104|COMPLETED|1900|1152|4|0\n')
            for job, timed in [('101', 1801), ('102', 1801), ('104', 1799)]:
                run = artifacts / 'experiments/runs' / job
                run.mkdir(parents=True)
                (run / 'HPCG-Benchmark-fixture.txt').write_text(
                    f'Final Summary::HPCG result is VALID with a GFLOP/s rating of=100\n'
                    f'Benchmark Time Summary::Total={timed}\n'
                    'Machine Summary::Distributed Processes=288\n')
            subprocess.run(['python3', str(scripts / 'summarise-cirrus.py')], check=True, capture_output=True)
            with (root / 'results/hpcg-cirrus.csv').open() as f:
                rows = {r['job_id']: r for r in csv.DictReader(f)}
            self.assertEqual(rows['101']['final_duration_eligible'], 'True')
            self.assertEqual(rows['102']['final_duration_eligible'], 'False')
            self.assertEqual(rows['104']['final_duration_eligible'], 'False')
            self.assertEqual(rows['104']['gflops_per_W'], '')
            self.assertIn('PENDING', (root / 'results/FINAL_SCALING.md').read_text())
            ET.fromstring((root / 'results/scaling-final.svg').read_text())

if __name__ == '__main__':
    unittest.main()
