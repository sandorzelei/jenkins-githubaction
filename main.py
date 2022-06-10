import os
from api4jenkins import Jenkins
from github import Github
import logging
import re
import json
import requests
from time import time, sleep

log_level = os.environ.get('INPUT_LOG_LEVEL', 'INFO')
logging.basicConfig(format='JENKINS_ACTION: %(message)s', level=log_level)

def main():
    access_token = os.environ.get("INPUT_ACCESS_TOKEN")
    codebeamer_user = os.environ.get("INPUT_CODEBEAMER_USER")
    codebeamer_password = os.environ.get("INPUT_CODEBEAMER_PASSWORD")
    
    if !(username and api_token):
        auth = (username, api_token)
    else:
        auth = None
        logging.info('Username or token not provided. Connecting without authentication.')
        
    g = Github(access_token)
    
    getCommitMessages(g, (codebeamer_user, codebeamer_password))


def getCommitMessages(githubApi, cbAuth):
    
    github_event_file = open(os.environ.get("GITHUB_EVENT_PATH"), "r")
    github_event = json.loads(github_event_file.read())
    github_event_file.close

    pr_repo_name = github_event["pull_request"]["base"]["repo"]["full_name"]
    pr_number = github_event["number"]

    pr = githubApi.get_repo(pr_repo_name).get_pull(pr_number)
    commits = pr.get_commits()
    
    ids = []
    ids.extend(getIds(pr.title))
    
    for c in pr.get_commits():
        ids.extend(getIds(c.commit.message))
    
    for i in set(ids):
        itemGetUrl = f"https://codebeamer.com/cb/api/v3/items/{joke}"
        response = requests.get(url=itemGetUrl, auth=cbAuth)
        print(response)
        
def getIds(text):
    return re.findall(r'#([\d]+)', text)

if __name__ == "__main__":
    main()
