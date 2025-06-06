#!/usr/bin/env python3

import csv
import sys

def read(file):
    time = []
    x = []
    y = []
    with open(file, "r") as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            time.append(row["Time"])
            x.append(row["X1"])
            y.append(row["Y1"])

    return (time, x, y)

time1, x1, y1 = read(sys.argv[1])
time2, x2, y2 = read(sys.argv[2])

with open("merged.csv", "w") as f:
    writer = csv.writer(f, delimiter=",")
    writer.writerow(["Time", "X1", "Y1", "X2", "Y2"])
    for i in range(min(len(time1), len(time2))):
        writer.writerow([time1[i], x1[i], y1[i], x2[i], y2[i]])
