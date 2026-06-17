from __future__ import annotations

import argparse
from pathlib import Path

from .evaluator import evaluate_resident_notes
from .excel_parser import parse_workbook
from .report_generator import write_issues_to_workbook


def main() -> int:
    parser = argparse.ArgumentParser(description='ProcessX falls management compliance checker')
    parser.add_argument('--input', required=True, help='Workbook containing resident input sheets')
    parser.add_argument('--output', required=True, help='Workbook path to write output sheets')
    parser.add_argument('--template', default='Your_Output_File.xlsx', help='Workbook template that contains output sheets')
    args = parser.parse_args()

    input_path = Path(args.input)
    template_path = Path(args.template)
    output_path = Path(args.output)

    residents = parse_workbook(input_path)
    issues_by_resident = {
        resident.resident_name: evaluate_resident_notes(resident.days, resident.resident_name)
        for resident in residents
    }
    write_issues_to_workbook(template_path, output_path, issues_by_resident)
    print(f'Wrote {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())