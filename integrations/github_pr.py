import os
from github import Github
from datetime import datetime


def create_fix_pr(fix_description):
    """
    Create a GitHub PR with an AI-generated fix
    """

    # -------------------------
    # ✅ TEST MODE → Skip PR
    # -------------------------
    if os.getenv("TEST_MODE") == "true":
        return "✅ PR skipped (TEST MODE)"

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_NAME = os.getenv("REPO_NAME") or os.getenv("GITHUB_REPO")

    if not GITHUB_TOKEN or not REPO_NAME:
        return "⚠️ Missing GitHub configuration"

    try:
        # ✅ Handle SSL issue (dev environments)
        g = Github(GITHUB_TOKEN, verify=False)

        repo = g.get_repo(REPO_NAME)

        print(f"✅ Connected to repo: {repo.full_name}")

        base_branch = repo.default_branch
        new_branch = f"ai-fix-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # -------------------------
        # ✅ Create Branch
        # -------------------------
        source = repo.get_branch(base_branch)

        repo.create_git_ref(
            ref=f"refs/heads/{new_branch}",
            sha=source.commit.sha
        )

        # -------------------------
        # ✅ Create / Update File
        # -------------------------
        file_path = "auto_fix.txt"
        content = f"AI Fix Applied:\n\n{fix_description}\n"

        try:
            contents = repo.get_contents(file_path, ref=new_branch)

            repo.update_file(
                path=contents.path,
                message="🤖 AI auto-fix update",
                content=content,
                sha=contents.sha,
                branch=new_branch
            )

            print("✅ Updated existing file")

        except Exception:
            repo.create_file(
                path=file_path,
                message="🤖 AI auto-fix created",
                content=content,
                branch=new_branch
            )

            print("✅ Created new file")

        # -------------------------
        # ✅ Create Pull Request
        # -------------------------
        pr = repo.create_pull(
            title="🤖 GeminiGuard Auto Fix",
            body=f"""
### 🚀 AI Generated Fix

{fix_description}

---

✅ Automatically created by GeminiGuard  
""",
            head=new_branch,
            base=base_branch
        )

        return f"✅ PR Created: {pr.html_url}"

    except Exception as e:
        return f"❌ GitHub Error: {str(e)}"