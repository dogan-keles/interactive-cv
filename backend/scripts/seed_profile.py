"""
Profile Seed Template - FOR INITIAL SETUP ONLY

⚠️ IMPORTANT INSTRUCTIONS:
1. This ENTIRE script is commented out by default for safety
2. Uncomment ALL sections below and replace with YOUR data
3. Run ONLY ONCE: python -m backend.scripts.seed_profile
4. After successful seeding, DO NOT run again (it will delete existing data)

📝 HOW TO USE:
- Uncomment ALL code sections (from ALLOW_SEED to the end)
- Replace placeholder text with your actual information
- Run the script to populate your database
- Comment out again after successful seeding
"""

# import asyncio
# from datetime import date
# from backend.infrastructure.database import SessionLocal
# from backend.data_access.knowledge_base.postgres import (
#     Profile, Skill, Experience, Project
# )


# # ============================================================
# # SAFETY SWITCH - Set to True to enable seeding
# # ============================================================
# ALLOW_SEED = False  # ← Change to True when ready to seed


# # ============================================================
# # YOUR PROFILE DATA - CUSTOMIZE THIS
# # ============================================================

# PROFILE_DATA = {
#     "name": "Your Full Name",  # Replace with your name
#     "email": "your.email@example.com",  # Replace with your email
#     "location": "Your City, Country",  # Replace with your location
#     "summary": (
#         "Your professional summary here. "
#         "Describe your expertise, experience, and career goals. "
#         "This will be shown on your CV page."
#     ),
#     "linkedin_url": "https://linkedin.com/in/your-profile",  # Your LinkedIn URL
#     "github_username": "your-github-username",  # Your GitHub username
# }


# # ============================================================
# # YOUR SKILLS - CUSTOMIZE THIS
# # Format: (skill_name, category)
# # Categories: Backend, Frontend, Database, AI/ML, DevOps, etc.
# # ============================================================

# SKILLS_DATA = [
#     # Programming Languages
#     ("Python", "Backend"),
#     ("JavaScript", "Frontend"),
#     ("TypeScript", "Frontend"),
#     
#     # Frontend Technologies
#     ("React.js", "Frontend"),
#     ("Vue.js", "Frontend"),
#     ("HTML", "Frontend"),
#     ("CSS", "Frontend"),
#     
#     # Backend Technologies
#     ("FastAPI", "Backend"),
#     ("Node.js", "Backend"),
#     ("Django", "Backend"),
#     
#     # Databases
#     ("PostgreSQL", "Database"),
#     ("MongoDB", "Database"),
#     
#     # Add more skills here...
# ]


# # ============================================================
# # YOUR WORK EXPERIENCE - CUSTOMIZE THIS
# # ============================================================

# EXPERIENCES_DATA = [
#     {
#         "company": "Company Name",
#         "role": "Your Role/Title",
#         "start_date": date(2024, 1, 1),  # Start date
#         "end_date": date(2024, 12, 31),  # End date (or None if current)
#         "location": "City, Country",
#         "description": (
#             "• Describe your responsibilities and achievements\n"
#             "• Use bullet points for clarity\n"
#             "• Focus on impact and results\n"
#             "• Include relevant technologies and methodologies"
#         )
#     },
#     # Add more experiences here...
# ]


# # ============================================================
# # YOUR PROJECTS - CUSTOMIZE THIS
# # ============================================================

# PROJECTS_DATA = [
#     {
#         "title": "Project Name",
#         "description": (
#             "Brief description of your project. "
#             "What problem does it solve? "
#             "What technologies did you use? "
#             "What was your role?"
#         ),
#         "tech_stack": [
#             "Python", "FastAPI", "React", "PostgreSQL"
#             # Add technologies used
#         ],
#         "relevance_tags": ["AI", "Full-Stack", "Web"],  # Project categories
#         "github_url": "https://github.com/yourusername/project",  # Optional
#         "demo_url": "https://yourproject.com",  # Optional
#     },
#     # Add more projects here...
# ]


# # ============================================================
# # SEEDING FUNCTION - DO NOT MODIFY THIS PART
# # ============================================================

