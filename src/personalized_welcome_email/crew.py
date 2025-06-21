from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from pydantic import BaseModel

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


class PersonalizedEmail(BaseModel):
    subject_line: str
    email_body: str
    follow_up_notes: str


@CrewBase
class PersonalizedWelcomeEmailCrew:
    """PersonalizedWelcomeEmail crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def relationship_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["relationship_researcher"],
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def personalization_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["personalization_strategist"],
            tools=[],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def adaptive_copywriter(self) -> Agent:
        return Agent(
            config=self.agents_config["adaptive_copywriter"],
            tools=[],
            allow_delegation=False,
            verbose=True,
        )

    @task
    def research_prospect_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_prospect_task"],
            agent=self.relationship_researcher(),
        )

    @task
    def personalize_content_task(self) -> Task:
        return Task(
            config=self.tasks_config["personalize_content_task"],
            agent=self.personalization_strategist(),
        )

    @task
    def write_email_task(self) -> Task:
        return Task(
            config=self.tasks_config["write_email_task"],
            agent=self.adaptive_copywriter(),
            output_json=PersonalizedEmail,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the PersonalizedWelcomeEmail crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
