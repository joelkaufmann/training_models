#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import datetime
from azure.storage.filedatalake import DataLakeServiceClient
import io
import os
from dotenv import load_dotenv, find_dotenv
import numpy as np
#######################
# Page configuration
st.set_page_config(
    page_title="Sherpa Sensor Data",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #FFFFFF;
    text-align: center;
    padding: 15px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)



######################
# define sensors
vt_sensors = ['FEFFFFB71E5E54B1',
              'FEFFFFB71E5E54B2',
              'FEFFFFB71E5E54B3',
              'FEFFFFB71E5E54B4',
              'FEFFFFB71E5E54B5',
              'FEFFFFB71E5E54B6',
              'FEFFFFB71E5E54B7',
              'FEFFFFB71E5E54B8',
              'FEFFFFB71E5E54B9',
              'FEFFFFB71E5E54BA',
              'FEFFFFB71E5E54BB',
              'FEFFFFB71E5E54BC',
              'FEFFFFB71E5E54BD',
              'FEFFFFB71E5E54BE',
              'FEFFFFB71E5E54BF',
              'FEFFFFB71E5E54C0',
              'FEFFFFB71E5E54C1',
              'FEFFFFB71E5E54C2',
              'FEFFFFB71E5E54C3',
              'FEFFFFB71E5E54C4',
              'FEFFFFB71E5E54C5',
              'FEFFFFB71E5E54C6'
              ]
current_sensors = ['FEFFFFB71E5E54E1',
                   'FEFFFFB71E5E54E3',
                   'FEFFFFB71E5E54E4',
                   'FEFFFFB71E5E54E5'
                   ]
#######################
# Sidebar
start = datetime.date(2024, 3, 7)
end_min = start + datetime.timedelta(days=1)
today = datetime.datetime.today()
idx = (today.weekday() + 1) % 7
last_sunday = today - datetime.timedelta(idx)

with st.sidebar:
    st.title('Sherpa Sensor Data')

    #week_list = list(range(10, week + 1))

    #selected_week = st.selectbox('Select a week of data you want to inspect', week_list)
    start_date = st.date_input("start date", datetime.date(2024, 3, 7),
                                min_value=start, max_value=last_sunday - datetime.timedelta(days=1))
   
    end_date = st.date_input("end date", last_sunday, max_value=last_sunday, min_value=end_min)

    selected_sensors = '|'.join(st.multiselect('Select the sensors you want to analyze', 
                                      vt_sensors + current_sensors))
    select_metric = st.radio('select the metric you want to analyze', 
                             ['temperature', 'voltage', 'current'])
    filter = st.toggle('remove missed measurements ?', value=True)

#######################
# Plots

