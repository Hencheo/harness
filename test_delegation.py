import sys
import os
from bridge.harness_mission_factory import create_mission

# Case: Web Scrapper Mission
mission_name = "TechNewsScrapper"
tasks = [
    (
        "research_patterns",
        "sre",
        {"instruction": "Identify the best libraries and RSS feeds for tech news scraping in 2026."},
        []
    ),
    (
        "implement_scrapper",
        "devops",
        {"instruction": "Create a robust Python scrapper in the workspace based on the research patterns provided in prev_research_patterns."},
        ["research_patterns"]
    )
]

create_mission(mission_name, tasks)
