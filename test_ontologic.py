import io
from datetime import date
from typing import Any
import sys

from shiny import App, render, ui
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
from sklearn.linear_model import LinearRegression
import pandas as pd



def read_input_file1(infile):

    df = pd.read_csv(infile)

    try:
        df["start_day"] = pd.to_datetime([t.split()[0] if type(t) is str else np.nan for t in df["Start"]],  format='%m/%d/%y')
    except:
        df["start_day"] = pd.to_datetime([t.split()[0] if type(t) is str else np.nan for t in df["Start"]],  format='%Y/%m/%d')

    return df

def plot_type_diaper(df, title, outfile):
    fig, ax = plt.subplots(1,1)
    counts = df.groupby("End Condition")["Start"].count()  # count group members
    sns.barplot(x = counts.index, y = counts)
    plt.title(title)
    plt.xlabel("Count")
    plt.tight_layout()
    plt.savefig(outfile)

    return fig

def main():
    args = sys.argv
    infile = args[1]
    outfile = args[2]

    df = read_input_file1(infile)
    
    df = df[df["Type"] == "Diaper"]

    plot_type_diaper(df, "Types of diapers", outfile)


if __name__ == "__main__":
    main()