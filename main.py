import os
from api4jenkins import Jenkins
from github import Github
import logging
import json
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
    wait = bool(os.environ.get("INPUT_WAIT"))
    timeout = int(os.environ.get("INPUT_TIMEOUT"))
    start_timeout = int(os.environ.get("INPUT_START_TIMEOUT"))
    interval = int(os.environ.get("INPUT_INTERVAL"))
    access_token = os.environ.get("INPUT_ACCESS_TOKEN")


    if username and api_token:
        auth = (username, api_token)
    else:
        auth = None
        logging.info('Username or token not provided. Connecting without authentication.')

    if parameters:
        try:
            parameters = json.loads(parameters)
        except json.JSONDecodeError as e:
            raise Exception('`parameters` is not valid JSON.') from e
    else:
        parameters = {}

    if cookies:
        try:
            cookies = json.loads(cookies)
        except json.JSONDecodeError as e:
            raise Exception('`cookies` is not valid JSON.') from e
    else:
        cookies = {}

    jenkins = Jenkins(url, auth=auth, cookies=cookies)

    try:
        jenkins.version
    except Exception as e:
        raise Exception('Could not connect to Jenkins.') from e

    logging.info('Successfully connected to Jenkins.')

    queue_item = jenkins.build_job(job_name, **parameters)

    logging.info('Requested to build job.')

    t0 = time()
    sleep(interval)
    while time() - t0 < start_timeout:
        build = queue_item.get_build()
        if build:
            break
        logging.info(f'Build not started yet. Waiting {interval} seconds.')
        sleep(interval)
    else:
        raise Exception(f"Could not obtain build and timed out. Waited for {start_timeout} seconds.")

    build_url = build.url
    if access_token is not None:
        issue_comment(f'Build started [here]({build_url})')
    logging.info(f"Build URL: {build_url}")
    print(f"::set-output name=build_url::{build_url}")
    print(f"::notice title=build_url::{build_url}")

    result=wait_for_build(build,timeout,interval)

    if access_token is None:
        logging.info("No comment.")
        if result in ('FAILURE', 'ABORTED'):
            raise Exception(result)
        return

    body = f'### [Build]({build_url}) status returned **{result}**.'
    try:
        body+='\nBuild ran _{build_time} ms_'.format(build_time=build.api_json()["duration"])
    except e:
        logging.info(f"Build duration unknown:\n{e}")

    test_reports=build.get_test_report()
    if build.get_test_report() is None:
        body+="\n_No test were ran_"
    else:
        test_reports_json=test_reports.api_json()
        body+="\n\n## Test Results:\n**Passed: {p}**\n**Failed: {f}**\n**Skipped: {s}**".format(
        p=test_reports_json["passCount"],
        f=test_reports_json["failCount"],
        s=test_reports_json["skipCount"]
    )
    issue_comment(body)

    if result in ('FAILURE', 'ABORTED'):
        raise Exception(result)


def wait_for_build(build,timeout,interval):
    build_url=build.url
    t0 = time()
    sleep(interval)
    while time() - t0 < timeout:
        result = build.result
        if result == 'SUCCESS':
            logging.info(f'Build successful')
            return result
        if result == 'UNSTABLE':
            logging.info(f'Build unstable')
            return result
        if result in ('FAILURE', 'ABORTED'):
            logging.info(f'Build status returned "{result}". Build has failed ☹️.')
            return result
        logging.info(f'Build not finished yet. Waiting {interval} seconds. {build_url}')
        sleep(interval)
    logging.info(f"Build has not finished and timed out. Waited for {timeout} seconds.")
    return "TIMEOUT"


def issue_comment(body):
    g = Github(os.environ.get("INPUT_ACCESS_TOKEN"))

    github_event_file = open(os.environ.get("GITHUB_EVENT_PATH"), "r")
    github_event = json.loads(github_event_file.read())
    github_event_file.close

    pr_repo_name = github_event["pull_request"]["base"]["repo"]["full_name"]
    pr_number = github_event["number"]

    g.get_repo(pr_repo_name).get_pull(pr_number).create_issue_comment(body)


if __name__ == "__main__":
    main()
