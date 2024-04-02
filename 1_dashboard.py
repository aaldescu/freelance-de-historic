import streamlit as st
import pandas as pd
import os
 
st.title('Germany Freelancer Market Visualizer')
 
project_path = os.path.dirname(os.path.realpath(__file__)) + "/"

df = pd.read_csv(project_path + "project_data.csv", sep=';')
freelance_df = pd.read_csv(project_path + "freelance_data.csv", sep=';')
freelancermap_prj_df = pd.read_csv(project_path + "freelancermap_project_data.csv", sep=';')
freelancermap_person_df= ""

# FRELANCE.DE 
#
job_group_options = st.multiselect(
    'Job Groups',
    df["job_group"].unique().tolist(),["ERP / CRM Systeme", "SAP", "Web", "Softwareentwicklung / -programmierung"])

filtered_df  = df[df['job_group'].isin(job_group_options)]
filtered_freelancedf = freelance_df[freelance_df['job_group'].isin(job_group_options)]

filtered_df = filtered_df.reset_index()

filtered_freelancedf = filtered_freelancedf.reset_index()

if not filtered_df.empty:
    st.line_chart(filtered_df, x="date",y="num_jobs", color="job_group")
    st.line_chart(filtered_freelancedf, x="date",y="num_jobs", color="job_group")
    st.area_chart(filtered_df, x="date", y="num_jobs", color="job_group")
else:
    filtered_df = df

with st.expander('Freelance.de Table Preview'):
    st.dataframe(filtered_df)
    st.dataframe(filtered_freelancedf)

# FRELANCERMAP.DE 
#
fm_job_group_options = st.multiselect(
    'Job Groups',
    freelancermap_prj_df["job_group"].unique().tolist(),["Jira", "Java","SQL","Python","Javascript"])

filtered_fm_df  = freelancermap_prj_df[freelancermap_prj_df['job_group'].isin(fm_job_group_options)]

filtered_fm_df = filtered_fm_df.reset_index()

if not filtered_fm_df.empty:
    st.line_chart(filtered_fm_df, x="date",y="num_jobs", color="job_group")

else:
    filtered_df = freelancermap_prj_df
    


with st.expander('Freelancermap.de Table Preview'):
    st.dataframe(freelancermap_prj_df)

