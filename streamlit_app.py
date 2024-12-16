import pandas as pd
import os
import streamlit as st
from datetime import timedelta
import math
import altair as alt
import sqlite3

def safe_divide_and_ceil(numerator, denominator):
    if denominator == 0:  # Check for division by zero
        return 0  # Or None, or any other value you deem appropriate
    else:
        result = numerator / denominator
        return round(result, 2)
    
project_path = os.path.dirname(os.path.realpath(__file__))

# HTML code for the "Buy Me A Coffee" button
buy_me_a_coffee_html = """
<a href="https://www.buymeacoffee.com/aldescu_projects" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" 
    height="50" width="180">
</a>
"""

# Connect to SQLite database
conn = sqlite3.connect(os.path.join(project_path, 'freelance_projects.db'))

# Read data from both tables
projects_df = pd.read_sql_query("""
    SELECT 
        date,
        category as job_group,
        num_jobs
    FROM projects
""", conn)

freelancers_df = pd.read_sql_query("""
    SELECT 
        date,
        category as job_group,
        num_freelancers
    FROM freelances
""", conn)

# Convert date columns to datetime
projects_df['date'] = pd.to_datetime(projects_df['date']).dt.floor('D')
freelancers_df['date'] = pd.to_datetime(freelancers_df['date']).dt.floor('D')

# Sidebar 
st.sidebar.header('Filters')

# Date Slider - use projects date range since that's what we're primarily interested in
min_date, max_date = projects_df['date'].min().date(), projects_df['date'].max().date()

_ago_date = max_date - timedelta(days=90)

selected_date_range = st.sidebar.slider("Select Date Range:", 
                                      min_value=min_date, 
                                      max_value=max_date, 
                                      value=(_ago_date, max_date)
                                     )

# Job Group Multiselect - use unique categories from projects
job_groups = projects_df['job_group'].unique()
selected_job_groups = st.sidebar.multiselect("Select Job Groups:", job_groups, default=["SQL","ERP / CRM Systeme", "SAP", "Web", "Softwareentwicklung / -programmierung"])

# Filter data based on selections
start_date, end_date = pd.to_datetime(selected_date_range[0]), pd.to_datetime(selected_date_range[1])

filtered_projects = projects_df[
    (projects_df['date'] >= start_date) & 
    (projects_df['date'] <= end_date) &
    (projects_df['job_group'].isin(selected_job_groups))
]

filtered_freelancers = freelancers_df[
    (freelancers_df['date'] >= start_date) & 
    (freelancers_df['date'] <= end_date) &
    (freelancers_df['job_group'].isin(selected_job_groups))
]

# Preparing data for the line charts
job_pivot_df = filtered_projects.pivot_table(
    index='date', 
    columns='job_group', 
    values='num_jobs', 
    aggfunc='sum'
).fillna(0)

expert_pivot_df = filtered_freelancers.pivot_table(
    index='date', 
    columns='job_group', 
    values='num_freelancers', 
    aggfunc='sum'
).fillna(0)

# Data for Experts / Jobs Ratio
merged_df = pd.merge(
    filtered_projects.groupby(['date', 'job_group'])['num_jobs'].sum().reset_index(),
    filtered_freelancers.groupby(['date', 'job_group'])['num_freelancers'].sum().reset_index(),
    on=['date', 'job_group'],
    how='outer'
).fillna(0)

merged_df['ratio'] = merged_df.apply(
    lambda row: safe_divide_and_ceil(row['num_freelancers'], row['num_jobs']), 
    axis=1
)

expert_ratio_df = merged_df.pivot_table(
    index='date', 
    columns='job_group', 
    values='ratio', 
    aggfunc='sum'
).fillna(0)

# Calculate the daily differences for jobs
job_daily_diff = job_pivot_df.diff().fillna(0)  # Calculate day-to-day difference and fill NaN with 0

# Calculate the daily differences for experts
expert_daily_diff = expert_pivot_df.diff().fillna(0)  # Similar calculation for experts

st.title('Germany\'s freelancer market in daily numbers')
st.markdown(buy_me_a_coffee_html, unsafe_allow_html=True)

st.header('Jobs :money_with_wings:')

# Plotting with st.altair_chart to rotate labels
job_chart = alt.Chart(job_pivot_df.reset_index().melt('date')).mark_line().encode(
    x=alt.X('date:T', axis=alt.Axis(labelAngle=45)), 
    y='value:Q', 
    color='job_group:N'
).properties(
    width=800,
    height=400
)

st.altair_chart(job_chart)

st.header('Experts per Job :sunglasses:')
expert_ratio_chart = alt.Chart(expert_ratio_df.reset_index().melt('date')).mark_line().encode(
    x=alt.X('date:T', axis=alt.Axis(labelAngle=45)), 
    y='value:Q', 
    color='job_group:N'
).properties(
    width=800,
    height=400
)

st.altair_chart(expert_ratio_chart)

# Visualize the daily differences
st.header('Daily Difference in Jobs :chart_with_upwards_trend:')
daily_diff_chart_jobs = alt.Chart(job_daily_diff.reset_index().melt('date')).mark_bar().encode(
    x=alt.X('date:T', axis=alt.Axis(labelAngle=45)), 
    y='value:Q', 
    color='job_group:N'
).properties(
    width=800,
    height=400
)

st.altair_chart(daily_diff_chart_jobs)

st.header('Daily Difference in Experts :chart_with_upwards_trend:')
daily_diff_chart_experts = alt.Chart(expert_daily_diff.reset_index().melt('date')).mark_bar().encode(
    x=alt.X('date:T', axis=alt.Axis(labelAngle=45)), 
    y='value:Q', 
    color='job_group:N'
).properties(
    width=800,
    height=400
)

st.altair_chart(daily_diff_chart_experts)

# Top competition calculation
df_topcomp = merged_df.copy()
df_topcomp = df_topcomp.groupby('job_group')['ratio'].mean().round().reset_index()
df_topcomp = df_topcomp.sort_values(by="ratio", ascending=False)
st.write(df_topcomp)

# Close database connection
conn.close()
