#!/usr/bin/env python3
"""
Random Prospect Generator for Auto-Improvement Testing

Generates diverse test prospects through web research to avoid bias in testing.
Ensures variety in industries, roles, company sizes, and geographies.
"""

import random
import os
from typing import List, Dict, Optional
from crewai_tools import SerperDevTool
from dataclasses import dataclass


@dataclass
class ProspectTemplate:
    """Template for generating prospect search queries"""
    role: str
    industry: str
    company_size: str
    geography: str
    selling_intent: str


class RandomProspectGenerator:
    """
    Generates diverse test prospects through web research.

    Ensures variety across:
    - Industries (tech, finance, retail, logistics, manufacturing, consulting)
    - Roles (technical, business, executive)
    - Company sizes (startup, mid-market, enterprise)
    - Geographies (US, EU, APAC)
    - Selling intents (specific use cases)
    """

    def __init__(self):
        self.search_tool = SerperDevTool()

        # Diverse prospect patterns
        self.roles = {
            'technical': ['CTO', 'VP Engineering', 'Head of Data', 'Director of Analytics', 'Chief Data Officer'],
            'business': ['CEO', 'COO', 'VP Operations', 'Director of Business Operations', 'Head of Strategy'],
            'executive': ['President', 'Managing Director', 'Partner', 'General Manager', 'EVP']
        }

        self.industries = [
            'technology', 'financial services', 'retail', 'e-commerce',
            'logistics', 'manufacturing', 'consulting', 'healthcare',
            'media', 'telecommunications', 'automotive', 'insurance'
        ]

        self.company_sizes = {
            'startup': ['startup', 'Series A', 'Series B', 'early-stage'],
            'midmarket': ['mid-market', 'growth-stage', 'scale-up'],
            'enterprise': ['Fortune 500', 'enterprise', 'public company', 'multinational']
        }

        self.geographies = {
            'US': ['United States', 'New York', 'San Francisco', 'Chicago', 'Boston', 'Austin'],
            'EU': ['London', 'Berlin', 'Paris', 'Amsterdam', 'Stockholm', 'Dublin'],
            'APAC': ['Singapore', 'Sydney', 'Tokyo', 'Hong Kong', 'Bangalore']
        }

        # Diverse selling intents
        self.selling_intents = [
            "CRM data analytics and customer segmentation",
            "Supply chain optimization and visibility",
            "Financial reporting and FP&A automation",
            "E-commerce inventory and sales analytics",
            "Marketing attribution and ROI tracking",
            "Customer data platform consolidation",
            "Operational efficiency and cost reduction",
            "Multi-source data integration and reporting",
            "Product analytics and user behavior tracking",
            "Sales pipeline analytics and forecasting",
            "Real-time business intelligence dashboards",
            "Data warehouse modernization",
            "Compliance and regulatory reporting automation",
            "Predictive maintenance and IoT analytics",
            "HR analytics and workforce planning"
        ]

    def generate_test_prospects(
        self,
        num_prospects: int = 20,
        ensure_diversity: bool = True
    ) -> List[Dict]:
        """
        Generate diverse test prospects through web research.

        Args:
            num_prospects: Number of prospects to generate (default: 20)
            ensure_diversity: Ensure mix of industries, roles, geographies (default: True)

        Returns:
            List of prospect dictionaries with keys:
            - first_name, last_name, company, title, selling_intent
            - phone, country, linkedin_profile (optional)
        """

        prospects = []
        used_companies = set()

        # Generate prospect templates for diversity
        templates = self._generate_diverse_templates(num_prospects) if ensure_diversity else None

        for i in range(num_prospects):
            print(f"Generating prospect {i+1}/{num_prospects}...", end='', flush=True)

            # Get template for this prospect
            template = templates[i] if templates else self._random_template()

            # Search for real prospect
            prospect = self._search_for_prospect(template, used_companies)

            if prospect:
                prospects.append(prospect)
                used_companies.add(prospect['company'])
                print(f" ✓ {prospect['first_name']} {prospect['last_name']} at {prospect['company']}")
            else:
                # Fallback to synthetic prospect if search fails
                prospect = self._generate_synthetic_prospect(template, used_companies)
                prospects.append(prospect)
                used_companies.add(prospect['company'])
                print(f" ⚠ Generated synthetic: {prospect['first_name']} {prospect['last_name']}")

        print(f"\n✅ Generated {len(prospects)} diverse prospects")
        self._print_diversity_stats(prospects)

        return prospects

    def _generate_diverse_templates(self, num_prospects: int) -> List[ProspectTemplate]:
        """Generate diverse prospect templates ensuring variety"""

        templates = []

        # Distribute across role types
        role_types = list(self.roles.keys())
        roles_per_type = num_prospects // len(role_types)

        for role_type in role_types:
            for _ in range(roles_per_type):
                templates.append(ProspectTemplate(
                    role=random.choice(self.roles[role_type]),
                    industry=random.choice(self.industries),
                    company_size=random.choice(list(self.company_sizes.keys())),
                    geography=random.choice(list(self.geographies.keys())),
                    selling_intent=random.choice(self.selling_intents)
                ))

        # Add remaining to reach target number
        while len(templates) < num_prospects:
            templates.append(self._random_template())

        # Shuffle to avoid patterns
        random.shuffle(templates)

        return templates

    def _random_template(self) -> ProspectTemplate:
        """Generate a random prospect template"""
        role_type = random.choice(list(self.roles.keys()))
        return ProspectTemplate(
            role=random.choice(self.roles[role_type]),
            industry=random.choice(self.industries),
            company_size=random.choice(list(self.company_sizes.keys())),
            geography=random.choice(list(self.geographies.keys())),
            selling_intent=random.choice(self.selling_intents)
        )

    def _search_for_prospect(
        self,
        template: ProspectTemplate,
        used_companies: set
    ) -> Optional[Dict]:
        """
        Search for real prospect matching template.

        Uses web search to find LinkedIn profiles matching criteria.
        """

        # Build search query
        location = random.choice(self.geographies[template.geography])
        query = f'"{template.role}" {template.industry} {location} LinkedIn profile'

        try:
            # Execute search
            result = self.search_tool.run(query)

            # Parse search results to extract prospect info
            # Note: This is a simplified version. Real implementation would parse
            # LinkedIn URLs and extract names/companies more robustly.

            prospect = self._parse_search_result(result, template, used_companies)
            return prospect

        except Exception as e:
            print(f" (search failed: {e})", end='')
            return None

    def _parse_search_result(
        self,
        search_result: str,
        template: ProspectTemplate,
        used_companies: set
    ) -> Optional[Dict]:
        """
        Parse search results to extract prospect information.

        This is a simplified implementation. Real version would use more
        sophisticated parsing of LinkedIn URLs and company names.
        """

        # Simplified: Use common names as fallback
        # Real implementation would parse actual search results

        # For now, return None to use synthetic generation
        # TODO: Implement actual LinkedIn result parsing
        return None

    def _generate_synthetic_prospect(
        self,
        template: ProspectTemplate,
        used_companies: set
    ) -> Dict:
        """
        Generate synthetic prospect when search fails.

        Uses realistic names and company patterns.
        """

        # Common professional names
        first_names = [
            'Sarah', 'Michael', 'Jennifer', 'David', 'Emily', 'James',
            'Jessica', 'Robert', 'Lisa', 'William', 'Amanda', 'Christopher',
            'Michelle', 'Daniel', 'Melissa', 'Matthew', 'Stephanie', 'Andrew'
        ]

        last_names = [
            'Johnson', 'Smith', 'Williams', 'Brown', 'Jones', 'Garcia',
            'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Anderson', 'Taylor',
            'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson'
        ]

        # Generate company name
        company_prefixes = ['Global', 'Advanced', 'Premier', 'Summit', 'Apex', 'Vertex']
        company_suffixes = ['Group', 'Solutions', 'Corporation', 'Technologies', 'Enterprises', 'Systems']

        company = f"{random.choice(company_prefixes)} {template.industry.title()} {random.choice(company_suffixes)}"

        # Ensure unique company
        counter = 1
        original_company = company
        while company in used_companies:
            company = f"{original_company} {counter}"
            counter += 1

        return {
            'first_name': random.choice(first_names),
            'last_name': random.choice(last_names),
            'title': template.role,
            'company': company,
            'phone': '',
            'country': random.choice(self.geographies[template.geography]),
            'linkedin_profile': '',
            'selling_intent': template.selling_intent
        }

    def _print_diversity_stats(self, prospects: List[Dict]):
        """Print diversity statistics of generated prospects"""

        print("\n📊 Diversity Statistics:")
        print(f"   Total prospects: {len(prospects)}")
        print(f"   Unique companies: {len(set(p['company'] for p in prospects))}")

        # Count selling intents
        intents = {}
        for prospect in prospects:
            intent = prospect.get('selling_intent', 'none')
            intents[intent] = intents.get(intent, 0) + 1

        print(f"   Unique selling intents: {len(intents)}")

        # Count geographies
        countries = {}
        for prospect in prospects:
            country = prospect.get('country', 'unknown')
            countries[country] = countries.get(country, 0) + 1

        print(f"   Geographic diversity: {len(countries)} countries/regions")


def generate_selling_intents(num_intents: int = 15) -> List[str]:
    """
    Generate list of diverse selling intents for testing.

    Args:
        num_intents: Number of intents to return (default: 15)

    Returns:
        List of selling intent strings
    """

    generator = RandomProspectGenerator()
    return random.sample(generator.selling_intents, min(num_intents, len(generator.selling_intents)))


if __name__ == "__main__":
    """
    Test the prospect generator
    """

    print("🧪 Testing Random Prospect Generator")
    print("=" * 70)

    generator = RandomProspectGenerator()

    # Generate 5 test prospects
    prospects = generator.generate_test_prospects(num_prospects=5, ensure_diversity=True)

    print("\n📝 Sample Prospects:")
    for i, prospect in enumerate(prospects[:3], 1):
        print(f"\n{i}. {prospect['first_name']} {prospect['last_name']}")
        print(f"   Company: {prospect['company']}")
        print(f"   Title: {prospect.get('title', 'N/A')}")
        print(f"   Country: {prospect.get('country', 'N/A')}")
        print(f"   Selling Intent: {prospect['selling_intent']}")

    print("\n✅ Generator test complete!")
