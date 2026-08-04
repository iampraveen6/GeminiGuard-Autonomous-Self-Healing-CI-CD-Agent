import os
from github import Github
from datetime import datetime


def create_fix_pr(fix_description, branch_type="feature"):
    """
    Create a GitHub PR with an AI-generated fix
    
    Args:
        fix_description: Description of the fix
        branch_type: Type of branch - "feature" or "hotfix" (default: "feature")
    """

    # TEST MODE → Skip PR
    if os.getenv("TEST_MODE") == "true":
        return "PR skipped (TEST MODE)"

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_NAME = os.getenv("REPO_NAME") or os.getenv("GITHUB_REPO")

    if not GITHUB_TOKEN or not REPO_NAME:
        return "Missing GitHub configuration"

    try:
        g = Github(GITHUB_TOKEN)

        repo = g.get_repo(REPO_NAME)

        print(f"Connected to repo: {repo.full_name}")

        base_branch = repo.default_branch
        
        # Generate descriptive branch name based on type
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        if branch_type == "hotfix":
            branch_prefix = "hotfix"
            pr_title = "Hotfix: GeminiGuard Auto Fix"
        else:
            branch_prefix = "feature"
            pr_title = "Feature: GeminiGuard Auto Fix"
        
        # Create short description slug for branch name
        desc_slug = fix_description[:30].replace(' ', '-').lower().replace('/', '-').replace('\\', '-')
        new_branch = f"{branch_prefix}/ai-fix-{timestamp}-{desc_slug}"

        # Create Branch
        source = repo.get_branch(base_branch)

        repo.create_git_ref(
            ref=f"refs/heads/{new_branch}",
            sha=source.commit.sha
        )

        # Create / Update File
        file_path = "auto_fix.txt"
        content = f"AI Fix Applied:\n\n{fix_description}\n"

        try:
            contents = repo.get_contents(file_path, ref=new_branch)

            repo.update_file(
                path=contents.path,
                message="AI auto-fix update",
                content=content,
                sha=contents.sha,
                branch=new_branch
            )

            print("Updated existing file")

        except Exception:
            repo.create_file(
                path=file_path,
                message="AI auto-fix created",
                content=content,
                branch=new_branch
            )

            print("Created new file")

        # Create Pull Request
        pr = repo.create_pull(
            title=pr_title,
            body=f"""
### AI Generated Fix

**Branch Type:** {branch_type.capitalize()}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{fix_description}

---

Automatically created by GeminiGuard
""",
            head=new_branch,
            base=base_branch
        )

        return f"PR Created: {pr.html_url}"

    except Exception as e:
        return f"GitHub Error: {str(e)}"