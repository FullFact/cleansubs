"""Test subtitle processing."""
import os
import unittest

import cleansubs


class TestSentencer(unittest.TestCase):
    """Test prepared subtitles."""

    results = []

    def test_all(self):
        """"Compare the before/after versions in each directory in ./tests."""

        tests = os.listdir('tests')
        dirs = [f for f in tests if os.path.isdir(os.path.join('tests', f))]
        for dir in dirs:
            if dir[0] == '-':
                continue
            self.results = []

            with open(os.path.join('tests', dir, 'after.sub'), 'r') as f:
                target = [line.strip() for line in f.readlines()]
            with open(os.path.join('tests', dir, 'before.sub'), 'r') as f:
                sentencer = cleansubs.Sentencer(self.results.append)
                for line in f:
                    sentencer.process(line)

            with self.subTest(dir=dir):
                self.assertEqual(target, self.results)
