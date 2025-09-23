from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from pydantic import BaseModel, Field
from typing import Optional

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


class ProspectData(BaseModel):
    first_name: str = Field(..., description="First name of the prospect")
    last_name: str = Field(..., description="Last name of the prospect")
    title: Optional[str] = Field(None, description="Job title of the prospect")
    company: str = Field(..., description="Company/Account name (mandatory)")
    phone: Optional[str] = Field(None, description="Phone number")
    country: Optional[str] = Field(None, description="Country location")
    linkedin_profile: Optional[str] = Field(None, description="LinkedIn profile URL")
    selling_intent: Optional[str] = Field(None, description="Specific selling intent/use case for the product")


class PersonalizedEmail(BaseModel):
    subject_line: str
    email_body: str
    follow_up_notes: str
    validated_title: Optional[str] = Field(None, description="Validated job title (only if high confidence)")
    validated_linkedin_profile: Optional[str] = Field(None, description="Validated LinkedIn profile URL")
    validated_country: Optional[str] = Field(None, description="Validated country location (only if high confidence)")


@CrewBase
class SalesPersonalizedEmailCrew:
    """SalesPersonalizedEmail crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def linkedin_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["linkedin_researcher"],
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
            allow_delegation=False,
            verbose=True,
        )

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
    def linkedin_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["linkedin_research_task"],
            agent=self.linkedin_researcher(),
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
