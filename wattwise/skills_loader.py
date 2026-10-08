import os
import re

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")

def parse_frontmatter(content: str):
    """Parses simple YAML frontmatter from a markdown string."""
    name = "unknown"
    description = "No description provided."
    
    # Match the frontmatter block
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        frontmatter = match.group(1)
        for line in frontmatter.split('\n'):
            line = line.strip()
            if line.startswith('name:'):
                name = line[5:].strip()
            elif line.startswith('description:'):
                description = line[12:].strip()
                
    return name, description

def get_all_skills() -> list[dict]:
    """Scans the skills directory and returns a list of available skills with their descriptions."""
    skills = []
    if not os.path.exists(SKILLS_DIR):
        return skills
        
    for item in os.listdir(SKILLS_DIR):
        skill_path = os.path.join(SKILLS_DIR, item)
        if os.path.isdir(skill_path):
            md_file = os.path.join(skill_path, "SKILL.md")
            if os.path.exists(md_file):
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    name, description = parse_frontmatter(content)
                    skills.append({
                        "name": item, # Use folder name as required by spec
                        "description": description
                    })
    return skills

def load_skill(name: str) -> str:
    """Returns the full markdown content of the requested skill."""
    # Prevent directory traversal attacks
    safe_name = os.path.basename(name)
    md_file = os.path.join(SKILLS_DIR, safe_name, "SKILL.md")
    
    if os.path.exists(md_file):
        with open(md_file, "r", encoding="utf-8") as f:
            return f.read()
    return f"Error: Skill '{name}' not found."
