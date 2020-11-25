#!/usr/bin/env python
# coding: utf-8

# In[5]:


# This notebook have as a point to allow us scraping job sites, to give us ability to have a DB that references 
# all available computing jobs in France.
# Steps:
"""
Search on :
- indeed
- monster
with keys {'informatique', 'france'} 
- Find where is job ads 
- parse and get {title, salary, location, missions, company name}
"""
#get_ipython().system('pip install pandas')


# In[6]:


# Brouillon
#!conda install lxml requests bs4
#!conda install -y pandas
#!pip install pandas

import requests
from bs4 import BeautifulSoup as bs
import pandas as pd


# In[9]:


# search for jobs with key 'inforamtique' and 'france' location.

indeed_url = "https://fr.indeed.com/emplois?q=informatique&l=France"
res = requests.get("https://fr.indeed.com/emplois?q=informatique&l=France")
# print(res)
# parse witrh soup
soup = bs(res.content,"lxml")
#print(type(soup))
cards = soup.find_all({"div"},{"class":"jobsearch-SerpJobCard unifiedRow row result"})
subjects = []
companies = []
for card in cards:
    draft = card.h2.a.text
    result = draft.replace('\n','')
    subjects.append(result)
    result2 = card.find({"div"},{"class":"sjcl"}).span.text
    companies.append(result2)
df = pd.DataFrame(zip(subjects,companies),columns=('Job','Company'))
print(df)


# In[ ]:





# In[ ]:




