import io
import os
from datetime import datetime

import requests
import pyarrow as pa
import pyarrow.parquet as pq
from b2sdk.v2 import InMemoryAccountInfo, B2Api


BASE_URL = (
    "https://ec.europa.eu/eurostat/api/"
    "dissemination/statistics/1.0/data"
)

DATASET = "demo_pjan"

COUNTRIES = ["BG", "RO", "EL"]

START_YEAR = 2023
CURRENT_YEAR = datetime.now().year

YEARS = [
    str(year)
    for year in range(START_YEAR, CURRENT_YEAR + 1)
]

BUCKET_NAME = "balkan-merak-data"
B2_FILE_NAME = "src/population/population.parquet"


def get_population():
    url = f"{BASE_URL}/{DATASET}"

    params = {
        "geo": COUNTRIES,
        "time": YEARS,
        "age": "TOTAL",
        "sex": ["M", "F"],
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

        ordered_codes = sorted(
            index,
            key=index.get,
        )

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

        for dimension, coordinate in zip(
            dimensions,
            coordinates,
        ):
            row[dimension] = categories[dimension][coordinate]

        row["value"] = value

        rows.append(row)

    return rows


def upload_to_b2(rows):
    key_id = "003e898d12b7ec80000000001"
    application_key = "K0035wTLYhQIG9rDcO+/obMFzm2mGT0"

    info = InMemoryAccountInfo()
    b2_api = B2Api(info)

    b2_api.authorize_account(
        "production",
        key_id,
        application_key,
    )

    bucket = b2_api.get_bucket_by_name(
        BUCKET_NAME
    )

    # Convert rows to an Arrow table
    table = pa.Table.from_pylist(rows)

    # Create Parquet in memory
    buffer = io.BytesIO()

    pq.write_table(
        table,
        buffer,
    )

    # Get the Parquet bytes
    data = buffer.getvalue()

    # Upload directly to B2
    bucket.upload_bytes(
        data,
        B2_FILE_NAME,
    )

    print()
    print("=" * 60)
    print("B2 UPLOAD SUCCESSFUL")
    print("=" * 60)
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Path:   {B2_FILE_NAME}")
    print(f"Rows:   {len(rows)}")
    print(f"Size:   {len(data):,} bytes")


def main():
    print("=" * 60)
    print("EUROSTAT POPULATION INGESTION")
    print("=" * 60)

    print(f"Dataset:   {DATASET}")
    print(f"Countries: {COUNTRIES}")
    print(f"Years:     {YEARS}")

    print()
    print("Retrieving data from Eurostat...")

    data = get_population()

    rows = jsonstat_to_rows(data)

    print(f"Retrieved {len(rows)} rows.")

    upload_to_b2(rows)


if __name__ == "__main__":
    main()