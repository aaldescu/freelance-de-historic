#!/usr/bin/env python
"""
Generate reports analyzing the German freelance market based on MySQL data.
This script creates various reports including:
- Top categories for new jobs
- Trending jobs and categories over time
- Category groupings and job counts per group
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import numpy as np
from db_utils import get_mysql_connection
import re
from pathlib import Path

# Set style for plots
plt.style.use('fivethirtyeight')
sns.set_palette("Set2")

# Create reports directory if it doesn't exist
REPORTS_DIR = Path(__file__).parent / 'reports'
FIGURES_DIR = REPORTS_DIR / 'figures'
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# Category groupings for analysis
CATEGORY_GROUPS = {
    'Development': [
        'Java', 'Python', 'C#', 'C++', '.NET', 'PHP', 'JavaScript', 'TypeScript',
        'React', 'Angular', 'Vue', 'Node.js', 'Full-Stack', 'Frontend', 'Backend',
        'Mobile', 'iOS', 'Android', 'Swift', 'Kotlin', 'Flutter', 'React Native',
        'DevOps', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Cloud',
        'Entwickler', 'Entwicklung', 'Software', 'Web', 'App', 'Mobile', 'Programmierung'
    ],
    'Data': [
        'Data', 'Analytics', 'Business Intelligence', 'BI', 'Tableau', 'Power BI',
        'SQL', 'Database', 'Datenbank', 'ETL', 'Data Warehouse', 'Data Lake',
        'Big Data', 'Hadoop', 'Spark', 'Data Science', 'Machine Learning', 'ML',
        'AI', 'Artificial Intelligence', 'Deep Learning', 'NLP', 'Natural Language',
        'Data Engineer', 'Data Analyst', 'Data Scientist', 'Statistik', 'Daten'
    ],
    'Management': [
        'Project', 'Projekt', 'Management', 'Manager', 'PMO', 'Scrum', 'Agile',
        'Product Owner', 'PO', 'Scrum Master', 'Kanban', 'Lean', 'Projektleiter',
        'Projektmanager', 'Projektleitung', 'Führung', 'Lead', 'Leitung'
    ],
    'Design': [
        'Design', 'UX', 'UI', 'User Experience', 'User Interface', 'Graphic',
        'Grafik', 'Visual', 'Creative', 'Kreativ', 'Illustration', 'Animation',
        'Video', 'Media', 'Medien', '3D', 'CAD'
    ],
    'Infrastructure': [
        'System', 'Network', 'Netzwerk', 'Security', 'Sicherheit', 'Admin',
        'Administrator', 'IT-Administration', 'Support', 'Helpdesk', 'Service Desk',
        'Infrastructure', 'Infrastruktur', 'Server', 'Hardware', 'Virtualization',
        'VMware', 'Hyper-V', 'Windows', 'Linux', 'Unix'
    ],
    'SAP': [
        'SAP', 'ABAP', 'S/4HANA', 'ERP', 'FI', 'CO', 'MM', 'SD', 'PP', 'HCM',
        'CRM', 'BW', 'BI', 'Fiori', 'HANA'
    ],
    'Testing': [
        'Test', 'QA', 'Quality Assurance', 'Qualitätssicherung', 'Testing',
        'Tester', 'Selenium', 'Cypress', 'Automation', 'Automatisierung'
    ],
    'Consulting': [
        'Consulting', 'Beratung', 'Berater', 'Consultant', 'Strategy', 'Strategie',
        'Business', 'Geschäft', 'Process', 'Prozess', 'Optimization', 'Optimierung'
    ],
    'Marketing': [
        'Marketing', 'SEO', 'SEA', 'SEM', 'Social Media', 'Content', 'Online Marketing',
        'Digital Marketing', 'E-Commerce', 'Ecommerce', 'CRM', 'Customer', 'Kunde'
    ]
}

def fetch_data():
    """Fetch data from MySQL database."""
    conn = get_mysql_connection()
    try:
        # Fetch projects data
        projects_df = pd.read_sql("""
            SELECT date, category, num, href 
            FROM projects 
            ORDER BY date DESC
        """, conn)
        
        # Fetch freelances data
        freelances_df = pd.read_sql("""
            SELECT date, category, num, href 
            FROM freelances 
            ORDER BY date DESC
        """, conn)
        
        # Convert date strings to datetime objects
        projects_df['date'] = pd.to_datetime(projects_df['date'])
        freelances_df['date'] = pd.to_datetime(freelances_df['date'])
        
        # Convert num to integer
        projects_df['num'] = pd.to_numeric(projects_df['num'], errors='coerce').fillna(0).astype(int)
        freelances_df['num'] = pd.to_numeric(freelances_df['num'], errors='coerce').fillna(0).astype(int)
        
        return projects_df, freelances_df
    
    finally:
        conn.close()

def assign_category_group(category):
    """Assign a category to a group based on keywords."""
    category_lower = category.lower()
    
    for group, keywords in CATEGORY_GROUPS.items():
        for keyword in keywords:
            if keyword.lower() in category_lower:
                return group
    
    return 'Other'

def generate_top_categories_report(projects_df, freelances_df):
    """Generate report on top categories for projects and freelancers."""
    print("Generating top categories report...")
    
    # Get the most recent date in the data
    latest_date = projects_df['date'].max()
    
    # Filter for the most recent date
    latest_projects = projects_df[projects_df['date'] == latest_date]
    
    # Get top 20 categories by number of projects
    top_projects = latest_projects.sort_values('num', ascending=False).head(20)
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    bars = plt.barh(top_projects['category'], top_projects['num'], color=sns.color_palette("viridis", 20))
    plt.xlabel('Number of Projects')
    plt.ylabel('Category')
    plt.title(f'Top 20 Project Categories (as of {latest_date.strftime("%Y-%m-%d")})')
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'top_project_categories.png', dpi=300)
    plt.close()
    
    # Write to CSV
    top_projects.to_csv(REPORTS_DIR / 'top_project_categories.csv', index=False)
    
    # If freelances data is available, create a similar report
    if not freelances_df.empty:
        latest_date_freelancers = freelances_df['date'].max()
        latest_freelancers = freelances_df[freelances_df['date'] == latest_date_freelancers]
        top_freelancers = latest_freelancers.sort_values('num', ascending=False).head(20)
        
        plt.figure(figsize=(12, 8))
        plt.barh(top_freelancers['category'], top_freelancers['num'], color=sns.color_palette("viridis", 20))
        plt.xlabel('Number of Freelancers')
        plt.ylabel('Category')
        plt.title(f'Top 20 Freelancer Categories (as of {latest_date_freelancers.strftime("%Y-%m-%d")})')
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'top_freelancer_categories.png', dpi=300)
        plt.close()
        
        top_freelancers.to_csv(REPORTS_DIR / 'top_freelancer_categories.csv', index=False)
    
    # Generate a report with HTML
    with open(REPORTS_DIR / 'top_categories_report.html', 'w') as f:
        f.write(f"""
        <html>
        <head>
            <title>Top Categories Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                tr:hover {{ background-color: #f5f5f5; }}
                img {{ max-width: 100%; height: auto; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>Top Categories Report</h1>
            <p>Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <h2>Top 20 Project Categories (as of {latest_date.strftime("%Y-%m-%d")})</h2>
            <img src="figures/top_project_categories.png" alt="Top Project Categories">
            
            <table>
                <tr>
                    <th>Category</th>
                    <th>Number of Projects</th>
                    <th>Date</th>
                </tr>
        """)
        
        for _, row in top_projects.iterrows():
            f.write(f"""
                <tr>
                    <td>{row['category']}</td>
                    <td>{row['num']}</td>
                    <td>{row['date'].strftime("%Y-%m-%d")}</td>
                </tr>
            """)
        
        f.write("</table>")
        
        if not freelances_df.empty:
            f.write(f"""
                <h2>Top 20 Freelancer Categories (as of {latest_date_freelancers.strftime("%Y-%m-%d")})</h2>
                <img src="figures/top_freelancer_categories.png" alt="Top Freelancer Categories">
                
                <table>
                    <tr>
                        <th>Category</th>
                        <th>Number of Freelancers</th>
                        <th>Date</th>
                    </tr>
            """)
            
            for _, row in top_freelancers.iterrows():
                f.write(f"""
                    <tr>
                        <td>{row['category']}</td>
                        <td>{row['num']}</td>
                        <td>{row['date'].strftime("%Y-%m-%d")}</td>
                    </tr>
                """)
            
            f.write("</table>")
        
        f.write("""
            </body>
            </html>
        """)
    
    print("Top categories report generated.")

def generate_trending_report(projects_df):
    """Generate report on trending categories over time."""
    print("Generating trending categories report...")
    
    # Get dates for the last 3 months
    latest_date = projects_df['date'].max()
    three_months_ago = latest_date - pd.DateOffset(months=3)
    
    # Filter data for the last 3 months
    recent_data = projects_df[projects_df['date'] >= three_months_ago]
    
    # Group by date and category, and sum the numbers
    grouped = recent_data.groupby(['date', 'category'])['num'].sum().reset_index()
    
    # Get the top 10 categories based on the most recent date
    latest_data = grouped[grouped['date'] == latest_date]
    top_categories = latest_data.sort_values('num', ascending=False).head(10)['category'].unique()
    
    # Filter the grouped data to include only these top categories
    trend_data = grouped[grouped['category'].isin(top_categories)]
    
    # Pivot the data for plotting
    pivot_data = trend_data.pivot(index='date', columns='category', values='num')
    
    # Plot the trends
    plt.figure(figsize=(14, 8))
    for category in top_categories:
        if category in pivot_data.columns:
            plt.plot(pivot_data.index, pivot_data[category], marker='o', linewidth=2, label=category)
    
    plt.title('Trending Project Categories (Last 3 Months)')
    plt.xlabel('Date')
    plt.ylabel('Number of Projects')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'trending_categories.png', dpi=300)
    plt.close()
    
    # Calculate growth rates
    growth_data = []
    
    for category in top_categories:
        if category in pivot_data.columns:
            first_value = pivot_data[category].iloc[0]
            last_value = pivot_data[category].iloc[-1]
            
            if first_value > 0:  # Avoid division by zero
                growth_rate = ((last_value - first_value) / first_value) * 100
            else:
                growth_rate = float('inf') if last_value > 0 else 0
                
            growth_data.append({
                'category': category,
                'first_date': pivot_data.index[0],
                'first_value': first_value,
                'last_date': pivot_data.index[-1],
                'last_value': last_value,
                'growth_rate': growth_rate
            })
    
    growth_df = pd.DataFrame(growth_data)
    growth_df = growth_df.sort_values('growth_rate', ascending=False)
    
    # Plot growth rates
    plt.figure(figsize=(12, 8))
    bars = plt.bar(growth_df['category'], growth_df['growth_rate'], color=sns.color_palette("viridis", len(growth_df)))
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    plt.xlabel('Category')
    plt.ylabel('Growth Rate (%)')
    plt.title(f'Category Growth Rates ({pivot_data.index[0].strftime("%Y-%m-%d")} to {pivot_data.index[-1].strftime("%Y-%m-%d")})')
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels above bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                 f'{height:.1f}%', ha='center', va='bottom', rotation=0)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'category_growth_rates.png', dpi=300)
    plt.close()
    
    # Save to CSV
    growth_df.to_csv(REPORTS_DIR / 'category_growth_rates.csv', index=False)
    pivot_data.to_csv(REPORTS_DIR / 'trending_categories_data.csv')
    
    # Generate HTML report
    with open(REPORTS_DIR / 'trending_categories_report.html', 'w') as f:
        f.write(f"""
        <html>
        <head>
            <title>Trending Categories Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                img {{ max-width: 100%; height: auto; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>Trending Categories Report</h1>
            <p>Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <h2>Trending Project Categories (Last 3 Months)</h2>
            <img src="figures/trending_categories.png" alt="Trending Categories">
            
            <h2>Category Growth Rates</h2>
            <img src="figures/category_growth_rates.png" alt="Category Growth Rates">
            
            <table>
                <tr>
                    <th>Category</th>
                    <th>Value on {pivot_data.index[0].strftime("%Y-%m-%d")}</th>
                    <th>Value on {pivot_data.index[-1].strftime("%Y-%m-%d")}</th>
                    <th>Growth Rate</th>
                </tr>
        """)
        
        for _, row in growth_df.iterrows():
            growth_class = "positive" if row['growth_rate'] >= 0 else "negative"
            f.write(f"""
                <tr>
                    <td>{row['category']}</td>
                    <td>{int(row['first_value'])}</td>
                    <td>{int(row['last_value'])}</td>
                    <td class="{growth_class}">{row['growth_rate']:.1f}%</td>
                </tr>
            """)
        
        f.write("""
            </table>
            </body>
            </html>
        """)
    
    print("Trending categories report generated.")

def generate_category_groups_report(projects_df):
    """Generate report on category groupings."""
    print("Generating category groups report...")
    
    # Get the most recent date
    latest_date = projects_df['date'].max()
    
    # Filter for the most recent date
    latest_projects = projects_df[projects_df['date'] == latest_date]
    
    # Assign each category to a group
    latest_projects['group'] = latest_projects['category'].apply(assign_category_group)
    
    # Group by the assigned group and sum the numbers
    grouped = latest_projects.groupby('group')['num'].sum().reset_index()
    grouped = grouped.sort_values('num', ascending=False)
    
    # Plot the results
    plt.figure(figsize=(12, 8))
    bars = plt.bar(grouped['group'], grouped['num'], color=sns.color_palette("viridis", len(grouped)))
    plt.xlabel('Category Group')
    plt.ylabel('Number of Projects')
    plt.title(f'Projects by Category Group (as of {latest_date.strftime("%Y-%m-%d")})')
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels above bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                 f'{height:,}', ha='center', va='bottom', rotation=0)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'category_groups.png', dpi=300)
    plt.close()
    
    # Create a pie chart for the distribution
    plt.figure(figsize=(10, 10))
    plt.pie(grouped['num'], labels=grouped['group'], autopct='%1.1f%%', 
            startangle=90, colors=sns.color_palette("viridis", len(grouped)))
    plt.axis('equal')
    plt.title(f'Distribution of Projects by Category Group (as of {latest_date.strftime("%Y-%m-%d")})')
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'category_groups_pie.png', dpi=300)
    plt.close()
    
    # Save to CSV
    grouped.to_csv(REPORTS_DIR / 'category_groups.csv', index=False)
    
    # Also save the detailed breakdown
    detailed = latest_projects.groupby(['group', 'category'])['num'].sum().reset_index()
    detailed = detailed.sort_values(['group', 'num'], ascending=[True, False])
    detailed.to_csv(REPORTS_DIR / 'category_groups_detailed.csv', index=False)
    
    # Generate HTML report
    with open(REPORTS_DIR / 'category_groups_report.html', 'w') as f:
        f.write(f"""
        <html>
        <head>
            <title>Category Groups Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                tr:hover {{ background-color: #f5f5f5; }}
                img {{ max-width: 100%; height: auto; margin: 20px 0; }}
                .group-header {{ background-color: #e8f4f8; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Category Groups Report</h1>
            <p>Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <h2>Projects by Category Group (as of {latest_date.strftime("%Y-%m-%d")})</h2>
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between;">
                <div style="flex: 1; min-width: 45%;">
                    <img src="figures/category_groups.png" alt="Category Groups">
                </div>
                <div style="flex: 1; min-width: 45%;">
                    <img src="figures/category_groups_pie.png" alt="Category Groups Pie Chart">
                </div>
            </div>
            
            <h2>Summary by Group</h2>
            <table>
                <tr>
                    <th>Category Group</th>
                    <th>Number of Projects</th>
                    <th>Percentage</th>
                </tr>
        """)
        
        total = grouped['num'].sum()
        for _, row in grouped.iterrows():
            percentage = (row['num'] / total) * 100
            f.write(f"""
                <tr>
                    <td>{row['group']}</td>
                    <td>{row['num']:,}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
            """)
        
        f.write(f"""
            </table>
            
            <h2>Detailed Breakdown by Group</h2>
        """)
        
        current_group = None
        for _, row in detailed.iterrows():
            if current_group != row['group']:
                if current_group is not None:
                    f.write("</table>")
                
                current_group = row['group']
                group_total = detailed[detailed['group'] == current_group]['num'].sum()
                
                f.write(f"""
                    <h3>{current_group} ({group_total:,} projects)</h3>
                    <table>
                        <tr>
                            <th>Category</th>
                            <th>Number of Projects</th>
                            <th>Percentage of Group</th>
                        </tr>
                """)
            
            percentage = (row['num'] / group_total) * 100
            f.write(f"""
                <tr>
                    <td>{row['category']}</td>
                    <td>{row['num']:,}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
            """)
        
        if current_group is not None:
            f.write("</table>")
        
        f.write("""
            </body>
            </html>
        """)
    
    print("Category groups report generated.")

def generate_index_page():
    """Generate an index page linking to all reports."""
    print("Generating index page...")
    
    with open(REPORTS_DIR / 'index.html', 'w') as f:
        f.write(f"""
        <html>
        <head>
            <title>German Freelance Market Analysis</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                h1, h2 {{ color: #2c3e50; }}
                .report-card {{
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                    background-color: #f9f9f9;
                }}
                .report-card h2 {{
                    margin-top: 0;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                }}
                a {{ color: #3498db; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>German Freelance Market Analysis</h1>
            <p>Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <div class="report-card">
                <h2>Top Categories Report</h2>
                <p>Analysis of the most in-demand project categories and freelancer specializations in the German market.</p>
                <p><a href="top_categories_report.html">View Report</a></p>
            </div>
            
            <div class="report-card">
                <h2>Trending Categories Report</h2>
                <p>Analysis of trending project categories over time, including growth rates and emerging opportunities.</p>
                <p><a href="trending_categories_report.html">View Report</a></p>
            </div>
            
            <div class="report-card">
                <h2>Category Groups Report</h2>
                <p>Analysis of project categories grouped by domain, showing the distribution of demand across different sectors.</p>
                <p><a href="category_groups_report.html">View Report</a></p>
            </div>
            
            <h2>Raw Data</h2>
            <ul>
                <li><a href="top_project_categories.csv">Top Project Categories (CSV)</a></li>
                <li><a href="top_freelancer_categories.csv">Top Freelancer Categories (CSV)</a></li>
                <li><a href="category_growth_rates.csv">Category Growth Rates (CSV)</a></li>
                <li><a href="trending_categories_data.csv">Trending Categories Data (CSV)</a></li>
                <li><a href="category_groups.csv">Category Groups Summary (CSV)</a></li>
                <li><a href="category_groups_detailed.csv">Category Groups Detailed (CSV)</a></li>
            </ul>
        </body>
        </html>
        """)
    
    print("Index page generated.")

def main():
    """Main function to generate all reports."""
    print("Starting report generation...")
    
    # Fetch data from MySQL
    projects_df, freelances_df = fetch_data()
    
    # Generate reports
    generate_top_categories_report(projects_df, freelances_df)
    generate_trending_report(projects_df)
    generate_category_groups_report(projects_df)
    generate_index_page()
    
    print(f"All reports generated successfully. View them in the '{REPORTS_DIR}' directory.")
    print(f"Open '{REPORTS_DIR}/index.html' to access all reports.")

if __name__ == "__main__":
    main()
