#!/usr/bin/env python
# coding: utf-8

# In[37]:


# This notebook have as a point to allow us scraping job sites, to give us ability to have a DB that references 
# all available computing jobs in France.
# We should add also a country classemnet of basic salries to compare ?? TBD
# Steps:
#Search on :
#- indeed
#- monster
#with keys {'informatique', 'france'} 
#- Find where is job ads 
#- parse and get {title, salary, location, missions, company name}
#
#!pip install pandas
#!pip install bs4 requests lxml 
#!pip install mysql-connector-python
#!pip  install numpy
#!pip install matplotlib
#!pip install seaborn 


# In[1]:


# Install libraries
#!pip install  lxml requests bs4  pandas selenium

import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
import mysql.connector
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
import json
import datetime
import matplotlib.pyplot as plt
import seaborn as sns


# In[122]:


# Utils:

#Compute the salary per month for INDEED
def compute_salary(card):
    salary_tmp = None
    final_salary = None
    if card.find({"span"},{"class":"salaryText"}) is not None:
        salary_tmp = card.find({"span"}, {"class":"salaryText"}).text.strip()
        salary_tmp_splited = salary_tmp.split(' ')
        result = salary_tmp_splited[0].replace('\xa0','')
        final_salary= int(result)
        if salary_tmp_splited[-1] != "an":
            final_salary = final_salary*12
    return final_salary

#Compute the salary per month for monster
def compute_salary_mon(salary_string):
    sal = None
    if salary_string is not None:
        splited = salary_string.split(' ')
        cleaned_string = splited[0].lstrip("€")
        sal = int(cleaned_string)
        if splited[-1].lower() != "an":
            sal = sal*12
    return sal

#Compute the salary per month for apec
def compute_salary_apec(salary_string):
    if salary_string == "A négocier":
        return None
    if salary_string is not None:
        splited = salary_string.split(' ')
        if 'partir' in splited:
            return int(splited[3])*1000
        if splited[-1].lower() != "annuel":
            return splited[0]*12
        if splited[-1].lower() == "annuel":
            return int(splited[0])*1000
    return None



# configure Firefox Driver
## Pleach check your version chrom
def web_driver():
    # Add additional Options to the webdriver
    firefox_options = FirefoxOptions()
    # add the argument and make the browser Headless.
    firefox_options.add_argument("--headless")

    # Instantiate the Webdriver: Mention the executable path of the webdriver you have downloaded
    # if driver is in PATH, no need to provide executable_path
    driver = webdriver.Firefox(executable_path = "./geckodriver", options=firefox_options)
    return driver

# configure Chrome Webdriver
def configure_chrome_driver():
    # Add additional Options to the webdriver
    chrome_options = ChromeOptions()
    # add the argument and make the browser Headless.
    chrome_options.add_argument("--headless")
    # Instantiate the Webdriver: Mention the executable path of the webdriver you have downloaded
    # if driver is in PATH, no need to provide executable_path
    driver = webdriver.Chrome(executable_path="./chromedriver", options = chrome_options)
    return driver
# fetch soup request function
def do_request(url):
    try:
        res = requests.get(url)
        res.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print ("OOps: Something Else",err)
    # parse witrh soup
    return bs(res.content,"html")
   
# Simulate a scroll and click on cookies constement pop up
def fetch_salary(url, browser):
    browser.get(url)
    browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    try:
        browser.find_element_by_xpath("//button[text()='Fermer']").click()
    except: 
        print("No button")
        pass
    time.sleep(3)
    ad_detail = bs(browser.page_source, 'html')
    salary = None
    try:
        salary = ad_detail.find({"div"},{"name":"value_salary"}).text
    except:
        print("No salary")
        pass
    return salary

