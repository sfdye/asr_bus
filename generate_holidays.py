"""Generate ios_widget/holidays.json from the holidays package."""

import json
from datetime import date
from pathlib import Path

import holidays

OUTPUT = Path(__file__).parent / "ios_widget" / "holidays.json"


def main():
    current_year = date.today().year
    years = range(current_year, current_year + 2)
    result = {}
    for year in years:
        sg = holidays.Singapore(years=year)
        result[str(year)] = sorted(d.isoformat() for d in sg.keys())
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Written {OUTPUT} for years {list(years)}")


if __name__ == "__main__":
    main()
