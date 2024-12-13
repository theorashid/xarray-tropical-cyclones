import os

import altair as alt
from dotenv import load_dotenv
import xarray as xr
import numpy as np

KT_MS_CONVERSION_FACTOR = 0.514444
CATEGORY_1_THRESHOLD = 64.0 * KT_MS_CONVERSION_FACTOR


def load_data() -> xr.Dataset:
    load_dotenv()
    dataset_path = os.getenv("DATASET_PATH")

    data = xr.open_dataset(dataset_path, engine="h5netcdf")

    data["basin"] = data["basin"].astype(str)
    data["sid"] = data["sid"].astype(str)
    data["name"] = data["name"].astype(str)

    return data


def plot_annual_dist2land_trend(data: xr.Dataset) -> alt.Chart:
    annual_cyclones = data.groupby("time.year").mean()[["max_wind", "dist2land"]]
    df_annual_cyclones = annual_cyclones.to_dataframe().reset_index()

    base = alt.Chart(df_annual_cyclones).encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y(
            "dist2land:Q", title="Distance to Land (km)", scale=alt.Scale(zero=False)
        ),
        tooltip=[
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("dist2land:Q", title="Distance to Land (km)"),
        ],
    )

    line = base.mark_line(color="steelblue", opacity=0.7).properties(
        title="Average Distance to Land of hurricanes per Year", width=800, height=400
    )

    points = base.mark_point(color="steelblue", size=50, opacity=0.7)

    trend = base.transform_regression("year", "dist2land").mark_line(
        color="lightcoral", opacity=0.7
    )

    chart = (
        (line + points + trend)
        .configure_axis(labelFontSize=12, titleFontSize=14)
        .configure_title(fontSize=16)
    )

    return chart


def main() -> None:
    data = load_data()

    # convert wind speed from knots to m/s
    data["max_wind"] = data["usa_wind"] * KT_MS_CONVERSION_FACTOR

    # select storms with coordinate time between 1982 and 2017, 3877 storms
    data_filtered = data.where(
        (data["time"] >= np.datetime64("1982-01-01"))
        & (data["time"] <= np.datetime64("2017-12-31")),
        drop=True,
    )

    # find the maximum wind speed for each storm
    max_wind_per_storm = data_filtered["max_wind"].max(dim="date_time")

    # filter storms based on the maximum wind speed (also gets rid of any nan series)
    storms_above_threshold = max_wind_per_storm >= CATEGORY_1_THRESHOLD
    data_filtered = data_filtered.where(storms_above_threshold, drop=True)

    chart = plot_annual_dist2land_trend(data_filtered)
    chart.save("distance_to_land.png", scale_factor=3.0)


if __name__ == "__main__":
    main()