def get_real_location(string):
    location = {}
    AUTH_KEY =  "AIzaSyATr6fvRb-z29lA4z_iVXLcXrfOXh86MRs"
    params = {
        'loc': string,
        'mykey': AUTH_KEY
    }
    api_url = "https://maps.googleapis.com/maps/api/geocode/json?address={loc}&key={mykey}".format_map(params)
    data = requests.get(api_url)
    real_location = json.loads(data.content)
    full_adds = real_location['results'][0]['address_components']
    location['city'] = ""
    location['zipcode'] = ""
    location['region'] = ""
    location['department'] = ""
    for add in full_adds:
        if add['types'][0] == 'locality':
            location['city'] = add['long_name']
        if add['types'][0] == 'administrative_area_level_2':
            location['department'] = add['long_name']
        if add['types'][0] == 'administrative_area_level_1':
            location['region'] = add['long_name']
        if add['types'][0] == 'postal_code':
            location['zipcode'] = add['long_name']
    return location


#Create database connection
def insertAd(ad):
    try:
        mydb = mysql.connector.connect(host="localhost",
                               port="3306",
                               user="root",
                               password="rootpassword",
                               database="scrap")
        mycursor = mydb.cursor()
        sql = "INSERT INTO ad (ref,job,company,city,zipcode,region,department,link,salary,origin) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        val = (ad['ref'], ad['job'],ad['company'],ad['city'],ad['zipcode'],ad['region'],ad['department'],ad['link'],ad['salary'],ad['origin'])
        mycursor.execute(sql, val)
        mydb.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        
# Recover data from database

def fetch_all_data():
    try:
        connection = mysql.connector.connect(host="localhost",
                           port="3306",
                           user="root",
                           password="rootpassword",
                           database="scrap")
        sql_select_Query = "select * from ad"
        cursor = connection.cursor()
        cursor.execute(sql_select_Query)
        records = cursor.fetchall()
    except Error as e:
        print("Error reading data from MySQL table", e)
    finally:
        if (connection.is_connected()):
            connection.close()
            cursor.close()
            print("MySQL connection is closed")
    return records
indeed_url = "https://fr.indeed.com/emplois?q=bigdata&l=France"
monster_url = "https://www.monster.fr/emploi/recherche/?q=bigdata"
apec_url = "https://www.apec.fr/candidat/recherche-emploi.html/emploi?niveauxExperience=101881&motsCles=informatique"


# In[3]:


ads = []


# In[123]:


# search for jobs with key 'inforamtique' and 'france' location.
# INDEED
i = 1
for x in range(0,50,10):
    soup = do_request(indeed_url)
    cards = soup.find_all({"div"},{"class":"jobsearch-SerpJobCard unifiedRow row result"})
    for card in cards:
        ad = {}
        ad["ref"] = card.attrs['id'].lstrip('\n')
        ad["job"] =  card.h2.a.text.replace('\n','')
        ad["company"] = card.find({"div"},{"class":"sjcl"}).span.text.lstrip('\n')
        location = card.find({"div"},{"class":"sjcl"}).find({"div"},{"class":"recJobLoc"}).attrs['data-rc-loc'].lstrip('\n')
        realsLocations = get_real_location(location)
        ad['city'] = realsLocations['city']
        ad['zipcode'] = realsLocations['zipcode']
        ad['region'] = realsLocations['region']
        ad['department'] = realsLocations['department']
        ad["link"] = 'https://fr.indeed.com'+card.find({"a"},{"class":"jobtitle turnstileLink"}).attrs['href'].lstrip('\n')
        ad["salary"] = compute_salary(card)
        ad['origin'] = 'indeed'
        #ads.append(ad)
        insertAd(ad)
        if(i > 5):
            break
        i = i + 1


# In[124]:


# Monster
# step 1: 
# fetch ads links in one page

