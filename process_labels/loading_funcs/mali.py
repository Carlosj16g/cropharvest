import geopandas
import pandas as pd

from datetime import datetime

from .utils import process_crop_non_crop
from cropharvest.config import EXPORT_END_DAY, EXPORT_END_MONTH
from cropharvest.columns import RequiredColumns, NullableColumns
from ..utils import DATASET_PATH


LABEL_TO_CLASSIFICATION = {
    "maize": "cereals",
    "sorghum": "cereals",
    "millet": "cereals",
    "rice": "cereals",
    "sesame": "oilseeds",
    "groundnuts": "oilseeds",
    "beans": "leguminous",
    "cotton": "other",
}


def load_mali_crop_noncrop():
    df = process_crop_non_crop(DATASET_PATH / "mali/mali_noncrop_2019")
    # not sure about this
    df[RequiredColumns.COLLECTION_DATE] = datetime(2019, 1, 1)
    df[RequiredColumns.EXPORT_END_DATE] = datetime(2020, EXPORT_END_MONTH, EXPORT_END_DAY)
    df = df.reset_index(drop=True)
    df[RequiredColumns.INDEX] = df.index
    return df


def load_mali():
    df = geopandas.read_file(DATASET_PATH / "mali/segou_bounds_07212020")

    df[RequiredColumns.LON] = df.geometry.centroid.x.values
    df[RequiredColumns.LAT] = df.geometry.centroid.y.values
    df[RequiredColumns.COLLECTION_DATE] = datetime(2020, 7, 21)
    df[RequiredColumns.IS_CROP] = 1

    final_dfs = []
    for year in [2018, 2019]:
        year_df = df.copy()
        year_df[NullableColumns.LABEL] = year_df[f"{year}_main_"]
        year_df[NullableColumns.CLASSIFICATION_LABEL] = year_df.apply(
            lambda x: LABEL_TO_CLASSIFICATION[x[NullableColumns.LABEL]], axis=1
        )
        year_df[RequiredColumns.EXPORT_END_DATE] = datetime(
            year + 1, EXPORT_END_MONTH, EXPORT_END_DAY
        )
        year_df = year_df.drop(
            columns=["2018_main_", "2018_other", "2019_main_", "2019_other", "2019_mai_1"]
        )
        final_dfs.append(year_df)

    df = pd.concat(final_dfs)
    df = df.reset_index(drop=True)
    df[RequiredColumns.INDEX] = df.index

    return df


def load_mali_hlc():
    df = pd.read_csv(
        DATASET_PATH / "mali/helmets_crop_type_mapping_2022_04_06_16_20_56_356161.csv"
    )

    # currently don't include intercropped crops
    df = df[df["multiple_crops"] == "no"]

    df[RequiredColumns.LON] = df[
        "field_specification_assessment/_geopoint_widget_placementmap_longitude"
    ]
    df[RequiredColumns.LAT] = df[
        "field_specification_assessment/_geopoint_widget_placementmap_latitude"
    ]
    df[RequiredColumns.COLLECTION_DATE] = pd.to_datetime(df["today"])
    df[RequiredColumns.IS_CROP] = 1

    df[NullableColumns.LABEL] = df["current_season_crop/current_season_current_crop"]
    df[NullableColumns.CLASSIFICATION_LABEL] = df.apply(
        lambda x: LABEL_TO_CLASSIFICATION[x[NullableColumns.LABEL]], axis=1
    )
    df[RequiredColumns.EXPORT_END_DATE] = datetime(2022, EXPORT_END_MONTH, EXPORT_END_DAY)
    df[RequiredColumns.GEOMETRY] = df.apply(
        lambda x: Point(x[RequiredColumns.LON], x[RequiredColumns.LAT]), axis=1
    )

    df = df.reset_index(drop=True)
    df[RequiredColumns.INDEX] = df.index

    return geopandas.GeoDataFrame(df, geometry=RequiredColumns.GEOMETRY)