# async def seed_profile():
#     """Seed profile data into database."""
#     
#     # Safety check
#     if not ALLOW_SEED:
#         print("=" * 70)
#         print("⚠️  SEEDING IS DISABLED")
#         print("=" * 70)
#         print("")
#         print("This script will DELETE existing profile_id=1 data and create new data.")
#         print("")
#         print("To use this script:")
#         print("  1. Uncomment ALL code sections (from imports to the end)")
#         print("  2. Replace placeholder values with YOUR information")
#         print("  3. Set ALLOW_SEED = True")
#         print("  4. Run: python -m backend.scripts.seed_profile")
#         print("  5. After successful seeding, comment out all code again")
#         print("")
#         print("=" * 70)
#         return
#     
#     # Confirmation prompt
#     print("=" * 70)
#     print("⚠️  WARNING: This will DELETE profile_id=1 and all related data!")
#     print("=" * 70)
#     print(f"Profile Name: {PROFILE_DATA['name']}")
#     print(f"Skills Count: {len(SKILLS_DATA)}")
#     print(f"Experiences Count: {len(EXPERIENCES_DATA)}")
#     print(f"Projects Count: {len(PROJECTS_DATA)}")
#     print("=" * 70)
#     response = input("Type 'yes' to continue: ")
#     
#     if response.lower() != "yes":
#         print("Seeding cancelled.")
#         return
#     
#     db = SessionLocal()
#     
#     try:
#         # Delete existing profile
#         existing_profile = db.query(Profile).filter(Profile.id == 1).first()
#         if existing_profile:
#             db.query(Skill).filter(Skill.profile_id == 1).delete()
#             db.query(Experience).filter(Experience.profile_id == 1).delete()
#             db.query(Project).filter(Project.profile_id == 1).delete()
#             db.delete(existing_profile)
#             db.commit()
#             print("✅ Deleted existing profile data")
#         
#         # Create new profile
#         profile = Profile(**PROFILE_DATA)
#         db.add(profile)
#         db.flush()
#         
#         print(f"✅ Created profile: {profile.name} (ID: {profile.id})")
#         
#         # Create skills
#         for skill_name, category in SKILLS_DATA:
#             skill = Skill(
#                 profile_id=profile.id,
#                 name=skill_name,
#                 category=category,
#                 proficiency_level="Proficient",
#             )
#             db.add(skill)
#         
#         print(f"✅ Created {len(SKILLS_DATA)} skills")
#         
#         # Create experiences
#         for exp_data in EXPERIENCES_DATA:
#             experience = Experience(
#                 profile_id=profile.id,
#                 **exp_data
#             )
#             db.add(experience)
#         
#         print(f"✅ Created {len(EXPERIENCES_DATA)} experiences")
#         
#         # Create projects
#         for proj_data in PROJECTS_DATA:
#             project = Project(
#                 profile_id=profile.id,
#                 **proj_data
#             )
#             db.add(project)
#         
#         print(f"✅ Created {len(PROJECTS_DATA)} projects")
#         
#         # Commit all changes
#         db.commit()
#         db.refresh(profile)
#         
#         print("\n" + "=" * 70)
#         print("🎉 SEEDING COMPLETE!")
#         print("=" * 70)
#         print(f"Profile: {profile.name}")
#         print(f"Skills: {len(SKILLS_DATA)}")
#         print(f"Experiences: {len(EXPERIENCES_DATA)}")
#         print(f"Projects: {len(PROJECTS_DATA)}")
#         print("=" * 70)
#         print("")
#         print("⚠️  IMPORTANT: Comment out all code again to prevent accidental re-runs!")
#         print("")
#         print("Next steps:")
#         print("  1. Run vector ingestion: python -m backend.scripts.ingest_profile")
#         print("  2. Start backend: uvicorn backend.main:app --reload")
#         print("  3. Check http://localhost:8000/api/profile/1/full")
#         print("")
#         
#     except Exception as e:
#         db.rollback()
#         print(f"❌ Error: {e}")
#         raise
#     
#     finally:
#         db.close()


# if __name__ == "__main__":
#     asyncio.run(seed_profile())