browser = configure_chrome_driver()
for x in range(0,2):
    monster_url = monster_url + "&stpage=" + str(x) + "&page=" + str(x + 1)
    soup_monster = do_request(monster_url)
    allPostLink = soup_monster.findAll("h2", {'class', 'title'})
    linksArray = []
    i=1
    for post in allPostLink:
        linksArray.append(post.a['href'])
        linkUrl = post.a['href']
        try:
            res = requests.get(linkUrl)
            res.raise_for_status()
        except:
            continue
        ad_detail = bs(res.text, 'html')
        ad = {}
        ad['ref'] = linkUrl.split('/')[-1]
        ad['job'] = ad_detail.find({"h1"},{"class":"job_title"}).text
        ad['company'] = ad_detail.find({"div"},{"name":"job_company_name"}).text
        location = ad_detail.find({"div"},{"name":"job_company_location"}).text 
        realsLocations = get_real_location(location)
        ad['city'] = realsLocations['city']
        ad['zipcode'] = realsLocations['zipcode']
        ad['region'] = realsLocations['region']
        ad['department'] = realsLocations['department']
        ad['link'] = linkUrl
        salary_string = fetch_salary(linkUrl, browser)
        ad['salary'] = compute_salary_mon(salary_string)
        ad['origin'] = 'monster'
        #ads.append(ad) 
        insertAd(ad)
        if (i > 1) : break
        i= i+1
browser.close()


# In[125]:


# Apec data
baselink = "https://www.apec.fr"
browser = configure_chrome_driver()
browser.get(apec_url)
soup_apec = bs(browser.page_source, 'html')
cards = soup_apec.find_all({"a"},{"queryparamshandling":"merge"})
i = 1
for card in cards:
    url = baselink + card.attrs['href']
    #url = "https://www.apec.fr/candidat/recherche-emploi.html/emploi/detail-offre/165733084W?niveauxExperience=101881&motsCles=informatique&selectedIndex=4&page=0"
    browser.get(url)
    time.sleep(2)
    detail_apec = bs(browser.page_source, 'html')
    ad = {}
    draft_ref = detail_apec.find({"div"},{"class":"card-offer__text"}).div.text
    ad['ref'] = draft_ref.split(' ')[4]
    ad['job'] = detail_apec.find({"h2"},{"class":"card-title mt-0"}).text
    lists = detail_apec.find({"ul"},{"class":"details-offer-list mb-20"}).findChildren()
    try:
        ad['company'] = lists[0].text
    except:
        print('company error')
    try:
        location = lists[3].text
    except:
        print('location error')
        location = lists[2].text
    realsLocations = get_real_location(location)
    ad['city'] = realsLocations['city']
    ad['zipcode'] = realsLocations['zipcode']
    ad['region'] = realsLocations['region']
    ad['department'] = realsLocations['department']
    ad['link'] = url
    salary_string = detail_apec.find({"div"},{"class":"details-post"}).span.text
    ad['salary'] = compute_salary_apec(salary_string)
    ad['origin'] = 'apec'
    ##TODO : Insert in BD instead array
    #ads.append(ad)
    insertAd(ad)
    if(i > 5) :
        break
    i = i + 1
browser.close()


# In[136]:


# get data from database
records = fetch_all_data()
df = pd.DataFrame(records,columns=['id','ref','job','company','city','zipcode','region','department','link','salary','origin','creation_date'])


# In[8]:


# Test corelation TODO later
#plt.figure(figsize=(10,10))
#df_corr = df.corr()
#p=sns.heatmap(df_corr, annot=True,cmap ='RdYlGn')
df


# In[137]:


# Salaire moyen par region
# SQL version: SELECT region, avg(salary) FROM ad WHERE salary IS NOT NULL GROUP BY region
df_copy = df.copy()
df_mean_salary = df_copy[df_copy['salary'].notna()]
df_grouped = df_mean_salary.groupby(['region'])['salary'].mean()
x = df_grouped.index.values
y = df_grouped.values


# In[138]:


plt.bar(x,y,align='center',width=0.2) # A bar chart
plt.xlabel('Regions')
plt.ylabel('mean salary')
plt.xticks(x, x, rotation='vertical')
fig = plt.gcf() 
fig.set_size_inches(14,10)


# In[144]:


# camamber for job types 
# Nombre d'offre par region

#select region, count(*) as nbre_offre from  ad group by region;
df_grouped_1 = df_copy.groupby('region')['region'].count()


# In[149]:


labels = df_grouped_1.index.values
sizes = df_grouped_1.values
plt.pie(sizes, labels=labels, 
        autopct='%1.1f%%', shadow=True, startangle=90)
plt.axis('equal')
fig = plt.gcf() 
fig.set_size_inches(14,14)
plt.show()

