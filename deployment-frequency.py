import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Generator

import requests
from manim import Scene, RED, GREEN, BLUE, YELLOW, ORANGE, BarChart, DrawBorderThenFill, PURPLE, GRAY

CIRCLECI_TOKEN = os.getenv("CIRCLECI_TOKEN", "setme")


@dataclass
class Deploy:
    on: datetime
    revision: str
    url: str


def get_deploys_from_jobs(org_slug: str, project_slug: str, pipeline_name: str, job_name: str, branch: str,
                          days: int) -> Generator[Deploy, None, None]:
    start_date = (datetime.utcnow() - timedelta(days=days - 1)).date()
    start_date_str = start_date.isoformat()
    resp = requests.get(f"https://circleci.com/api/v2/insights/{org_slug}/{project_slug}/workflows/{pipeline_name}?branch={branch}&start-date={start_date_str}Z",
                        auth=(CIRCLECI_TOKEN, ""))

    for item in resp.json()["items"]:
        workflow_id = item["id"]
        resp = requests.get(f"https://circleci.com/api/v2/workflow/{workflow_id}/job", auth=(CIRCLECI_TOKEN, ""))
        for workflow_item in resp.json()["items"]:
            name = workflow_item["name"]
            status = workflow_item["status"]
            if name == job_name and status == "success":
                print(f"Looking up job {workflow_item['id']}")
                # get revision
                resp = requests.get(f"https://circleci.com/api/v2/workflow/{workflow_id}", auth=(CIRCLECI_TOKEN, ""))
                pipeline_id = resp.json()["pipeline_id"]
                resp = requests.get(f"https://circleci.com/api/v2/pipeline/{pipeline_id}", auth=(CIRCLECI_TOKEN, ""))
                revision = resp.json()["vcs"]["revision"]

                on = datetime.fromisoformat(workflow_item["stopped_at"].replace("Z", ""))

                if on.date() < start_date:
                    print(f"Skipping as too early: {on.date()}")
                    return

                yield Deploy(
                    on=on,
                    revision=revision,
                    url=f"https://app.circleci.com/pipelines/{org_slug}/{project_slug}/{pipeline_id}/workflows/{workflow_id}/jobs/MISSING"
                )


def get_deploys_by_day(days: int):
    now = datetime.utcnow()
    deploys = {(now - timedelta(days=i)).date().isoformat()[5:]: [] for i in range(days)}
    for deploy in get_deploys_from_jobs(
            org_slug="gh/sleuth-io",
            project_slug="sleuth",
            pipeline_name="test-and-deploy",
            job_name="deploy-prod",
            branch="master",
            days=days):
        day = deploy.on.date().isoformat()[5:]
        deploys[day].insert(0, deploy)

    return deploys


class DeployFrequencyChart(Scene):

    def construct(self):
        deploys = get_deploys_by_day(7)
        colors = [RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, GRAY]
        values = [len(values) for values in deploys.values()]
        names = [key for key in deploys.keys()]
        bar_chart = BarChart(values, bar_colors=colors, bar_names=names)
        self.play(DrawBorderThenFill(bar_chart, run_time=5))
        self.wait(3)


if __name__ == "__main__":
    deploys = get_deploys_by_day(5)
    print(f"deploys per day")
    for day, deploy_list in deploys.items():
        print(f"Day: {day}")
        for deploy in deploy_list:
            print(f"- {deploy.revision} ({deploy.on})")




