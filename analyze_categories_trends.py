#!/usr/bin/env python
"""
Analyze distinct categories from the database, group them, and focus on daily trends.
This script provides insights into category groupings and their daily/weekly trends.
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
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
import matplotlib.dates as mdates

# Set style for plots
plt.style.use('fivethirtyeight')
sns.set_palette("viridis")

# Create reports directory if it doesn't exist
REPORTS_DIR = Path(__file__).parent / 'reports'
CATEGORIES_DIR = REPORTS_DIR / 'categories_analysis'
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(CATEGORIES_DIR, exist_ok=True)

# Define main category groups based on keywords
CATEGORY_GROUPS = {
    'Development': [
        'entwickl', 'develop', 'software', 'web', 'app', 'mobile', 'java', 'python', 
        'c#', 'c++', '.net', 'php', 'javascript', 'typescript', 'react', 'angular', 
        'vue', 'node', 'full-stack', 'frontend', 'backend', 'ios', 'android', 'swift', 
        'kotlin', 'flutter', 'devops', 'docker', 'kubernetes', 'aws', 'azure', 'cloud',
        'programm', 'coding', 'coder', 'entwickler'
    ],
    'Data': [
        'data', 'analytics', 'business intelligence', 'bi', 'tableau', 'power bi',
        'sql', 'database', 'datenbank', 'etl', 'data warehouse', 'data lake',
        'big data', 'hadoop', 'spark', 'data science', 'machine learning', 'ml',
        'ai', 'artificial intelligence', 'deep learning', 'nlp', 'statistik', 'daten',
        'analyst', 'scientist', 'engineer'
    ],
    'Management': [
        'project', 'projekt', 'management', 'manager', 'pmo', 'scrum', 'agile',
        'product owner', 'po', 'scrum master', 'kanban', 'lean', 'projektleiter',
        'projektmanager', 'projektleitung', 'führung', 'lead', 'leitung'
    ],
    'Design': [
        'design', 'ux', 'ui', 'user experience', 'user interface', 'graphic',
        'grafik', 'visual', 'creative', 'kreativ', 'illustration', 'animation',
        'video', 'media', 'medien', '3d', 'cad'
    ],
    'Infrastructure': [
        'system', 'network', 'netzwerk', 'security', 'sicherheit', 'admin',
        'administrator', 'it-administration', 'support', 'helpdesk', 'service desk',
        'infrastructure', 'infrastruktur', 'server', 'hardware', 'virtualization',
        'vmware', 'hyper-v', 'windows', 'linux', 'unix'
    ],
    'SAP': [
        'sap', 'abap', 's/4hana', 'erp', 'fi', 'co', 'mm', 'sd', 'pp', 'hcm',
        'crm', 'bw', 'fiori', 'hana'
    ],
    'Testing': [
        'test', 'qa', 'quality assurance', 'qualitätssicherung', 'testing',
        'tester', 'selenium', 'cypress', 'automation', 'automatisierung'
    ],
    'Consulting': [
        'consulting', 'beratung', 'berater', 'consultant', 'strategy', 'strategie',
        'business', 'geschäft', 'process', 'prozess', 'optimization', 'optimierung'
    ],
    'Marketing': [
        'marketing', 'seo', 'sea', 'sem', 'social media', 'content', 'online marketing',
        'digital marketing', 'e-commerce', 'ecommerce', 'crm', 'customer', 'kunde'
    ],
    'Healthcare': [
        'gesundheit', 'health', 'medical', 'medizin', 'arzt', 'ärzte', 'pflege', 
        'pharma', 'krankenhaus', 'hospital', 'klinik', 'clinic'
    ],
    'Engineering': [
        'ingenieur', 'engineer', 'maschinenbau', 'mechanical', 'electrical', 
        'elektronik', 'elektro', 'automotive', 'automobil', 'construction', 'bau'
    ],
    'Finance': [
        'finanz', 'finance', 'accounting', 'buchhaltung', 'controlling', 'bank', 
        'versicherung', 'insurance', 'steuer', 'tax', 'wirtschaft', 'economic'
    ],
    'Legal': [
        'legal', 'recht', 'law', 'anwalt', 'attorney', 'compliance', 'vertrag', 
        'contract', 'datenschutz', 'privacy'
    ],
    'Location': [
        'deutschland', 'germany', 'berlin', 'hamburg', 'münchen', 'munich', 'köln', 
        'cologne', 'frankfurt', 'stuttgart', 'düsseldorf', 'dortmund', 'essen', 
        'bremen', 'dresden', 'leipzig', 'hannover', 'nürnberg', 'nuremberg', 
        'duisburg', 'bochum', 'wuppertal', 'bielefeld', 'bonn', 'mannheim',
        'nordrhein-westfalen', 'bayern', 'bavaria', 'baden-württemberg', 'hessen',
        'niedersachsen', 'sachsen', 'rheinland-pfalz', 'berlin', 'schleswig-holstein',
        'brandenburg', 'sachsen-anhalt', 'thüringen', 'hamburg', 'mecklenburg-vorpommern',
        'saarland', 'bremen'
    ],
    'Work Model': [
        'remote', 'vor ort', 'hybrid', 'homeoffice', 'home office', 'onsite', 
        'on-site', 'offsite', 'off-site', 'freiberuflich', 'freelance'
    ]
}

def fetch_data():
    """Fetch data from MySQL database."""
    conn = get_mysql_connection()
    try:
        # Fetch projects data with all dates
        projects_df = pd.read_sql("""
            SELECT date, category, num, href 
            FROM projects 
            ORDER BY date, category
        """, conn)
        
        # Convert date strings to datetime objects
        projects_df['date'] = pd.to_datetime(projects_df['date'])
        
        # Convert num to integer
        projects_df['num'] = pd.to_numeric(projects_df['num'], errors='coerce').fillna(0).astype(int)
        
        return projects_df
    
    finally:
        conn.close()

def assign_category_group(category):
    """Assign a category to a group based on keywords."""
    if pd.isna(category) or category == '':
        return 'Other'
    
    category_lower = category.lower()
    
    for group, keywords in CATEGORY_GROUPS.items():
        for keyword in keywords:
            if keyword.lower() in category_lower:
                return group
    
    return 'Other'

def analyze_distinct_categories(df):
    """Analyze distinct categories and their groupings."""
    print("Analyzing distinct categories...")
    
    # Get distinct categories
    distinct_categories = df['category'].unique()
    print(f"Found {len(distinct_categories)} distinct categories")
    
    # Assign groups to categories
    category_groups = {}
    for category in distinct_categories:
        group = assign_category_group(category)
        if group not in category_groups:
            category_groups[group] = []
        category_groups[group].append(category)
    
    # Count categories per group
    group_counts = {group: len(categories) for group, categories in category_groups.items()}
    
    # Sort groups by count
    sorted_groups = sorted(group_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Create a DataFrame for visualization
    groups_df = pd.DataFrame(sorted_groups, columns=['Group', 'Count'])
    
    # Plot the distribution
    plt.figure(figsize=(12, 8))
    bars = plt.bar(groups_df['Group'], groups_df['Count'], color=sns.color_palette("viridis", len(groups_df)))
    plt.xlabel('Category Group')
    plt.ylabel('Number of Distinct Categories')
    plt.title('Distribution of Categories by Group')
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels above bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                 f'{int(height)}', ha='center', va='bottom', rotation=0)
    
    plt.tight_layout()
    plt.savefig(CATEGORIES_DIR / 'category_groups_distribution.png', dpi=300)
    plt.close()
    
    # Create a detailed report
    with open(CATEGORIES_DIR / 'category_groups_report.txt', 'w') as f:
        f.write(f"Category Groups Analysis\n")
        f.write(f"======================\n\n")
        f.write(f"Total distinct categories: {len(distinct_categories)}\n\n")
        
        for group, count in sorted_groups:
            f.write(f"{group}: {count} categories\n")
            for category in sorted(category_groups[group]):
                f.write(f"  - {category}\n")
            f.write("\n")
    
    # Return the grouped categories for further analysis
    return category_groups

def analyze_daily_trends(df, category_groups):
    """Analyze daily trends for each category group."""
    print("Analyzing daily trends...")
    
    # Add group column to the dataframe
    df['group'] = df['category'].apply(assign_category_group)
    
    # Get date range
    min_date = df['date'].min()
    max_date = df['date'].max()
    date_range = (max_date - min_date).days
    
    print(f"Analyzing trends over {date_range} days from {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
    
    # Aggregate by date and group
    daily_trends = df.groupby(['date', 'group'])['num'].sum().reset_index()
    
    # Create a pivot table for easier plotting
    pivot_trends = daily_trends.pivot(index='date', columns='group', values='num')
    
    # Fill NaN values with 0
    pivot_trends = pivot_trends.fillna(0)
    
    # Plot trends for each group
    for group in pivot_trends.columns:
        if group == 'Other':
            continue  # Skip the "Other" group
            
        plt.figure(figsize=(14, 8))
        plt.plot(pivot_trends.index, pivot_trends[group], marker='', linewidth=2)
        plt.title(f'Daily Trend for {group} Category')
        plt.xlabel('Date')
        plt.ylabel('Number of Projects')
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Format x-axis to show dates nicely
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        plt.gcf().autofmt_xdate()
        
        plt.tight_layout()
        plt.savefig(CATEGORIES_DIR / f'daily_trend_{group}.png', dpi=300)
        plt.close()
    
    # Plot trends for top 5 groups
    top_groups = pivot_trends.mean().sort_values(ascending=False).head(5).index
    
    plt.figure(figsize=(14, 8))
    for group in top_groups:
        plt.plot(pivot_trends.index, pivot_trends[group], marker='', linewidth=2, label=group)
    
    plt.title('Daily Trends for Top 5 Category Groups')
    plt.xlabel('Date')
    plt.ylabel('Number of Projects')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Format x-axis to show dates nicely
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    plt.savefig(CATEGORIES_DIR / 'daily_trends_top_groups.png', dpi=300)
    plt.close()
    
    # Calculate weekly averages to smooth out the data
    pivot_trends['week'] = pivot_trends.index.isocalendar().week
    pivot_trends['year'] = pivot_trends.index.isocalendar().year
    
    weekly_trends = pivot_trends.groupby(['year', 'week']).mean()
    weekly_trends.index = weekly_trends.index.map(lambda x: f"{x[0]}-W{x[1]:02d}")
    
    # Plot weekly trends for top 5 groups
    plt.figure(figsize=(14, 8))
    for group in top_groups:
        plt.plot(weekly_trends.index, weekly_trends[group], marker='o', linewidth=2, label=group)
    
    plt.title('Weekly Trends for Top 5 Category Groups')
    plt.xlabel('Week')
    plt.ylabel('Average Number of Projects')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(CATEGORIES_DIR / 'weekly_trends_top_groups.png', dpi=300)
    plt.close()
    
    # Calculate growth rates for each group
    growth_rates = {}
    
    for group in pivot_trends.columns:
        if group in ['week', 'year'] or group == 'Other':
            continue
            
        # Get the first and last 30 days average
        first_30_days = pivot_trends[group].head(30).mean()
        last_30_days = pivot_trends[group].tail(30).mean()
        
        if first_30_days > 0:
            growth_rate = ((last_30_days - first_30_days) / first_30_days) * 100
        else:
            growth_rate = 0 if last_30_days == 0 else float('inf')
            
        growth_rates[group] = {
            'first_30_days_avg': first_30_days,
            'last_30_days_avg': last_30_days,
            'growth_rate': growth_rate
        }
    
    # Convert to DataFrame for easier visualization
    growth_df = pd.DataFrame.from_dict(growth_rates, orient='index')
    growth_df = growth_df.sort_values('growth_rate', ascending=False)
    
    # Plot growth rates
    plt.figure(figsize=(14, 8))
    bars = plt.bar(growth_df.index, growth_df['growth_rate'], color=sns.color_palette("viridis", len(growth_df)))
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    plt.xlabel('Category Group')
    plt.ylabel('Growth Rate (%)')
    plt.title('Growth Rate by Category Group')
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels above bars
    for bar in bars:
        height = bar.get_height()
        if height > 1000:  # Handle very large values
            label = "∞" if np.isinf(height) else f"{height:.0f}%"
        else:
            label = f"{height:.1f}%"
        
        plt.text(bar.get_x() + bar.get_width()/2., 
                 height + 5 if height >= 0 else height - 15,
                 label, ha='center', va='bottom' if height >= 0 else 'top', rotation=0)
    
    plt.tight_layout()
    plt.savefig(CATEGORIES_DIR / 'growth_rates_by_group.png', dpi=300)
    plt.close()
    
    # Save growth rates to CSV
    growth_df.to_csv(CATEGORIES_DIR / 'growth_rates_by_group.csv')
    
    # Generate a detailed report
    with open(CATEGORIES_DIR / 'daily_trends_report.txt', 'w') as f:
        f.write(f"Daily Trends Analysis\n")
        f.write(f"===================\n\n")
        f.write(f"Analysis period: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')} ({date_range} days)\n\n")
        
        f.write(f"Growth Rates by Category Group:\n")
        f.write(f"-------------------------------\n\n")
        
        for group, data in growth_df.iterrows():
            growth = data['growth_rate']
            growth_str = "∞" if np.isinf(growth) else f"{growth:.2f}%"
            
            f.write(f"{group}:\n")
            f.write(f"  First 30 days average: {data['first_30_days_avg']:.2f}\n")
            f.write(f"  Last 30 days average: {data['last_30_days_avg']:.2f}\n")
            f.write(f"  Growth rate: {growth_str}\n\n")
    
    return growth_df

def analyze_category_correlations(df):
    """Analyze correlations between different category groups."""
    print("Analyzing category correlations...")
    
    # Add group column to the dataframe if not already present
    if 'group' not in df.columns:
        df['group'] = df['category'].apply(assign_category_group)
    
    # Aggregate by date and group
    daily_trends = df.groupby(['date', 'group'])['num'].sum().reset_index()
    
    # Create a pivot table
    pivot_trends = daily_trends.pivot(index='date', columns='group', values='num')
    
    # Fill NaN values with 0
    pivot_trends = pivot_trends.fillna(0)
    
    # Calculate correlation matrix
    corr_matrix = pivot_trends.corr()
    
    # Plot correlation matrix
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr_matrix, annot=True, cmap='viridis', vmin=-1, vmax=1, center=0,
                square=True, linewidths=.5, cbar_kws={"shrink": .8})
    plt.title('Correlation Between Category Groups')
    plt.tight_layout()
    plt.savefig(CATEGORIES_DIR / 'category_correlations.png', dpi=300)
    plt.close()
    
    # Save correlation matrix to CSV
    corr_matrix.to_csv(CATEGORIES_DIR / 'category_correlations.csv')
    
    # Find the most correlated pairs
    corr_pairs = []
    
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            group1 = corr_matrix.columns[i]
            group2 = corr_matrix.columns[j]
            correlation = corr_matrix.iloc[i, j]
            
            corr_pairs.append({
                'group1': group1,
                'group2': group2,
                'correlation': correlation
            })
    
    # Convert to DataFrame and sort
    corr_pairs_df = pd.DataFrame(corr_pairs)
    corr_pairs_df = corr_pairs_df.sort_values('correlation', ascending=False)
    
    # Save to CSV
    corr_pairs_df.to_csv(CATEGORIES_DIR / 'category_correlation_pairs.csv', index=False)
    
    # Generate a detailed report
    with open(CATEGORIES_DIR / 'category_correlations_report.txt', 'w') as f:
        f.write(f"Category Correlations Analysis\n")
        f.write(f"============================\n\n")
        
        f.write(f"Top Positive Correlations:\n")
        f.write(f"-------------------------\n\n")
        
        for _, row in corr_pairs_df.head(10).iterrows():
            f.write(f"{row['group1']} and {row['group2']}: {row['correlation']:.4f}\n")
        
        f.write(f"\nTop Negative Correlations:\n")
        f.write(f"-------------------------\n\n")
        
        for _, row in corr_pairs_df.tail(10).iterrows():
            f.write(f"{row['group1']} and {row['group2']}: {row['correlation']:.4f}\n")
    
    return corr_pairs_df

def generate_html_report():
    """Generate an HTML report with all the analysis results."""
    print("Generating HTML report...")
    
    with open(CATEGORIES_DIR / 'index.html', 'w') as f:
        f.write(f"""
        <html>
        <head>
            <title>Category Analysis and Daily Trends</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                .report-section {{
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                    background-color: #f9f9f9;
                }}
                .report-section h2 {{
                    margin-top: 0;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                }}
                img {{ max-width: 100%; height: auto; margin: 10px 0; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Category Analysis and Daily Trends</h1>
            <p>Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <div class="report-section">
                <h2>Category Groups Distribution</h2>
                <p>Analysis of how categories are distributed across different groups.</p>
                <img src="category_groups_distribution.png" alt="Category Groups Distribution">
                <p>For a detailed list of categories in each group, see the <a href="category_groups_report.txt">Category Groups Report</a>.</p>
            </div>
            
            <div class="report-section">
                <h2>Daily Trends</h2>
                <p>Analysis of daily trends for the top category groups.</p>
                <img src="daily_trends_top_groups.png" alt="Daily Trends for Top Groups">
                <img src="weekly_trends_top_groups.png" alt="Weekly Trends for Top Groups">
                
                <h3>Growth Rates by Category Group</h3>
                <img src="growth_rates_by_group.png" alt="Growth Rates by Category Group">
                
                <h3>Top Growing Categories</h3>
                <table>
                    <tr>
                        <th>Category Group</th>
                        <th>First 30 Days Avg</th>
                        <th>Last 30 Days Avg</th>
                        <th>Growth Rate</th>
                    </tr>
        """)
        
        # Read growth rates data
        growth_df = pd.read_csv(CATEGORIES_DIR / 'growth_rates_by_group.csv')
        growth_df = growth_df.sort_values('growth_rate', ascending=False)
        
        for _, row in growth_df.head(10).iterrows():
            growth_class = "positive" if row['growth_rate'] >= 0 else "negative"
            growth_str = "∞" if np.isinf(row['growth_rate']) else f"{row['growth_rate']:.2f}%"
            
            f.write(f"""
                    <tr>
                        <td>{row['Unnamed: 0']}</td>
                        <td>{row['first_30_days_avg']:.2f}</td>
                        <td>{row['last_30_days_avg']:.2f}</td>
                        <td class="{growth_class}">{growth_str}</td>
                    </tr>
            """)
        
        f.write("""
                </table>
                <p>For a detailed analysis of daily trends, see the <a href="daily_trends_report.txt">Daily Trends Report</a>.</p>
            </div>
            
            <div class="report-section">
                <h2>Category Correlations</h2>
                <p>Analysis of correlations between different category groups.</p>
                <img src="category_correlations.png" alt="Category Correlations">
                
                <h3>Top Correlated Category Pairs</h3>
                <table>
                    <tr>
                        <th>Category Group 1</th>
                        <th>Category Group 2</th>
                        <th>Correlation</th>
                    </tr>
        """)
        
        # Read correlation pairs data
        corr_pairs_df = pd.read_csv(CATEGORIES_DIR / 'category_correlation_pairs.csv')
        corr_pairs_df = corr_pairs_df.sort_values('correlation', ascending=False)
        
        for _, row in corr_pairs_df.head(10).iterrows():
            corr_class = "positive" if row['correlation'] >= 0 else "negative"
            
            f.write(f"""
                    <tr>
                        <td>{row['group1']}</td>
                        <td>{row['group2']}</td>
                        <td class="{corr_class}">{row['correlation']:.4f}</td>
                    </tr>
            """)
        
        f.write("""
                </table>
                <p>For a detailed analysis of category correlations, see the <a href="category_correlations_report.txt">Category Correlations Report</a>.</p>
            </div>
            
            <div class="report-section">
                <h2>Individual Category Group Trends</h2>
                <p>Daily trends for each individual category group.</p>
        """)
        
        # List all trend images
        trend_images = [f for f in os.listdir(CATEGORIES_DIR) if f.startswith('daily_trend_') and f.endswith('.png')]
        
        for image in trend_images:
            group_name = image.replace('daily_trend_', '').replace('.png', '')
            f.write(f"""
                <h3>{group_name}</h3>
                <img src="{image}" alt="Daily Trend for {group_name}">
            """)
        
        f.write("""
            </div>
            
            <div class="report-section">
                <h2>Raw Data</h2>
                <ul>
                    <li><a href="growth_rates_by_group.csv">Growth Rates by Category Group (CSV)</a></li>
                    <li><a href="category_correlations.csv">Category Correlations Matrix (CSV)</a></li>
                    <li><a href="category_correlation_pairs.csv">Category Correlation Pairs (CSV)</a></li>
                </ul>
            </div>
        </body>
        </html>
        """)
    
    print(f"HTML report generated at {CATEGORIES_DIR / 'index.html'}")

def main():
    """Main function to run the analysis."""
    print("Starting category analysis and daily trends...")
    
    # Fetch data from MySQL
    df = fetch_data()
    
    # Analyze distinct categories
    category_groups = analyze_distinct_categories(df)
    
    # Analyze daily trends
    growth_df = analyze_daily_trends(df, category_groups)
    
    # Analyze category correlations
    corr_pairs_df = analyze_category_correlations(df)
    
    # Generate HTML report
    generate_html_report()
    
    print(f"Analysis completed. View the report at {CATEGORIES_DIR / 'index.html'}")

if __name__ == "__main__":
    main()
