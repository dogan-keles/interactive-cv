"""
Complete Profile Seed Script
Run this to populate the database with professional CV data.

Usage:
    python -m backend.scripts.seed_profile
"""

import asyncio
from datetime import date
from backend.infrastructure.database import SessionLocal
from backend.data_access.knowledge_base.postgres import (
    Profile, Skill, Experience, Project
)


async def seed_profile():
    """Seed complete profile data."""
    
    db = SessionLocal()
    
    try:
        # Delete existing profile data (if re-running)
        existing_profile = db.query(Profile).filter(Profile.id == 1).first()
        if existing_profile:
            db.query(Skill).filter(Skill.profile_id == 1).delete()
            db.query(Experience).filter(Experience.profile_id == 1).delete()
            db.query(Project).filter(Project.profile_id == 1).delete()
            db.delete(existing_profile)
            db.commit()
            print("🗑️  Deleted existing profile data")
        
        # ============================================================
        # PROFILE
        # ============================================================
        profile = Profile(
            name="Doğan Keleş",
            email="dgnkls.47@gmail.com",  # Update with real email
            location="Kadıköy, İstanbul, Turkey",
            summary=(
                "Software Engineer focused on solutions, user experience, and sustainability. "
                "Experienced in full-stack development with modern frameworks (React.js, Vue.js, Spring Boot, ASP.NET, Node.js). "
                "Currently working as a freelance developer, building complete end-to-end websites and AI-powered applications "
                "for clients using Python, FastAPI, and modern LLM technologies. "
                "Passionate about continuous learning, clean architecture, and building scalable systems. "
                "Strong believer in teamwork and quality-driven development. "
                "Aiming to specialize in system design, architecture, and real-time problem solving with AI-assisted solutions."
            ),
            linkedin_url="https://linkedin.com/in/dogan-keles",
            github_username="dogan-keles",
        )
        db.add(profile)
        db.flush()
        
        print(f"✅ Created profile: {profile.name} (ID: {profile.id})")
        
        # ============================================================
        # SKILLS (NO PROFICIENCY LEVELS)
        # ============================================================
        skills_data = [
            # Programming Languages
            ("Python", "Backend"),
            ("JavaScript", "Frontend"),
            ("TypeScript", "Frontend"),
            ("Java", "Backend"),
            
            # Frontend Technologies
            ("React.js", "Frontend"),
            ("Vue.js", "Frontend"),
            ("Redux", "Frontend"),
            ("Context API", "Frontend"),
            ("Hooks", "Frontend"),
            ("HTML", "Frontend"),
            ("CSS", "Frontend"),
            ("Tailwind CSS", "Frontend"),
            ("Bootstrap", "Frontend"),
            ("Axios", "Frontend"),
            ("Cypress", "Frontend"),
            
            # Backend Technologies
            ("Spring Boot", "Backend"),
            ("ASP.NET", "Backend"),
            ("Node.js", "Backend"),
            ("FastAPI", "Backend"),
            ("Flask", "Backend"),
            ("Django", "Backend"),
            ("Entity Framework", "Backend"),
            ("RESTful API", "Backend"),
            
            # Databases
            ("PostgreSQL", "Database"),
            ("SQL Server", "Database"),
            ("SQLAlchemy", "Database"),
            ("Neon DB", "Database"),
            
            # AI/ML & LLM
            ("LLM Integration", "AI/ML"),
            ("Groq API", "AI/ML"),
            ("RAG Systems", "AI/ML"),
            ("Multi-Agent Systems", "AI/ML"),
            ("GitHub Copilot", "AI/ML"),
            ("ChatGPT Integration", "AI/ML"),
            
            # Architecture & Design
            ("OOP", "Architecture"),
            ("Design Patterns", "Architecture"),
            ("Microservices Architecture", "Architecture"),
            ("System Design", "Architecture"),
            ("RESTful Architecture", "Architecture"),
            
            # DevOps & Tools
            ("Docker", "DevOps"),
            ("Kubernetes", "DevOps"),
            ("Git", "DevOps"),
            ("TFS", "DevOps"),
            ("Elasticsearch (ELK)", "DevOps"),
            
            # Cloud & Deployment
            ("Koyeb", "Cloud"),
            ("Vercel", "Cloud"),
            
            # Message Queue & Integration
            ("IBM MQ", "Integration"),
            ("Message Queue (MQ)", "Integration"),
            ("ISO 20022 (PACS/PAIN)", "Integration"),
            
            # Testing & Quality
            ("Unit Testing", "Testing"),
            ("Debugging", "Testing"),
            
            # Design & Tools
            ("Figma", "Design"),
            
            # Soft Skills
            ("Problem Solving", "Soft Skills"),
            ("Time Management", "Soft Skills"),
            ("Adaptability", "Soft Skills"),
            ("Teamwork", "Soft Skills"),
            ("Algorithms", "Soft Skills"),
        ]
        
        for skill_name, category in skills_data:
            skill = Skill(
                profile_id=profile.id,
                name=skill_name,
                category=category,
                proficiency_level="Proficient",  # Generic level for all
            )
            db.add(skill)
        
        print(f"✅ Created {len(skills_data)} skills")
        
        # ============================================================
        # WORK EXPERIENCE
        # ============================================================
        experiences_data = [
            {
                "company": "Intertech Bilgi İşlem ve Pazarlama Ticaret A.Ş.",
                "role": "Software Engineer (SEPA Department)",
                "start_date": date(2024, 1, 1),
                "end_date": date(2024, 12, 31),
                "location": "İstanbul, Turkey",
                "description": (
                    "• Worked in Single Euro Payments Area (SEPA) department, contributing to projects for Eurozone customers\n"
                    "• Developed SEPA Instant Payment system enabling 24/7 money transfers within 10 seconds across Eurozone\n"
                    "• Implemented event handler structures and message queue services (IBM MQ) for real-time transaction processing\n"
                    "• Worked with XML-based financial message files based on ISO 20022 standards (PACS, PAIN)\n"
                    "• Responded to daily customer call tickets and ensured accounting of unaccounted transactions\n"
                    "• Contributed to large-scale financial infrastructure projects with high availability requirements"
                )
            },
            {
                "company": "Self-Employed (Freelance)",
                "role": "Full Stack Developer & AI Engineer",
                "start_date": date(2024, 12, 1),
                "end_date": None,  # Current
                "location": "İstanbul, Turkey",
                "description": (
                    "• Building complete end-to-end websites for clients from design to deployment (frontend + backend)\n"
                    "• Developing AI-powered applications using Python, FastAPI, and modern LLM technologies (Groq API)\n"
                    "• Creating responsive, modern web applications with React.js, Vue.js, and Tailwind CSS\n"
                    "• Building multi-agent orchestration systems with intelligent routing and RAG (Retrieval-Augmented Generation)\n"
                    "• Implementing RESTful APIs, database design, and full-stack architecture for client projects\n"
                    "• Implementing vector databases with TF-IDF embeddings for semantic search capabilities\n"
                    "• Creating interactive CV assistant with ProfileAgent, GitHubAgent, CVAgent, and GuardrailAgent\n"
                    "• Deploying serverless applications on modern cloud platforms (Koyeb, Vercel, Neon DB, Netlify)\n"
                    "• Providing complete web solutions including domain setup, hosting, and maintenance\n"
                    "• Integrating AI-assisted development tools into production workflows for enhanced efficiency"
                )
            },
            {
                "company": "REFERANS MÜH. DAN. PROJE, MADEN. İNŞ. SAN. VE TİC.",
                "role": "Geomatics Engineer",
                "start_date": date(2022, 6, 1),
                "end_date": date(2022, 10, 31),
                "location": "Turkey",
                "description": (
                    "• Executed and controlled necessary measurements in infrastructure, superstructure, and cadastral works\n"
                    "• Focused on 3D modeling, problem-solving, and coordinating between field applications and office processes\n"
                    "• Managed landscaping projects and base map design with digital visualization tools"
                )
            },
            {
                "company": "EKİN PROJE YÖN. HARİTA MİM. İNŞ. SAN. VE TİC. LTD.",
                "role": "Intern Engineer",
                "start_date": date(2021, 6, 1),
                "end_date": date(2021, 8, 31),
                "location": "Turkey",
                "description": (
                    "• Conducted field measurements required for base map design\n"
                    "• Performed office work on visualizing measurements in digital environment\n"
                    "• Gained practical experience in geomatics engineering and surveying techniques"
                )
            },
        ]
        
        for exp_data in experiences_data:
            experience = Experience(
                profile_id=profile.id,
                company=exp_data["company"],
                role=exp_data["role"],
                start_date=exp_data["start_date"],
                end_date=exp_data["end_date"],
                description=exp_data["description"],
                location=exp_data["location"],
            )
            db.add(experience)
        
        print(f"✅ Created {len(experiences_data)} work experiences")
        
        # ============================================================
        # PROJECTS
        # ============================================================
        projects_data = [
            {
                "title": "Interactive CV Assistant (Multi-Agent AI System)",
                "description": (
                    "Intelligent CV assistant powered by multi-agent architecture with ProfileAgent, GitHubAgent, "
                    "CVAgent, and GuardrailAgent. Features include RAG-based semantic search, automatic vector "
                    "embedding synchronization, multi-language support (10+ languages), and dynamic SEO. "
                    "Deployed on Koyeb (backend) and Vercel (frontend) with PostgreSQL vector database."
                ),
                "tech_stack": [
                    "Python", "FastAPI", "PostgreSQL", "SQLAlchemy", "Groq API", 
                    "LLM Integration", "RAG", "TF-IDF", "Neon DB", "Koyeb", 
                    "React", "Vite", "Tailwind CSS", "Vercel"
                ],
                "relevance_tags": ["AI", "Multi-Agent", "LLM", "Backend", "Full-Stack", "RAG", "Vector DB"],
                "github_url": "https://github.com/dogan-keles/interactive-cv",
                "demo_url": "https://dogankeles.com",
            },
            {
                "title": "SEPA Instant Payment System",
                "description": (
                    "Real-time payment processing system for Single Euro Payments Area enabling 24/7 money "
                    "transfers within 10 seconds. Implemented event-driven architecture with IBM MQ message "
                    "queues and ISO 20022 compliant XML message processing (PACS, PAIN standards)."
                ),
                "tech_stack": [
                    "Java", "Spring Boot", "IBM MQ", "PostgreSQL", "Event-Driven Architecture",
                    "ISO 20022", "XML Processing", "Microservices", "RESTful API"
                ],
                "relevance_tags": ["FinTech", "Payment Systems", "Real-Time Processing", "Enterprise"],
                "github_url": None,
                "demo_url": None,
            },
            {
                "title": "Workintech Full-Stack Bootcamp Projects (75 Projects)",
                "description": (
                    "Completed intensive 6-month bootcamp (960 hours) focusing on modern full-stack development. "
                    "Built 75+ projects covering React, Redux, Node.js, PostgreSQL, RESTful APIs, authentication, "
                    "testing, and deployment. Passed 12 comprehensive assessments covering frontend and backend technologies."
                ),
                "tech_stack": [
                    "React", "Redux", "Node.js", "Express", "PostgreSQL", "HTML", "CSS",
                    "JavaScript", "TypeScript", "RESTful API", "Git", "Cypress"
                ],
                "relevance_tags": ["Full-Stack", "Bootcamp", "Web Development", "Education"],
                "github_url": None,
                "demo_url": None,
            },
        ]
        
        for proj_data in projects_data:
            project = Project(
                profile_id=profile.id,
                title=proj_data["title"],
                description=proj_data["description"],
                tech_stack=proj_data["tech_stack"],
                relevance_tags=proj_data["relevance_tags"],
                github_url=proj_data["github_url"],
                demo_url=proj_data["demo_url"],
            )
            db.add(project)
        
        print(f"✅ Created {len(projects_data)} projects")
        
        # ============================================================
        # COMMIT ALL
        # ============================================================
        db.commit()
        db.refresh(profile)
        
        print("\n" + "=" * 60)
        print("🎉 PROFILE SEEDING COMPLETE!")
        print("=" * 60)
        print(f"Profile ID: {profile.id}")
        print(f"Name: {profile.name}")
        print(f"Skills: {len(skills_data)}")
        print(f"Experiences: {len(experiences_data)}")
        print(f"Projects: {len(projects_data)}")
        print("=" * 60)
        
        return profile
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding profile: {e}")
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(seed_profile())