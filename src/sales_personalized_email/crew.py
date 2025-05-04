from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from pydantic import BaseModel

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


class PersonalizedEmail(BaseModel):
    subject_line: str
    email_body: str
    follow_up_notes: str


@CrewBase
class SalesPersonalizedEmailCrew:
    """SalesPersonalizedEmail crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def prospect_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["prospect_researcher"],
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def content_personalizer(self) -> Agent:
        return Agent(
            config=self.agents_config["content_personalizer"],
            tools=[],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def email_copywriter(self) -> Agent:
        return Agent(
            config=self.agents_config["email_copywriter"],
            tools=[],
            allow_delegation=False,
            verbose=True,
        )

    @task
    def research_prospect_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_prospect_task"],
            agent=self.prospect_researcher(),
        )

    @task
    def personalize_content_task(self) -> Task:
        return Task(
            config=self.tasks_config["personalize_content_task"],
            agent=self.content_personalizer(),
        )

    @task
    def write_email_task(self) -> Task:
        return Task(
            config=self.tasks_config["write_email_task"],
            agent=self.email_copywriter(),
            output_json=PersonalizedEmail,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the SalesPersonalizedEmail crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
