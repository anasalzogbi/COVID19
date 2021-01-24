import urllib

import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import numpy as np

@st.cache
def get_UN_data():
    AWS_BUCKET_URL = "https://streamlit-demo-data.s3-us-west-2.amazonaws.com"
    df = pd.read_csv(AWS_BUCKET_URL + "/agri.csv.gz")
    return df.set_index("Region")

@st.cache
def get_corona_data(day):
    corona_df = pd.read_excel('https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide.xlsx')
    corona_df.columns = ['DateRep', 'Day', 'Month', 'Year', 'Cases', 'Deaths', 'Country', 'GeoId', 'co_code', 'pop', 'continentExp', 'cumm_num']
    corona_df.sort_values('DateRep', inplace=True)
    return corona_df


try:
    day = datetime.datetime.date(datetime.datetime.now())
    df = get_corona_data(day)
except urllib.error.URLError as e:
    st.error(
        """
        **This demo requires internet access.**

        Connection error: %s
    """
        % e.reason
    )
sort_type = st.sidebar.selectbox("Sort countries by", [ 'Total number of cases', 'Number of daily cases',
                                                        'Total number of deaths', 'Number of daily deaths',
                                                        'cases/population', 'deaths/population', 'deaths/cases'])
if sort_type in ["Number of daily cases",  'Number of daily deaths', 'cases/population', 'deaths/population', 'deaths/cases']:
    last_k_days = st.sidebar.number_input("Number of days", min_value=1, max_value = df.DateRep.nunique(), step=1)

top_k = int(st.sidebar.text_input("Number of countries", '4'))

co_list = df[df.Deaths>100].groupby('co_code').sum().sort_values('Deaths', ascending=False).index.unique()

selected_countries= df.groupby('Country').Cases.sum().sort_values(ascending=False)[0:top_k].index.to_list()
if sort_type == 'Number of daily cases':
    selected_countries = df.groupby('Country').Cases.mean().sort_values(ascending=False)[0:top_k].index.to_list()
elif sort_type == 'Total number of cases':
    selected_countries = df.groupby('Country').Cases.sum().sort_values(ascending=False)[0:top_k].index.to_list()
elif sort_type == 'Number of daily deaths':
    selected_countries = df.groupby('Country').Deaths.mean().sort_values(ascending=False)[0:top_k].index.to_list()
elif sort_type == 'Total number of deaths':
    selected_countries = df.groupby('Country').Deaths.sum().sort_values(ascending=False)[0:top_k].index.to_list()
elif sort_type =='cases/population':
    df_temp = df[df.DateRep>=df.DateRep-datetime.TimeDelta(days=last_k_days)]
    #selected_countries = df_temp.groupby('Country').Cases.sum()/.sort_values(ascending=False)[0:top_k].index.to_list()

cum = st.sidebar.checkbox('Cummulative values', True)
log = st.sidebar.checkbox('Log scale', False)
date_input = np.datetime64(st.sidebar.date_input("Data from:", datetime.date(year=2020, month=3, day=1)))

countries = st.sidebar.multiselect(
    "Choose countries", list(df.Country.unique()), selected_countries)
if not countries:
    st.error("Please select at least one country.")



def plot_country(df, countries, window_size=2, cum = False, log = False):
    # Create traces
    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.05, subplot_titles=("Cases", "Deaths", 'Deaths/pop', "Ratio"))
    for i,c in enumerate(countries):
        df_plot = df.loc[((df.Country==c))].sort_values('DateRep')
        df_plot['ratio']= df_plot.Deaths/df_plot.Cases

        if cum:
            fig.add_trace(go.Scatter(x=df_plot.DateRep, y=df_plot.Cases.cumsum(), mode='lines+markers', name=f'Cases-{c}', line=dict(color=px.colors.qualitative.Dark24[i]), showlegend=False), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=df_plot.DateRep, y=df_plot.Cases, mode='lines+markers', name=f'Cases - {c}',
                                     line=dict(color=px.colors.qualitative.Dark24[i]), showlegend=False), row=1, col=1)
        fig.update_yaxes(type=("log" if log else "linear"), row=1, col=1)
        if cum:
            fig.add_trace(go.Scatter(x=df_plot.DateRep, y=df_plot.Deaths.cumsum(), mode='lines+markers', name=f'Deaths-{c}', line=dict(color=px.colors.qualitative.Dark24[i]), showlegend=False), row=2, col=1)
        else:
            fig.add_trace(go.Scatter(x=df_plot.DateRep, y=df_plot.Deaths, mode='lines+markers', name=f'Deaths - {c}',
                                     line=dict(color=px.colors.qualitative.Dark24[i]), showlegend=False), row=2, col=1)
        fig.update_yaxes(type=("log" if log else "linear"), row=2, col=1)
        if cum:
            fig.add_trace(go.Scatter(x=df_plot.DateRep, y=df_plot.Deaths.cumsum()/df_plot['pop'], mode='lines+markers', name=f'D/pop - {c}', line=dict(color=px.colors.qualitative.Dark24[i]), showlegend=False), row=3, col=1)
        else:
            fig.add_trace(
                go.Scatter(x=df_plot.DateRep, y=df_plot.Deaths / df_plot['pop'], mode='lines+markers',
                           name=f'D/pop - {c}', line=dict(color=px.colors.qualitative.Dark24[i]), showlegend=False),
                row=3, col=1)
        fig.update_yaxes(type=("log" if log else "linear"), row=3, col=1)
        if cum:
            fig.add_trace(go.Scatter(x=df_plot.DateRep, y=(df_plot.Deaths.cumsum()/df_plot.Cases.cumsum()).rolling(window_size,center=True).mean(), mode='lines+markers', name=c, line=dict(color=px.colors.qualitative.Dark24[i])), row=4, col=1)
        else:
            fig.add_trace(go.Scatter(x=df_plot.DateRep, y=df_plot.ratio.rolling(window_size,center=True).mean(), mode='lines+markers', name=c, line=dict(color=px.colors.qualitative.Dark24[i])), row=4, col=1)
        fig.update_yaxes(type=("log" if log else "linear"), row=4, col=1)
    if False:
        fig.add_trace(
            go.Scatter(x=df_plot.DateRep, y=df_plot.ratio.rolling(window_size, center=True).mean(), mode='lines+markers',
                       name=c, line=dict(color=px.colors.qualitative.Dark24[i])), row=4, col=1)

    fig.update_yaxes(type=("log" if log else "linear"), row=4, col=1)
    fig.update_layout(
        autosize=True,
        width=1100,
        height=700,
        legend={'traceorder': 'grouped'},
        legend_itemclick= False,
        
        legend_itemdoubleclick=False,
        xaxis_tickformat='%d %B (%a)<br>%Y'
    )
    return fig
#co_list = df[df.Deaths>100].groupby('co_code').sum().sort_values('Deaths', ascending=False).index.unique()
df = df[df.DateRep>date_input]
fig = plot_country(df, countries, cum = cum, log=log)
st.plotly_chart(fig)
