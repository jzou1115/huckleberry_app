import io
from datetime import date
from typing import Any

from shiny import App, render, ui
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
from sklearn.linear_model import LinearRegression
import pandas as pd

def make_example(id: str, label: str, title: str, desc: str, extra: Any = None):
    return ui.column(
        4,
        ui.div(
            {"class": "card mb-4"},
            ui.div(title, class_="card-header"),
            ui.div(
                {"class": "card-body"},
                ui.p(desc, class_="card-text text-muted"),
                extra,
                ui.download_button(id, label, class_="btn-primary")
            ),
        ),
    )

app_ui = ui.page_fluid(
    ui.input_file("file1", "Choose a file to upload:", multiple=False),
    ui.h3("Summary of data", class_="mt-2"),
    ui.output_table("summary"),
    ui.h3("Plots", class_="mt-2"),
    ui.row(
        make_example(
            "diaper_types",
            label="Download plot",
            title="Types of Diapers",
            desc="Downloads a bar plot of types of diapers generated",
            extra=[
                ui.input_text("title", "Plot title", "Types of Diapers"),
                ui.output_plot("diaper_types_plot")
            ],
        ),
    ),
    ui.row(
        make_example(
            "cum_dist",
            label="Download plot",
            title="Cumulative distribution",
            desc="Downloads a cumulative distribution of a variable",
            extra=[
                ui.input_select(
                    "var",
                    "Choose a variable:",
                    ["Diapers", "Breast Feeding", "Bottle"]
                ),
                ui.output_plot("cum_dist_plot")
            ],
        ),
    ),
)

def read_input_file1(input):
    file_info = input.file1()
    if not file_info:
        return None
    
    infile = file_info[0]["datapath"]
    df = pd.read_csv(infile)

    df["start_day"] = pd.to_datetime([t.split()[0] if type(t) is str else np.nan for t in df["Start"]],  format='%m/%d/%y')
    #df["end_day"] = pd.to_datetime([t.split()[0] if type(t) is str else np.nan for t in df["End"]],  format='%m/%d/%y')

    return df

def plot_type_diaper(df, title):
    fig, ax = plt.subplots(1,1)
    counts = df.groupby("End Condition")["Start"].count()  # count group members
    sns.barplot(x = counts.index, y = counts)
    plt.title(title)
    plt.xlabel("Count")
    return fig

def plot_cum_dist(df, var):
    fig, ax = plt.subplots(1,1)

    assert var in ["Diapers", "Breast Feeding", "Bottle"]

    if var == "Diapers":
        df = df[df["Type"]=="Diaper"]
        sns.ecdfplot(data = df, x = "start_day", stat="count")
        #sns.histplot(data = df,  x = "start_day", stat="count", cumulative=True, alpha=.4)
    elif var == "Breast Feeding":
        df = df[(df["Type"]=="Feed") & (df["Start Location"] != "Bottle")]
        df["nurse_hours"] = [float(v.split(":")[0]) if type(v) == str else 0 for v in df["Duration"]]
        df["nurse_min"] = [float(v.split(":")[1]) if type(v) == str else 0 for v in df["Duration"]]
        df["nurse_time"] = 60*df["nurse_hours"] + df["nurse_min"]
        df = df.sort_values(by="start_day")
        cum_nurse_time = []
        total = 0
        for t in df["nurse_time"]:
            total = total + t
            cum_nurse_time.append(total)
        df["cum_nurse_time"] = cum_nurse_time
        sns.lineplot(data = df, x = "start_day", y = cum_nurse_time)
        plt.ylabel("Time nursing (min)")
        #sns.histplot(data = df,  x = "start_day", y = "nurse_time", stat="count", cumulative=True, alpha=.4)
    else:
        df = df[(df["Type"]=="Feed") & (df["Start Location"] == "Bottle")]#TODO: check to make sure this is what huckleberry does
        df["oz"] = [float(v[:-2]) if type(v) == str else 0 for v in df["End Condition"]]
        
        df = df.sort_values(by="start_day")
        cum_oz = []
        total = 0
        for t in df["oz"]:
            total = total + t
            cum_oz.append(total)

        df["cum_oz"] = cum_oz
        sns.lineplot(data = df, x = "start_day", y = cum_oz)
        plt.ylabel("Oz of formula or breast milk")
    plt.xticks(rotation=90)

    return fig

#def aggregate_by_start_day(df):



def server(input, output, session):    

    @output
    @render.table 
    def summary():
        file_info = input.file1()
        if not file_info:
            return
        
        infile = file_info[0]["datapath"]
        df = pl.read_csv(infile)

        return df.describe()
    
    
    @session.download(filename="diaper_types.png")
    def diaper_types():

        df = read_input_file1(input)
        if df is None:
            return
        
        df = df[df["Type"] == "Diaper"]

        plot_type_diaper(df, input.title())

        with io.BytesIO() as buf:
            plt.savefig(buf, format="png")
            yield buf.getvalue()

    @output
    @render.plot(alt="A histogram")
    def diaper_types_plot():
        df = read_input_file1(input)
        if df is None:
            return
        
        df = df[df["Type"] == "Diaper"]

        plot_type_diaper(df, input.title())

    #Cumulative distribution of diapers, time spent breast feeding, oz of formula
    @session.download(filename="cum_dist.png")
    def cum_dist():

        df = read_input_file1(input)
        if df is None:
            return
        
        var = input.var()

        plot_cum_dist(df, var)

        with io.BytesIO() as buf:
            plt.savefig(buf, format="png")
            yield buf.getvalue()

    @output
    @render.plot(alt="A histogram")
    def cum_dist_plot():
        df = read_input_file1(input)
        if df is None:
            return
        
        var = input.var()

        plot_cum_dist(df, var)

    #Regression of time nursing & hours slept / oz of formula & hours slept

    #PCA plot of daily summary colored by number of hours slept
    #Make interactive plotly so that can see feature values

app = App(app_ui, server)