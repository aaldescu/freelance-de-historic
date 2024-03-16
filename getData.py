import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import csv
import os

def get_data_points(url,depth):
    time.sleep(2)
    print (url + str(depth))

    response = requests.get(url)
    current_depth = depth + 1

    if response.status_code == 200:
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find the element with id "panel_categories"
        panel_categories = soup.find(id="panel_categories")
        
        # Find all <li> elements within the element with id "panel_categories"
        li_elements = panel_categories.find_all('li')
        
        print(len(li_elements))
        page_title = soup.find('title').text
        print(page_title)
        

        # Print the text content of each <li> element
        for li in li_elements:
            time.sleep(1)
            a_element = li.find('a')
            span_element = li.find('span')
            
            if a_element and span_element:
                a_text = a_element.text.strip()
                span_text = span_element.text.replace('[','').replace(']','').strip()
                a_href = a_element.get('href').strip()
                li_url = "https://www.freelance.de" + a_href
                
                #print('-' * 30)

                data.append([current_time,a_text, span_text, a_href])

                if current_depth < max_depth:
                    get_data_points(li_url,current_depth)
                

    else:
        
        print(f"Error: {response.status_code}")

now = datetime.now()
current_time = now.strftime("%Y-%m-%d")
print("Current Time =", current_time)

#GET PROJEKTE DATA
start_url = "https://www.freelance.de/Projekte/"
max_depth = 2
data = []
project_path = os.path.dirname(os.path.realpath(__file__)) + "/"


#header row
#data.append(["date","job_group","num_jobs", "href"])


#start the recursive function
get_data_points(start_url,0)

# Save data to CSV file
with open(project_path + 'project_data.csv', 'a', newline='', encoding='utf-8' ) as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=";")
    csvwriter.writerows(data)


#GET FREELANCE DATA
start_url = "https://www.freelance.de/Freelancer/"
max_depth = 2
data = [] #reset
project_path = os.path.dirname(os.path.realpath(__file__)) + "/"

#start the recursive function
get_data_points(start_url,0)

# Save data to CSV file
with open(project_path + 'freelance_data.csv', 'a', newline='', encoding='utf-8' ) as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=";")
    csvwriter.writerows(data)