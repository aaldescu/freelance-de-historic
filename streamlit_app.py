import pandas as pd
import os
import streamlit as st
from datetime import timedelta
import math

def safe_divide_and_ceil(numerator, denominator):
    if denominator == 0:  # Check for division by zero
        return 0  # Or None, or any other value you deem appropriate
    else:
        result = numerator / denominator
        #return math.ceil(result)
        return round(result,2)
    
project_path = os.path.dirname(os.path.realpath(__file__))

# HTML code for the "Buy Me A Coffee" button
buy_me_a_coffee_html = """
<a href="https://www.buymeacoffee.com/aldescu_projects" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" 
    height="50" width="128">
</a>
"""

# Define the file paths (or names if they are in the same directory)
file_names = ['freelance_data.csv', 'freelancermap_project_data.csv', 'project_data.csv']
file_paths = [os.path.join(project_path, file_name) for file_name in file_names]

# Use comprehension to read each file into a DataFrame, adding a source column, and store them in a list
data_frames = [pd.read_csv(file, sep=';').assign(source=os.path.basename(file)) for file in file_paths]

# Concatenate all DataFrames in the list into a single DataFrame
df = pd.concat(data_frames, ignore_index=True)

#Streamlit Dashboard

# Convert date column to datetime
df['date'] = pd.to_datetime(df['date']).dt.floor('D')

# Sidebar 
st.sidebar.header('Filters')

# Date Slider
min_date, max_date = df['date'].min().date(), df['date'].max().date()

week_ago_date = max_date - timedelta(days=7)

selected_date_range = st.sidebar.slider("Select Date Range:", 
                                        min_value=week_ago_date, 
                                        max_value=max_date, 
                                        value=(week_ago_date, max_date)
                                       )

# Job Group Multiselect
job_groups = df['job_group'].unique()
selected_job_groups = st.sidebar.multiselect("Select Job Groups:", job_groups, default=["Jira", "Java","SQL","Python","Javascript","ERP / CRM Systeme", "SAP", "Web", "Softwareentwicklung / -programmierung"])

# Filter data based on selections
# Convert selected_date_range to pandas timestamps
start_date, end_date = pd.to_datetime(selected_date_range[0]), pd.to_datetime(selected_date_range[1])

filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
filtered_df = filtered_df[filtered_df['job_group'].isin(selected_job_groups)]

#Split data soruce into job and expert
job_filtered_df = filtered_df[ filtered_df['source'].isin(['freelancermap_project_data.csv', 'project_data.csv'])]
expert_filtered_df = filtered_df[ filtered_df['source'].isin(['freelance_data.csv'])]

# Preparing data for the line chart
job_pivot_df = job_filtered_df.pivot_table(index='date', columns='job_group', values='num_jobs', aggfunc='sum').fillna(0)
expert_pivot_df = expert_filtered_df.pivot_table(index='date', columns='job_group', values='num_jobs', aggfunc='sum').fillna(0)

# Data for Experts / Jobs Ratio
df_pivot = filtered_df.pivot_table(index=["job_group", "date"], columns="source", values="num_jobs").fillna(0).reset_index()
df_pivot["experts"] = df_pivot["freelance_data.csv"]+df_pivot["freelancermap_project_data.csv"]
df_pivot = df_pivot.drop(columns=["freelance_data.csv","freelancermap_project_data.csv"])
# Apply the function for safe division and rounding up
df_pivot["ratio"] = df_pivot.apply(lambda row: safe_divide_and_ceil(row["experts"], row["project_data.csv"]), axis=1)
expert_ratio_df = df_pivot.pivot_table(index='date', columns='job_group', values='ratio', aggfunc='sum').fillna(0)


# Calculate the daily differences for jobs
job_daily_diff = job_pivot_df.diff().fillna(0)  # Calculate day-to-day difference and fill NaN with 0

# Calculate the daily differences for experts
expert_daily_diff = expert_pivot_df.diff().fillna(0)  # Similar calculation for experts


st.title('Germany\'s freelancer market in daily numbers')
st.markdown(buy_me_a_coffee_html, unsafe_allow_html=True)

st.header('Jobs :money_with_wings:')
# Plotting with st.line_chart
st.line_chart(job_pivot_df)

st.header('Field Commpetition trend :sunglasses:')
st.line_chart(expert_ratio_df)

# Visualize the daily differences
st.header('Daily Difference in Jobs :chart_with_upwards_trend:')
st.bar_chart(job_daily_diff)

st.header('Daily Difference in Experts :chart_with_upwards_trend:')
st.bar_chart(expert_daily_diff)


#
df_topcomp = df.pivot_table(index=["job_group", "date"], columns="source", values="num_jobs").fillna(0).reset_index()
df_topcomp["experts"] = df_topcomp["freelance_data.csv"]+df_topcomp["freelancermap_project_data.csv"]
df_topcomp = df_topcomp.drop(columns=["freelance_data.csv","freelancermap_project_data.csv"])
# Apply the function for safe division and rounding up
df_topcomp["ratio"] = df_topcomp.apply(lambda row: safe_divide_and_ceil(row["experts"], row["project_data.csv"]), axis=1)

#
abc = df_topcomp.groupby('job_group')['ratio'].mean().round().reset_index()
abc = abc.sort_values(by="ratio", ascending=False)
st.write(abc)