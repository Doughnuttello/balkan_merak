import requests
import duckdb
from datetime import datetime


BASE_URL = (
    "https://ec.europa.eu/eurostat/api/"
    "dissemination/statistics/1.0/data"
)

DATASET = "demo_pjan"

COUNTRIES = ["BG", "RO", "EL"] # Bulgaria, Romania, Greece

CURRENT_YEAR = datetime.now().year
YEARS = [str(year) for year in range(2020, CURRENT_YEAR + 1)]

def get_population():
    url = f"{BASE_URL}/{DATASET}"

    params = {
        "geo": COUNTRIES,
        "time": YEARS,
        "lang": "en",
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def jsonstat_to_rows(data):
    dimensions = data["id"]
    sizes = data["size"]
    values = data["value"]

    categories = {}

    for dimension in dimensions:
        category = data["dimension"][dimension]["category"]
        index = category["index"]

        ordered_codes = sorted(index, key=index.get)

        categories[dimension] = ordered_codes

    rows = []

    for position, value in values.items():
        position = int(position)

        coordinates = []
        remainder = position

        for size in reversed(sizes):
            coordinates.append(remainder % size)
            remainder //= size

        coordinates.reverse()

        row = {}

        for dimension, coordinate in zip(dimensions, coordinates):
            row[dimension] = categories[dimension][coordinate]

        row["value"] = value

        rows.append(row)

    return rows


def main():
    data = get_population()

    rows = jsonstat_to_rows(data)

    print("=" * 90)
    print("EUROSTAT POPULATION")
    print("=" * 90)

    print(
        f"{'freq':<6}"
        f"{'unit':<6}"
        f"{'age':<10}"
        f"{'sex':<6}"
        f"{'geo':<6}"
        f"{'time':<8}"
        f"{'value':>15}"
    )

    print("-" * 90)

    for row in rows[:20]:
        print(
            f"{row['freq']:<6}"
            f"{row['unit']:<6}"
            f"{row['age']:<10}"
            f"{row['sex']:<6}"
            f"{row['geo']:<6}"
            f"{row['time']:<8}"
            f"{row['value']:>15}"
        )


    

if __name__ == "__main__":
    main()