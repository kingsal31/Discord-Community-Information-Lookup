#!/usr/bin/env python3
import argparse
import re
import requests
import time
from datetime import datetime
import os

def usage():
    return ("""Discord Community Information Lookup (DCIL)

Usage:
Basic single community usage:
  python3 dcil.py -l <discord_link> [-s <output_filename>]

For multiple communities:
  python3 dcil.py -L <file_with_links> [-s <output_filename>]
  python3 dcil.py -L <file_with_links> -S <base_filename> [-d <directory_name>]

Required:
  -l <discord_link>     Single Discord community invite link
  OR
  -L <file>            File containing multiple Discord invite links (one per line)

Optional:
  -s <filename>        Save output to a single file (will add .txt if not specified)
  -S <base_filename>   Save each community to a separate file (only with -L)
                      Files will be named as <base_filename>_<server_name>.txt
  -d <directory>       Directory to save individual files (only with -L and -S)
  -u                   Display this usage information
""")

def scrape_discord_community(link):
    try:
        # Extract invite code from the provided discord link
        pattern = r'(?:discord\.gg/|discord\.com/invite/)([\w-]+)'
        match = re.search(pattern, link)
        if not match:
            raise ValueError("Invalid Discord invite link format")
        
        invite_code = match.group(1)
        
        # Use Discord's public invite API
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        url = f"https://discord.com/api/v9/invites/{invite_code}?with_counts=true"
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch data (Status code: {response.status_code})")
        
        data = response.json()
        
        total_members = data['approximate_member_count']
        active_members = data['approximate_presence_count']
        offline_members = total_members - active_members
        
        return {
            'community_name': data['guild']['name'],
            'link': link,
            'active_members': active_members,
            'offline_members': offline_members,
            'total_members': total_members
        }
    except Exception as e:
        raise Exception(f"Error scraping community: {str(e)}")

def format_report(info):
    report = []
    report.append(f"Community Name: {info['community_name']}")
    report.append(f"Community Link: {info['link']}")
    report.append(f"Total Active Members: {info['active_members']}")
    report.append(f"Total Offline Members: {info['offline_members']}")
    report.append(f"Total Members: {info['total_members']}")
    return "\n".join(report)

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def sanitize_filename(filename):
    # Remove or replace invalid filename characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def ensure_txt_extension(filename):
    if not filename.lower().endswith('.txt'):
        return filename + '.txt'
    return filename

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-l', type=str, help='Discord community invite link')
    parser.add_argument('-L', type=str, help='Text file containing multiple discord community links')
    parser.add_argument('-s', type=str, help='Output file name to save the results')
    parser.add_argument('-S', type=str, help='Base filename for individual community files')
    parser.add_argument('-d', type=str, help='Directory to save individual files')
    parser.add_argument('-u', action='store_true', help='Display usage information')
    args = parser.parse_args()

    if args.u or (not args.l and not args.L):
        print(usage())
        return

    # Validate -S and -d can only be used with -L
    if (args.S or args.d) and not args.L:
        print("Error: -S and -d flags can only be used with -L flag")
        return

    # If directory is specified, ensure it exists
    if args.d:
        if not args.S:
            print("Error: -d flag can only be used with -S flag")
            return
        ensure_directory_exists(args.d)

    reports = []

    if args.l:
        try:
            info = scrape_discord_community(args.l)
            reports.append(format_report(info))
        except Exception as e:
            print(f"Error: {e}")
            return

    if args.L:
        try:
            with open(args.L, 'r') as f:
                links = [line.strip() for line in f if line.strip()]
            
            for link in links:
                try:
                    info = scrape_discord_community(link)
                    report = format_report(info)
                    
                    # If -S flag is used, save individual files
                    if args.S:
                        filename = f"{args.S}_{sanitize_filename(info['community_name'])}"
                        filename = ensure_txt_extension(filename)
                        
                        if args.d:
                            filepath = os.path.join(args.d, filename)
                        else:
                            filepath = filename
                            
                        try:
                            with open(filepath, 'w') as f:
                                f.write(report)
                            print(f"Saved report for {info['community_name']} to {filepath}")
                        except Exception as e:
                            print(f"Error writing to file {filepath}: {e}")
                    
                    reports.append(report)
                    # Add a small delay between requests to be nice to Discord's API
                    time.sleep(1)
                except Exception as e:
                    error_msg = f"Error scraping {link}: {str(e)}"
                    reports.append(error_msg)
                    print(error_msg)
        except Exception as e:
            print(f"Error reading file: {e}")
            return

    # If -s is used, save combined report
    if args.s:
        final_report = "\n\n".join(reports)
        output_file = ensure_txt_extension(args.s)
        try:
            with open(output_file, 'w') as f:
                f.write(final_report)
            print(f"Combined report saved to {output_file}")
        except Exception as e:
            print(f"Error writing to file: {e}")
    elif not args.S:  # Only print to console if we're not saving individual files
        print("\n\n".join(reports))

if __name__ == '__main__':
    main()
