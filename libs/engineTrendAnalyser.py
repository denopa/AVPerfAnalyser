import pandas as pd
import numpy as np
import sqlalchemy, os
from matplotlib import pyplot as plt
import datetime as dt
import seaborn as sns

try:
    sqlURL = os.environ["DATABASE_URL"]
except:
    sqlURL = "postgresql://localhost/AVPerformance"
engine = sqlalchemy.create_engine(sqlURL)
conn = engine.connect()

flights = pd.read_sql("analysed_flights", conn)
flights.loc[42, "flightDate"] = dt.datetime(2019, 11, 22)
flights.flightDate = pd.to_datetime(
    flights.flightDate, errors="coerce", format="%Y-%m-%d"
)
flights.sort_values(by=["flightDate"], inplace=True)
ContinuousFlights = flights[flights.continuousData]
flights.reset_index(inplace=True)

flights.describe()
flights.loc[0]


# plt.style.available
plt.style.use("ggplot")


def is_outlier(points, thresh=2.5):
    if len(points.shape) == 1:
        points = points[:, None]
    median = np.median(points, axis=0)
    diff = np.sum((points - median) ** 2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)
    modified_z_score = 0.6745 * diff / med_abs_deviation
    return modified_z_score > thresh


def scatterPlot(flights, x, y, removeOutliers=True):
    validData = flights[flights[x].notna() & flights[y].notna()]
    if removeOutliers:
        validData["isoutlier"] = is_outlier(validData[[x, y]].to_numpy())
        filtered = validData[~validData.isoutlier]
        print(len(filtered))
    else:
        filtered = validData
    plt.scatter(filtered[x], filtered[y])
    plt.xlabel(x)
    plt.ylabel(y)
    plt.show()


def heatMap(flights, x, y, z, removeOutliers=True):
    validData = flights[flights[x].notna() & flights[y].notna() & flights[z].notna()]
    if removeOutliers:
        validData["isoutlier"] = is_outlier(validData[[x, y, z]].to_numpy())
        filtered = validData[~validData.isoutlier]
    else:
        filtered = validData
    filtered.sort_values(axis=0, by=[x, y], inplace=True)
    filtered.reset_index(inplace=True)
    plt.imshow(
        filtered[[x, y, z]].to_numpy(dtype="float"),
        cmap="plasma",
        interpolation="none",
        origin="lower",
        extent=(
            filtered[x].min(),
            filtered[x].max(),
            filtered[y].min(),
            filtered[y].max(),
        ),
        aspect="auto",
        vmin=filtered[z].min(),
    )
    plt.colorbar()
    plt.xlabel(x)
    plt.ylabel(y)
    plt.show()


scatterPlot(
    flights,
    "Climb Average temp vs ISA Actual",
    "Climb Average Vertical Speed Actual",
    removeOutliers=True,
)
scatterPlot(
    flights, "Takeoff IAS Variance", "Takeoff Roll Variance", removeOutliers=True
)
scatterPlot(
    flights,
    "Climb Time Actual",
    "Climb Average Vertical Speed Variance",
    removeOutliers=True,
)
scatterPlot(
    flights, "Take off Fuel Flow Actual", "Climb Max CHT Actual", removeOutliers=True
)


scatterPlot(
    flights,
    "Climb Average temp vs ISA Actual",
    "Climb Highest Average CHT Actual",
    removeOutliers=True,
)
scatterPlot(
    flights,
    "Take off Fuel Flow Actual",
    "Climb Highest Average CHT Actual",
    removeOutliers=True,
)
heatMap(
    flights,
    "Climb Average temp vs ISA Actual",
    "Take off Fuel Flow Actual",
    "Climb Highest Average CHT Actual",
    removeOutliers=True,
)

# looking at stability
flightColumns = flights.columns.values
stabilityColumns = []
for column in flightColumns:
    if column[-9:] == "Stability":
        stabilityColumns.append(column)
flights[stabilityColumns].describe()


plt.scatter(
    flights.loc[27:, "Cruise Max Altitude Actual"],
    flights.loc[27:, "Cruise Intercooler Efficiency Actual"],
)
plt.scatter(
    flights.loc[27:, "Cruise Average Temp vs ISA Actual"],
    flights.loc[27:, "Cruise Intercooler Efficiency Actual"],
)
plt.scatter(
    flights.loc[:, "Climb Average temp vs ISA Actual"],
    flights.loc[:, "Climb Max CHT Actual"],
)
plt.scatter(
    flights.loc[:, "Climb Average temp vs ISA Actual"],
    flights.loc[:, "Climb Max TIT Actual"],
)
plt.scatter(
    flights.loc[:, "Climb Average temp vs ISA Actual"],
    flights.loc[:, "Climb Average Vertical Speed Actual"],
)


flights.loc[flights["Cruise Intercooler Efficiency Actual"].idxmax(), "file"]
