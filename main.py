import os
from api4jenkins import Jenkins
from github import Github
import logging
import json
import requests
from time import time, sleep

log_level = os.environ.get('INPUT_LOG_LEVEL', 'INFO')
logging.basicConfig(format='JENKINS_ACTION: %(message)s', level=log_level)

def main():
    # Required
    url = os.environ["INPUT_URL"]
    job_name = os.environ["INPUT_JOB_NAME"]

    # Optional
    username = os.environ.get("INPUT_USERNAME")
    api_token = os.environ.get("INPUT_API_TOKEN")
    parameters = os.environ.get("INPUT_PARAMETERS")
    cookies = os.environ.get("INPUT_COOKIES")
    timeout = int(os.environ.get("INPUT_TIMEOUT"))
    start_timeout = int(os.environ.get("INPUT_START_TIMEOUT"))
    interval = int(os.environ.get("INPUT_INTERVAL"))
    access_token = os.environ.get("INPUT_ACCESS_TOKEN")
    display_job_name = os.environ.get("INPUT_DISPLAY_JOB_NAME")

    # Predefined
    job_query_timeout = 60
    job_query_interval = 5

    g = Github(os.environ.get("INPUT_ACCESS_TOKEN"))
    
    getCommitMessages(g)


def getCommitMessages(githubApi):
    
    github_event_file = open(os.environ.get("GITHUB_EVENT_PATH"), "r")
    github_event = json.loads(github_event_file.read())
    github_event_file.close

    pr_repo_name = github_event["pull_request"]["base"]["repo"]["full_name"]
    pr_number = github_event["number"]

    commits = githubApi.get_repo(pr_repo_name).get_pull(pr_number).get_commits(body)
    
    cnt = 0
    for c in commits:
        cnt += 1
        print(str(cnt) + " :" + c.commit.message)

if __name__ == "__main__":
    main()
