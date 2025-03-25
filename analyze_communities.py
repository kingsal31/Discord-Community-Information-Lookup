#!/usr/bin/env python3
import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt
import shutil
from datetime import datetime

def usage():
    return ("""Discord Community Analysis Script (analyze_communities.py)

Usage:
  python3 analyze_communities.py -d <directory_with_text_files>
  python3 analyze_communities.py -f <single_text_file>
  python3 analyze_communities.py -d <directory> -s [save_directory]
  python3 analyze_communities.py -f <file> -s [save_directory]

Options:
  -d <directory_name>  Analyze all the text files in the given directory
  -f <filename>        Analyze a single text file
  -s [directory_name] Save analysis results to specified directory (default: 'Analysis Report')
  -u                   Display this usage information
""")

def load_data_from_file(filepath):
    """Load and parse community data from a text file."""
    data = {}
    with open(filepath, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith("Community Name:"):
                data['community_name'] = line.split(":")[1].strip()
            elif line.startswith("Community Link:"):
                data['link'] = line.split(":")[1].strip()
            elif line.startswith("Total Active Members:"):
                data['active_members'] = int(line.split(":")[1].strip())
            elif line.startswith("Total Offline Members:"):
                data['offline_members'] = int(line.split(":")[1].strip())
            elif line.startswith("Total Members:"):
                data['total_members'] = int(line.split(":")[1].strip())
    
    # Calculate additional metrics
    data['engagement_rate'] = (data['active_members'] / data['total_members'] * 100) if data['total_members'] > 0 else 0
    data['active_ratio'] = (data['active_members'] / (data['offline_members'] + 1)) # Adding 1 to avoid division by zero
    return data

def analyze_communities(directory=None, file=None):
    """Analyze communities from the specified directory or file."""
    communities_data = []
    
    if directory:
        # Analyze all text files in the directory
        for filename in os.listdir(directory):
            if filename.endswith('.txt'):
                filepath = os.path.join(directory, filename)
                community_data = load_data_from_file(filepath)
                communities_data.append(community_data)
    elif file:
        # Analyze the single text file
        community_data = load_data_from_file(file)
        communities_data.append(community_data)
    
    df = pd.DataFrame(communities_data)
    
    # Add rankings
    df['size_rank'] = df['total_members'].rank(ascending=False)
    df['engagement_rank'] = df['engagement_rate'].rank(ascending=False)
    df['activity_rank'] = df['active_ratio'].rank(ascending=False)
    
    return df

def save_analysis_results(save_dir, is_single_community=False):
    """Save all analysis results to specified directory."""
    # Create directory if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Get current timestamp for unique naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # List of files to save
    files_to_save = []
    
    if is_single_community:
        files_to_save.extend([
            'activity_ratio_report.txt',
            'active_vs_inactive_distribution.png',
            'membership_breakdown.png'
        ])
    else:
        files_to_save.extend([
            'analysis_report.txt',
            'engagement_analysis.png',
            'top_communities.png',
            'activity_matrix.png'
        ])
    
    # Copy each file to the save directory with timestamp
    for file in files_to_save:
        if os.path.exists(file):
            base, ext = os.path.splitext(file)
            new_name = f"{base}_{timestamp}{ext}"
            shutil.copy2(file, os.path.join(save_dir, new_name))
    
    print(f"\nAnalysis results saved to directory: {save_dir}")

def generate_analysis_report(df):
    """Generate a detailed competitive analysis report."""
    # Sort communities by different metrics (all communities, not just top 5)
    by_size = df.sort_values('total_members', ascending=False)[['community_name', 'total_members', 'engagement_rate']]
    by_engagement = df.sort_values('engagement_rate', ascending=False)[['community_name', 'engagement_rate', 'total_members']]
    by_activity = df.sort_values('active_ratio', ascending=False)[['community_name', 'active_members', 'total_members']]

    report = ["=== Discord Communities Competitive Analysis Report ===\n"]
    
    # Overall statistics
    report.extend([
        "MARKET OVERVIEW:",
        f"Total communities analyzed: {len(df)}",
        f"Average community size: {df['total_members'].mean():.0f} members",
        f"Average engagement rate: {df['engagement_rate'].mean():.2f}%",
        f"Market size (total members across all communities): {df['total_members'].sum():,}\n"
    ])

    # All communities ranked by different metrics
    report.extend([
        "ALL COMMUNITIES RANKED BY SIZE (Largest to Smallest):",
        by_size.to_string(),
        "\nALL COMMUNITIES RANKED BY ENGAGEMENT RATE (Highest to Lowest):",
        by_engagement.to_string(),
        "\nALL COMMUNITIES RANKED BY ACTIVITY RATIO (Most to Least Active):",
        by_activity.to_string(),
        "\nKEY FINDINGS:"
    ])

    # Add insights
    highest_engagement = df.loc[df['engagement_rate'].idxmax()]
    report.extend([
        f"- Most engaged community: {highest_engagement['community_name']} "
        f"({highest_engagement['engagement_rate']:.2f}% engagement rate)",
        f"- Largest community: {df.loc[df['total_members'].idxmax()]['community_name']} "
        f"({df['total_members'].max():,} members)",
        f"- Average engagement rate across all communities: "
        f"{df['engagement_rate'].mean():.2f}%",
        f"- Median community size: {df['total_members'].median():.0f} members",
        f"- Median engagement rate: {df['engagement_rate'].median():.2f}%"
    ])

    # Write report to file
    with open('analysis_report.txt', 'w') as file:
        file.write("\n".join(report))
    
    print("Competitive analysis report saved as 'analysis_report.txt'")

def generate_single_community_visualizations(df):
    """Generate visualizations specifically for single community analysis."""
    community_data = df.iloc[0]  # Get the first (and only) community's data
    
    # 1. Active vs Inactive Members Comparison
    plt.figure(figsize=(10, 6))
    members_data = [community_data['active_members'], community_data['offline_members']]
    labels = ['Active Members', 'Inactive Members']
    colors = ['#2ecc71', '#e74c3c']
    
    plt.pie(members_data, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=90)
    plt.title(f'Member Activity Distribution in {community_data["community_name"]}\n'
             f'Total Members: {community_data["total_members"]:,}')
    plt.axis('equal')
    plt.savefig('active_vs_inactive_distribution.png')
    print("Saved member distribution visualization as 'active_vs_inactive_distribution.png'")

    # 2. Bar chart comparing active vs inactive with total
    plt.figure(figsize=(10, 6))
    categories = ['Active Members', 'Inactive Members', 'Total Members']
    values = [community_data['active_members'], 
             community_data['offline_members'],
             community_data['total_members']]
    
    bars = plt.bar(categories, values, color=['#2ecc71', '#e74c3c', '#3498db'])
    plt.title(f'Membership Breakdown - {community_data["community_name"]}')
    plt.ylabel('Number of Members')
    
    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('membership_breakdown.png')
    print("Saved membership breakdown visualization as 'membership_breakdown.png'")

    # 3. Calculate and display activity ratios
    active_to_inactive_ratio = (community_data['active_members'] / 
                              community_data['offline_members'] 
                              if community_data['offline_members'] > 0 else float('inf'))
    
    inactive_to_active_ratio = (community_data['offline_members'] / 
                              community_data['active_members']
                              if community_data['active_members'] > 0 else float('inf'))

    # Generate activity ratio report
    ratio_report = [
        f"\nACTIVITY RATIO ANALYSIS - {community_data['community_name']}",
        f"Total Members: {community_data['total_members']:,}",
        f"Active Members: {community_data['active_members']:,}",
        f"Inactive Members: {community_data['offline_members']:,}",
        f"Engagement Rate: {community_data['engagement_rate']:.2f}%",
        "\nRATIOS:",
        f"• For every 1 ACTIVE member, there are {inactive_to_active_ratio:.2f} INACTIVE members",
        f"• For every 1 INACTIVE member, there are {active_to_inactive_ratio:.2f} ACTIVE members",
        f"\nKey Findings:",
        f"• {community_data['active_members'] / community_data['total_members'] * 100:.1f}% of the community is currently active",
        f"• {community_data['offline_members'] / community_data['total_members'] * 100:.1f}% of the community is currently inactive"
    ]

    with open('activity_ratio_report.txt', 'w') as file:
        file.write('\n'.join(ratio_report))
    print("Saved activity ratio report as 'activity_ratio_report.txt'")

def generate_visualizations(df, is_single_community=False):
    """Generate business-focused visualizations."""
    if is_single_community:
        generate_single_community_visualizations(df)
        return
        
    plt.style.use('ggplot')  # Using ggplot style instead of seaborn
    
    # Engagement Rate vs Community Size
    plt.figure(figsize=(12, 6))
    plt.scatter(df['total_members'], df['engagement_rate'], alpha=0.6)
    for i, txt in enumerate(df['community_name']):
        plt.annotate(txt, (df['total_members'].iloc[i], df['engagement_rate'].iloc[i]), 
                    fontsize=8, alpha=0.7)
    plt.title('Engagement Rate vs Community Size')
    plt.xlabel('Total Members (Community Size)')
    plt.ylabel('Engagement Rate (%)')
    plt.tight_layout()
    plt.savefig('engagement_analysis.png')
    print("Saved engagement analysis visualization as 'engagement_analysis.png'")

    # Top 10 Communities by Engagement
    plt.figure(figsize=(12, 6))
    top10 = df.nlargest(10, 'engagement_rate')
    bars = plt.bar(top10['community_name'], top10['engagement_rate'])
    plt.title('Top 10 Communities by Engagement Rate')
    plt.xlabel('Community Name')
    plt.ylabel('Engagement Rate (%)')
    plt.xticks(rotation=45, ha='right')
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom')
    plt.tight_layout()
    plt.savefig('top_communities.png')
    print("Saved top communities visualization as 'top_communities.png'")

    # Activity Matrix
    plt.figure(figsize=(12, 6))
    plt.scatter(df['active_ratio'], df['engagement_rate'], 
                s=df['total_members']/100, alpha=0.6)
    plt.title('Community Activity Matrix')
    plt.xlabel('Active/Inactive Ratio')
    plt.ylabel('Engagement Rate (%)')
    for i, txt in enumerate(df['community_name']):
        plt.annotate(txt, (df['active_ratio'].iloc[i], df['engagement_rate'].iloc[i]), 
                    fontsize=8, alpha=0.7)
    plt.tight_layout()
    plt.savefig('activity_matrix.png')
    print("Saved activity matrix visualization as 'activity_matrix.png'")

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-d', type=str, help='Directory containing text files with community data')
    parser.add_argument('-f', type=str, help='Single text file with community data')
    parser.add_argument('-s', nargs='?', const='Analysis Report', help='Save directory for analysis results')
    parser.add_argument('-u', action='store_true', help='Display usage information')
    args = parser.parse_args()

    if args.u or (not args.d and not args.f):
        print(usage())
        return

    # Analyze communities based on user input (directory or file)
    df = analyze_communities(directory=args.d, file=args.f)

    # Generate analysis report
    if not args.f:  # Only generate the competitive analysis report for multiple communities
        generate_analysis_report(df)

    # Generate visualizations (single community or bulk)
    is_single_community = bool(args.f)
    generate_visualizations(df, is_single_community=is_single_community)

    # Save results if -s flag is used
    if args.s:
        save_analysis_results(args.s, is_single_community=is_single_community)

if __name__ == '__main__':
    main()
