#!/usr/bin/env python3
"""
Smoke tests for complexity_analyser.py.

Verify that ComplexityAnalyzer counts nodes, identifies primitives vs operations,
and produces a non-zero complexity score for representative SolidPython structures.
"""

import unittest
from solid import cube, sphere, union, translate
from complexity_analyser import ComplexityAnalyzer


class TestComplexityAnalyzer(unittest.TestCase):
    def test_single_primitive_counts_one_node(self):
        analyzer = ComplexityAnalyzer(cube([10, 10, 10]))
        report = analyzer.get_complexity_report()
        self.assertGreaterEqual(report['total_nodes'], 1)
        self.assertGreater(report['complexity_score'], 0)

    def test_union_increases_node_count(self):
        small = ComplexityAnalyzer(cube([1, 1, 1])).get_complexity_report()
        bigger = ComplexityAnalyzer(
            union()(cube([1, 1, 1]), sphere(1), translate([5, 0, 0])(cube([2, 2, 2])))
        ).get_complexity_report()
        self.assertGreater(bigger['total_nodes'], small['total_nodes'])
        self.assertGreater(bigger['complexity_score'], small['complexity_score'])

    def test_operation_node_recorded_in_operation_counts(self):
        report = ComplexityAnalyzer(union()(cube([1, 1, 1]), sphere(1))).get_complexity_report()
        op_total = sum(report['operation_counts'].values())
        self.assertGreaterEqual(op_total, 1, f"Expected ≥1 operation, got {dict(report['operation_counts'])}")


if __name__ == '__main__':
    unittest.main()
