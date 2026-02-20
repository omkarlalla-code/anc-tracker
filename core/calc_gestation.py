#!/usr/bin/env python3
"""Calculate gestational age from LMP.

Usage: echo "2024-01-15" | ./calc_gestation.py
Output: weeks as integer
"""
import sys
from datetime import datetime


def main():
    lmp_str = sys.stdin.read().strip()

    try:
        lmp = datetime.strptime(lmp_str, "%Y-%m-%d")
        now = datetime.now()
        weeks = (now - lmp).days // 7
        print(weeks)
        return 0
    except ValueError as e:
        sys.stderr.write("Error: Invalid date format (use YYYY-MM-DD)\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