# Heatmap
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = alt.Chart(input_df).mark_rect().encode(
        y=alt.Y(f'{input_y}:O',
                axis=alt.Axis(title="Year", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
        x=alt.X(f'{input_x}:O', axis=alt.Axis(title="", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
        color=alt.Color(f'max({input_color}):Q',
                        legend=None,
                        scale=alt.Scale(scheme=input_color_theme)),
        stroke=alt.value('black'),
        strokeWidth=alt.value(0.25),
    ).properties(width=900
                 ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
    )
    # height=300
    return heatmap
# Box plot
def make_boxplot(input_df):
    fig = go.Figure()
    tmp_df = input_df.rename(columns=lambda x: x[16:])
    for column in tmp_df.columns:
        fig.add_trace(go.Box(y=tmp_df[column], name=column))

    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return fig
# Line plot
def make_lineplot(input_df):
    fig = go.Figure()
    tmp_df = input_df.rename(columns=lambda x: x[16:])
    for column in tmp_df.columns:
        fig.add_trace(go.Scatter(x=tmp_df.index, y=tmp_df[column], mode='lines', name=column))

    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=450
    )
    return fig
# Choropleth map
def make_choropleth(input_df, input_id, input_column, input_color_theme):
    choropleth = px.choropleth(input_df, locations=input_id, color=input_column, 
                               locationmode="USA-states",
                               color_continuous_scale=input_color_theme,
                               range_color=(0, max(df_selected_week.population)),
                               scope="usa",
                               labels={'population': 'Population'}
                               )
    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return choropleth
# Donut chart
def make_donut(input_response, input_text, input_color):
    if input_color == 'blue':
        chart_color = ['#29b5e8', '#155F7A']
    if input_color == 'green':
        chart_color = ['#27AE60', '#12783D']
    if input_color == 'orange':
        chart_color = ['#F39C12', '#875A12']
    if input_color == 'red':
        chart_color = ['#E74C3C', '#781F16']

    source = pd.DataFrame({
        "Package status": ['missed packages', input_text],
        "% value": [input_response, 100 - input_response]
    })
    # Define a custom color scale
    color_scale = alt.Scale(domain=['missed packages', input_text],
                            range=['#FF6666', '#6666FF'])

    plot = alt.Chart(source).mark_arc(innerRadius=80, cornerRadius=2).encode(
        theta=alt.Theta(field="% value", type="quantitative"),
        color=alt.Color(field="Package status", scale=color_scale),).properties(width=260, height=260)

    text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=50, fontWeight=700,
                          fontStyle="italic").encode(text=alt.value(f'{100-input_response} %'))

    return  plot + text



    selected_year_data = input_df[input_df['year'] == input_year].reset_index()
    previous_year_data = input_df[input_df['year'] == input_year - 1].reset_index()
    selected_year_data['population_difference'] = selected_year_data.population.sub(previous_year_data.population,
                                                                                    fill_value=0)
    return pd.concat([selected_year_data.states, selected_year_data.id, selected_year_data.population,
                      selected_year_data.population_difference], axis=1).sort_values(by="population_difference",
                                                                                     ascending=False)

_ = load_dotenv(find_dotenv())
key = os.getenv("AZURE_CONNECTION_STRING")
service_client = DataLakeServiceClient.from_connection_string(conn_str=key)

# Get the file system client
container_client = service_client.get_file_system_client(file_system="data-sherpa")
@st.cache_data
def download_csv_files(path, li=None, downloaded_files=None):
    if li is None:
        li = []
    if downloaded_files is None:
        downloaded_files = set()

    files = container_client.get_paths(path=path)

    for file in files:
        if file.name.endswith('.csv') and file.name not in downloaded_files:
            download = container_client.get_file_client(file.name).download_file()
            downloaded_bytes = download.readall()
            df = pd.read_csv(io.StringIO(downloaded_bytes.decode('utf-8'))).infer_objects()
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            li.append(df)
            downloaded_files.add(file.name)
        elif file.is_directory:
            download_csv_files(file.name, li, downloaded_files)
    return li
@st.cache_data
def create_one_df(list):
    new_li = []
    i=0
    j=1
    while i < len(list):
        new_df = pd.concat([list[i], list[j]], axis=1)
        new_li.append(new_df)
        i += 2
        j += 2
    df = new_li[0].combine_first(new_li[1])
    i =2

    while i < len(new_li):
        df = df.combine_first(new_li[i])

        i += 1
    return df
#######################
# Load data
loaded_df = create_one_df(download_csv_files("sensor_data/2024"))
df_reshaped = loaded_df
df_reshaped = df_reshaped.loc[(df_reshaped.index >= datetime.datetime.strptime(start_date.isoformat(), 
                                                                               '%Y-%m-%d')) & 
                              (df_reshaped.index <= datetime.datetime.strptime(end_date.isoformat(),
                                                                               '%Y-%m-%d'))]

#filter out the missed measurements
if select_metric == 'voltage':
    df_reshaped = df_reshaped.filter(regex='V_')
    if filter:
        df_reshaped = df_reshaped[df_reshaped < 0.09792]
    nan_name = 'NaN voltage'
elif select_metric == 'current':
    df_reshaped = df_reshaped.filter(regex='I_')
    if filter:
        df_reshaped = df_reshaped[df_reshaped < 48.96]
    nan_name = 'NaN current'
elif select_metric == 'temperature':
    df_reshaped = df_reshaped.filter(regex='T_')
    if filter:
        df_reshaped = df_reshaped[df_reshaped > -326.4]
    nan_name = 'NaN temperature'
else:
    nan_name = "NaN's"



#select the selected sensors
if len(selected_sensors) != 0:
    df_reshaped = df_reshaped.filter(regex=selected_sensors)
size_dataframe_widget = (len(df_reshaped.columns)+1) * 35

#######################
# Dashboard Main Panelcon

col = st.columns((1.5, 4.5, 2), gap='medium')

with col[0]:
    st.markdown('#### Data overview')

    #df_population_difference_sorted = calculate_population_difference(df_reshaped, selected_week)

    
    if select_metric == 'voltage':
        minimum = np.round(float(df_reshaped.min().min()), 4)
        mean = np.round(float(df_reshaped.mean().mean()), 4)
        maximum = np.round(float(df_reshaped.max().max()), 4)
    elif select_metric == 'current':
        minimum = np.round(float(df_reshaped.min().min()),2)
        mean = np.round(float(df_reshaped.mean().mean()), 2)
        maximum = np.round(float(df_reshaped.max().max()), 2)
    elif select_metric == 'temperature':
        minimum = np.round(float(df_reshaped.min().min()), 2)
        mean = np.round(float(df_reshaped.mean().mean()), 2)
        maximum = np.round(float(df_reshaped.max().max()), 2)
    else:
        minimum = '-'
        maximum = '-'
        mean = '-'
    st.metric(label='Minimum', value=minimum)
    st.metric(label='Mean', value=mean)
    st.metric(label='Maximum', value=maximum)

    is_nan = df_reshaped.isna().sum().sum()
    try:
        #Nans per day 288
        #Sensor wechsel = '2024-5-5' -> BA,B7 -> C5,C6
        sensor_change_date = datetime.date(2024, 5, 5)
        # remove the nans of the c5 and c6 sensors from overall nan count
        #if len(selected_sensors) == 0:

        if len(selected_sensors) == 0:    # remove the nans of ba and b7 sensors from overall nan count
            if start_date > sensor_change_date:
                nan_reduction = df_reshaped.filter(regex='54BA|54B7').isna().sum().sum()
                is_nan = is_nan - nan_reduction
            elif end_date < sensor_change_date:
                nan_reduction = df_reshaped.filter(regex='54C5|54C6').isna().sum().sum()
                is_nan = is_nan - nan_reduction
            elif start_date < sensor_change_date and end_date > sensor_change_date:
                bab7 = df_reshaped.loc[df_reshaped.index > pd.Timestamp(sensor_change_date)].filter(regex='BA|B7')
                bab7_nans = bab7.isna().sum().sum()
                c5c6 = df_reshaped.loc[df_reshaped.index < pd.Timestamp(sensor_change_date)].filter(regex='C5|C6')
                c5c6_nans = c5c6.isna().sum().sum()
                nan_reduction = bab7_nans + c5c6_nans
                is_nan = is_nan - nan_reduction
        else:
            selected_sensors_list = selected_sensors.split('|')
            if start_date > sensor_change_date:
                if 'FEFFFFB71E5E54BA' in selected_sensors_list or 'FEFFFFB71E5E54B7' in selected_sensors_list:
                    nan_reduction = df_reshaped.filter(regex='54BA|54B7').isna().sum().sum()
                    is_nan = is_nan - nan_reduction
            elif end_date < sensor_change_date:
                if 'FEFFFFB71E5E54C5' in selected_sensors_list or 'FEFFFFB71E5E54C6' in selected_sensors_list:
                    nan_reduction = df_reshaped.filter(regex='54C5|54C6').isna().sum().sum()
                    is_nan = is_nan - nan_reduction
            elif start_date < sensor_change_date and end_date > sensor_change_date:
                if 'FEFFFFB71E5E54BA' in selected_sensors_list or 'FEFFFFB71E5E54B7' in selected_sensors_list:
                    bab7 = df_reshaped.loc[df_reshaped.index > pd.Timestamp(sensor_change_date)].filter(regex='BA|B7')
                    bab7_nans = bab7.isna().sum().sum()
                    nan_reduction = bab7_nans
                    is_nan = is_nan - nan_reduction
                if 'FEFFFFB71E5E54C5' in selected_sensors_list or 'FEFFFFB71E5E54C6' in selected_sensors_list:
                    c5c6 = df_reshaped.loc[df_reshaped.index < pd.Timestamp(sensor_change_date)].filter(regex='C5|C6')
                    c5c6_nans = c5c6.isna().sum().sum()
                    nan_reduction = c5c6_nans
                    is_nan = is_nan - nan_reduction


        st.metric(label=nan_name, value=is_nan)
        st.markdown('#### Sensors efficiency')

        efficiency = int((is_nan/(df_reshaped.size)) * 100)

        donut_chart = make_donut(efficiency, 'Processed Packages', 'blue')
        st.altair_chart(donut_chart, use_container_width=True)
    except:
        st.metric(label=nan_name, value=is_nan)
        st.markdown('#### Sensors efficiency')

        efficiency = int((is_nan/(df_reshaped.size)) * 100)

        donut_chart = make_donut(efficiency, 'Processed Packages', 'blue')
        st.altair_chart(donut_chart, use_container_width=True)



with col[1]:
    st.markdown('#### Data visualization ' + select_metric)

    #if "df" not in st.session_state:
     #   st.session_state.df = df_reshaped

    #event = st.dataframe(st.session_state.df, key="data", on_select="rerun", selection_mode="multi-column",)



    fig1 = make_boxplot(df_reshaped)
    fig2 = make_lineplot(df_reshaped)

    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
    
with col[2]:
    st.markdown('#### Nan values by sensor')
    nan_df = df_reshaped
    nan_df.rename(columns=lambda x: x[16:], inplace=True)
    nan_values = nan_df.isna().sum()
    nan_values = pd.DataFrame(nan_values, columns=['nan_values'])
    nan_values.reset_index(inplace=True)
    nan_values.columns = ['sensor', 'nan_values']
    if (select_metric == 'temperature' or select_metric == 'voltage'):
        try:
            if len(selected_sensors) == 0:
                if end_date < sensor_change_date:
                    nan_values.at[20, 'nan_values'] = 0
                    nan_values.at[21, 'nan_values'] = 0
                    # remove the nans of ba and b7 sensors from overall nan count
                elif start_date > sensor_change_date:
                    nan_values.at[6, 'nan_values'] = 0
                    nan_values.at[9, 'nan_values'] = 0
                elif start_date < sensor_change_date and end_date > sensor_change_date:
                    ba_reduction = bab7.filter(regex='54BA').isna().sum()
                    b7_reduction = bab7.filter(regex='54B7').isna().sum()

                    nan_values.at[6, 'nan_values'] = nan_values.at[6, 'nan_values'] - ba_reduction
                    nan_values.at[9, 'nan_values'] = nan_values.at[9, 'nan_values'] - b7_reduction

                    c5_reduction = c5c6.filter(regex='54C5').isna().sum()
                    c6_reduction = c5c6.filter(regex='54C6').isna().sum()
                    nan_values.at[20, 'nan_values'] = nan_values.at[20, 'nan_values'] - c5_reduction
                    nan_values.at[21, 'nan_values'] = nan_values.at[21, 'nan_values'] - c6_reduction


                st.dataframe(nan_values, column_order=['sensor', 'nan_values'], hide_index=True, width=None, height=size_dataframe_widget,
                        column_config={'sensor': st.column_config.TextColumn('Sensor',),
                                        'nan_values': st.column_config.ProgressColumn('NaN values', format='%f', min_value=0,
                                                                                    max_value=len(nan_df),)})
            else:
                nan_values.set_index('sensor', inplace=True)
                if end_date < sensor_change_date:
                    if 'FEFFFFB71E5E54C5' in selected_sensors_list or 'FEFFFFB71E5E54C6' in selected_sensors_list:
                        nan_values.loc['C5', 'nan_values'] = 0
                        nan_values.loc['C6', 'nan_values'] = 0
                elif start_date > sensor_change_date:
                    if 'FEFFFFB71E5E54BA' in selected_sensors_list or 'FEFFFFB71E5E54B7' in selected_sensors_list:
                        nan_values.loc['BA', 'nan_values'] = 0
                        nan_values.loc['B7', 'nan_values'] = 0
                elif start_date < sensor_change_date and end_date > sensor_change_date:
                    if 'FEFFFFB71E5E54BA' in selected_sensors_list or 'FEFFFFB71E5E54B7' in selected_sensors_list:
                        if 'FEFFFFB71E5E54BA' in selected_sensors_list and 'FEFFFFB71E5E54B7' in selected_sensors_list:
                            ba_reduction = int(bab7.filter(regex='54BA').isna().sum())
                            nan_values.loc['BA', 'nan_values'] = nan_values.loc['BA', 'nan_values'] - ba_reduction
                            b7_reduction = int(bab7.filter(regex='54B7').isna().sum())
                            
                            nan_values.loc['B7', 'nan_values'] = nan_values.loc['B7', 'nan_values'] - b7_reduction
                        else:    
                            if 'FEFFFFB71E5E54BA' in selected_sensors_list:
                                ba_reduction = int(bab7.filter(regex='54BA').isna().sum())
                                nan_values.loc['BA', 'nan_values'] = nan_values.loc['BA', 'nan_values'] - ba_reduction
                            elif 'FEFFFFB71E5E54B7' in selected_sensors_list:
                            
                                b7_reduction = int(bab7.filter(regex='54B7').isna().sum())
                            
                                nan_values.loc['B7', 'nan_values'] = nan_values.loc['B7', 'nan_values'] - b7_reduction
                    if 'FEFFFFB71E5E54C5' in selected_sensors_list or 'FEFFFFB71E5E54C6' in selected_sensors_list:
                        if 'FEFFFFB71E5E54C5' in selected_sensors_list and 'FEFFFFB71E5E54C6' in selected_sensors_list:
                            c5_reduction = int(c5c6.filter(regex='54C5').isna().sum())
                            nan_values.loc['C5', 'nan_values'] = nan_values.loc['C5', 'nan_values'] - c5_reduction
                            c6_reduction = int(c5c6.filter(regex='54C6').isna().sum())
                            nan_values.loc['C6', 'nan_values'] = nan_values.loc['C6', 'nan_values'] - c6_reduction
                        else:
                            if 'FEFFFFB71E5E54C5' in selected_sensors_list:
                                c5_reduction = int(c5c6.filter(regex='54C5').isna().sum())
                                nan_values.loc['C5', 'nan_values'] = nan_values.loc['C5', 'nan_values'] - c5_reduction
                            elif 'FEFFFFB71E5E54C6' in selected_sensors_list:
                                c6_reduction = int(c5c6.filter(regex='54C6').isna().sum())
                            
                                nan_values.loc['C6', 'nan_values'] = nan_values.loc['C6', 'nan_values'] - c6_reduction
                nan_values.reset_index(inplace=True)
                st.dataframe(nan_values, column_order=['sensor', 'nan_values'], hide_index=True, width=None,
                            height=size_dataframe_widget,
                            column_config={'sensor': st.column_config.TextColumn('Sensor', ),
                                            'nan_values': st.column_config.ProgressColumn('NaN values', format='%f',
                                                                                        min_value=0,
                                                                                        max_value=len(nan_df), )})
        except:
            st.dataframe(nan_values, column_order=['sensor', 'nan_values'], hide_index=True, width=None, height=size_dataframe_widget,
                    column_config={'sensor': st.column_config.TextColumn('Sensor',),
                                    'nan_values': st.column_config.ProgressColumn('NaN values', format='%f', min_value=0,
                                                                                max_value=len(nan_df),)})

    