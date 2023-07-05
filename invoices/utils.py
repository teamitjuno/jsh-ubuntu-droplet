import pandas as pd
from io import BytesIO


def process_xlsx(file_name):
    # Read the .xlsx file
    df = pd.read_excel(file_name)

    # Group by 'Katalogeintrag' and sum the 'Menge' and 'EK Gesamtpreis' columns
    grouped_df = (
        df.groupby("Katalogeintrag")
        .agg({"Menge": "sum", "EK Gesamtpreis": "sum"})
        .reset_index()
    )

    # Merge the aggregated values with the original dataframe
    merged_df = pd.merge(df, grouped_df, on="Katalogeintrag", suffixes=("", "_sum"))

    # Drop duplicate 'Katalogeintrag' rows, keeping the first occurrence
    deduplicated_df = merged_df.drop_duplicates(subset="Katalogeintrag", keep="first")

    # Update the 'Menge' and 'EK Gesamtpreis' columns with the aggregated values
    deduplicated_df.loc[:, "Menge"] = deduplicated_df["Menge_sum"]
    deduplicated_df.loc[:, "EK Gesamtpreis"] = deduplicated_df["EK Gesamtpreis_sum"]

    # Drop the temporary aggregation columns
    deduplicated_df = deduplicated_df.drop(columns=["Menge_sum", "EK Gesamtpreis_sum"])

    # Delete columns A, B, E, F, G, and H
    deduplicated_df = deduplicated_df.drop(
        columns=[
            "Projektakte",
            "Projektbezeichnung",
            "Vorgangsnummer",
            "Vorgangstyp",
            "Lieferant / Kunde",
            "Belegdatum",
        ]
    )

    # Instead of writing to an Excel file on disk, write to a BytesIO object
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        deduplicated_df.to_excel(writer, sheet_name="Sheet1", index=False)

    output.seek(0)

    # return the BytesIO object
    return output
