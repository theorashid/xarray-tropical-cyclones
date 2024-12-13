import os

from dotenv import load_dotenv
import xarray as xr
import numpy as np
import altair as alt
import altair_tiles as til

KT_MS_CONVERSION_FACTOR = 0.514444


def main() -> None:
    load_dotenv()
    dataset_path = os.getenv("DATASET_PATH")

    data = xr.open_dataset(dataset_path, engine="h5netcdf")

    data["basin"] = data["basin"].astype(str)
    data["sid"] = data["sid"].astype(str)
    data["name"] = data["name"].astype(str)

    # convert wind speed from knots to m/s
    data["max_wind"] = data["usa_wind"] * KT_MS_CONVERSION_FACTOR

    # filter data between March 1, 2017, and October 31, 2017
    data_filtered = data.where(
        (data["time"] >= np.datetime64("2017-03-01"))
        & (data["time"] <= np.datetime64("2017-10-31")),
        drop=True,
    )

    df_plot = (
        data_filtered[["basin", "max_wind", "lat", "lon", "storm", "time", "name"]]
        .to_dataframe()
        .reset_index()
    )
    df_plot = df_plot.dropna(subset=["time"])

    chart = (
        alt.Chart(df_plot)
        .mark_point(size=2, opacity=0.8)
        .encode(
            longitude="lon:Q",
            latitude="lat:Q",
            color=alt.Color(
                "max_wind:Q",
                scale=alt.Scale(scheme="inferno"),
                title="Max Wind Speed",
                legend=alt.Legend(orient="bottom"),
            ),
            tooltip=["storm", "time", "lat", "lon", "max_wind", "name"],
        )
        .properties(title="Storm Tracks, 2017", width=800, height=400)
    )

    chart = til.add_tiles(chart).properties(width=600, height=400)
    chart.save("storm_tracks_2017.png", scale_factor=3.0)


if __name__ == "__main__":
    main()
