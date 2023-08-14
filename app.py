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
    # ui.row(
    #     make_example(
    #         "cum_dist",
    #         label="Download plot",
    #         title="Cumulative distribution",
    #         desc="Downloads a cumulative distribution of a variable",
    #         extra=[
    #             ui.input_select(
    #                 "var",
    #                 "Choose a variable:",
    #                 ["Diapers", "Breast Feeding", "Formula"]
    #             ),
    #             ui.output_plot("cum_dist_plot")
    #         ],
    #     ),
    # ),
)

def read_input_file1(input):
    file_info = input.file1()
    if not file_info:
        return None
    
    infile = file_info[0]["datapath"]
    df = pd.read_csv(infile)

    #df["start_day"] = pd.to_datetime([t.split()[0] if type(t) is str else np.nan for t in df["Start"]],  format='%m/%d/%y')
    #df["end_day"] = pd.to_datetime([t.split()[0] if type(t) is str else np.nan for t in df["End"]],  format='%m/%d/%y')

    return df

#def aggregate_by_day(df):



def server(input, output, session):    
    df = None

    @output
    @render.table
    def table():
        df = read_input_file1(input)
        if df is None:
            return
        return df

    @output
    @render.table 
    def summary():
        df = read_input_file1(input)
        if df is None:
            return
        return df.describe()
    

    @output
    @render.plot(alt="A histogram")
    def cumulative_diapers():
        file_info = input.file1()
        if not file_info:
            return
        
        infile = file_info[0]["datapath"]
        df = pl.read_csv(infile)

        np.random.seed(19680801)
        x = 100 + 15 * np.random.randn(437)

        fig, ax = plt.subplots()
        ax.hist(x, input.n(), density=True)

        return fig
    
    @session.download(filename="diaper_types.png")
    def diaper_types():

        df = read_input_file1(input)
        if df is None:
            return
        
        df = df[df["Type"] == "Diaper"]

        counts = df.groupby("End Condition")["Start"].count()  # count group members
        sns.barplot(x = counts.index, y = counts)
        plt.title(input.title())
        plt.xlabel("Count")

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

        counts = df.groupby("End Condition")["Start"].count()  # count group members
        sns.barplot(x = counts.index, y = counts)
        plt.title(input.title())
        plt.xlabel("Count")

    #Cumulative distribution of diapers, time spent breast feeding, oz of formula
    @session.download(filename="cum_dist.png")
    def cum_dist():

        df = read_input_file1(input)
        if df is None:
            return
        
        var = input.var()
        assert var in ["Diapers", "Breast Feeding", "Formula"]

        if var == "Diapers":
            df = df.filter(pl.col("Type") == "Diaper")
        elif var == "Breast Feeding":
            df = df.filter((pl.col("Type") == "Feed") & 
                           (pl.col("Start Condition") == "Breast Milk"))
        else:
            df = df.filter((pl.col("Type") == "Feed") & 
                           (pl.col("Start Condition") == "Formula")) #TODO: check to make sure this is what huckleberry does

        #df_day = aggregate_by_day(df)


        counts = df.groupby("End Condition").agg(
            pl.col("Start").count().alias("count"),  # count group members, assumes that start date/time is unique for each entry
        )

        #polars doesn't work with seaborn yet
        x = counts.select(pl.col('End Condition')).to_numpy().ravel()
        y = counts.select(pl.col('count')).to_numpy().ravel()
        
        sns.barplot(x = x, y = y)
        plt.title(input.title())
        plt.xlabel("Count")

        with io.BytesIO() as buf:
            plt.savefig(buf, format="png")
            yield buf.getvalue()

    @output
    @render.plot(alt="A histogram")
    def cum_dist_plot():
        df = read_input_file1(input)
        if df is None:
            return
        
        df = df.filter(pl.col("Type") == "Diaper")

        counts = df.groupby("End Condition").agg(
            pl.col("Start").count().alias("count"),  # count group members, assumes that start date/time is unique for each entry
        )

        #polars doesn't work with seaborn yet
        x = counts.select(pl.col('End Condition')).to_numpy().ravel()
        y = counts.select(pl.col('count')).to_numpy().ravel()
        
        sns.barplot(x = x, y = y)
        plt.title(input.title())
        plt.xlabel("Count")

    #Regression of time nursing & hours slept / oz of formula & hours slept

    #PCA plot of daily summary colored by number of hours slept
    #Make interactive plotly so that can see feature values

app = App(app_ui, server)