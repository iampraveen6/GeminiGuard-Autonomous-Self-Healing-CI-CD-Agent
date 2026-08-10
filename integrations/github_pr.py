import os
from github import Github
from datetime import datetime


def categorize_error_type(logs, fix_description):
    """
    Categorize the type of error based on logs and fix description
    
    Returns:
        tuple: (error_type, guidance_message)
        error_type: 'application', 'infrastructure', 'external', 'unknown'
    """
    logs_lower = logs.lower() if logs else ""
    fix_lower = fix_description.lower()
    
    # Check for actual build/compilation errors (highest priority)
    build_error_keywords = [
        'compilation failed', 'cannot find symbol', 'error: cannot find',
        'cannot find symbol', 'symbol:   method', 'symbol:   class',
        'compilation failure', 'build failed', ':compileJava FAILED',
        'javac error', 'error: cannot access', 'package does not exist',
        'class not found', 'method not found', 'illegal start of expression',
        'incompatible types', 'cannot resolve symbol', 'missing return statement'
    ]
    
    if any(kw in logs_lower for kw in build_error_keywords):
        return 'application', "Build/compilation error detected. This is a code issue that can be fixed with PR."
    
    # Check for dependency issues
    dependency_keywords = [
        'module not found', 'no module named', 'import error',
        'missing dependency', 'package not found', 'cannot import',
        'dependency not found', 'unresolved dependency'
    ]
    
    if any(kw in logs_lower for kw in dependency_keywords):
        return 'application', "Dependency/Import error detected. This is a code issue that can be fixed with PR."
    
    # Check for syntax/code errors
    syntax_error_keywords = [
        'syntax error', 'unexpected token', 'unexpected end',
        'indentationerror', 'invalid syntax', 'parse error',
        'unexpected indent', 'dedent mismatch'
    ]
    
    if any(kw in logs_lower for kw in syntax_error_keywords):
        return 'application', "Syntax error detected. This is a code issue that can be fixed with PR."
    
    # Only categorize as infrastructure if NO build/compilation errors are found
    infrastructure_keywords = [
        'pod failed', 'pod crashloopbackoff', 'oomkilled', 'imagepullback',
        'node not ready', 'insufficient resources', 'timeout waiting for pod',
        'network unreachable', 'dns resolution failed', 'connection refused',
        'certificate error', 'authentication failed'
    ]
    
    infrastructure_matches = sum(1 for kw in infrastructure_keywords if kw in logs_lower)
    if infrastructure_matches >= 2:
        # But check if the infrastructure was actually the cause (not just setup logs)
        # If the job ran for a while and then failed, it's likely not infrastructure
        job_ran_keywords = ['executing "step_script"', 'running on runner', 'getting source', 'compiling', 'building']
        if any(kw in logs_lower for kw in job_ran_keywords):
            # Infrastructure setup succeeded, failure happened later
            return 'application', "Infrastructure setup succeeded, but build failed. This is a code issue."
        else:
            return 'infrastructure', "Infrastructure setup failed before code execution. This requires DevOps intervention."
    
    # Check for external service issues
    external_service_keywords = [
        'artifactory', 'jfrog', 'nexus', 'gitlab', 'github', 'bitbucket',
        'sonarqube', 'jenkins', 'aws', 'azure', 'gcp', 'database',
        'api gateway', 'service mesh', 'vault', 'ldap', 'sso',
        'connection refused', 'timeout connecting', 'service unavailable'
    ]
    
    external_matches = sum(1 for kw in external_service_keywords if kw in logs_lower)
    if external_matches >= 2:
        return 'external', "External service issue detected. This may require service team coordination."
    
    # Check if fix suggests code changes
    code_change_keywords = ['code', 'function', 'class', 'import', 'file', 'variable', 'method', 'class', 'interface']
    if any(kw in fix_lower for kw in code_change_keywords):
        return 'application', "Application code issue detected. Can be fixed with code changes."
    
    return 'unknown', "Error type unclear. Manual review required."


def validate_fix_relevance(fix_description, logs):
    """
    Validate if the fix is relevant to the logs and source code
    
    Args:
        fix_description: The AI-generated fix description
        logs: The original CI/CD logs
        
    Returns:
        tuple: (is_valid, validation_message, confidence_score, detailed_report)
    """
    # Categorize error type first
    error_type, guidance_message = categorize_error_type(logs, fix_description)
    
    # Detailed validation report
    validation_report = {
        'checks': [],
        'score_breakdown': {},
        'passed_checks': 0,
        'failed_checks': 0,
        'error_type': error_type,
        'guidance': guidance_message
    }
    
    # Check 1: Technical keywords
    technical_keywords = ['install', 'update', 'fix', 'change', 'modify', 'add', 'remove', 'configure', 'set', 'enable', 'disable', 'implement', 'refactor']
    found_keywords = [kw for kw in technical_keywords if kw in fix_description.lower()]
    has_technical_action = len(found_keywords) > 0
    
    check_result = {
        'name': 'Technical Action Keywords',
        'status': 'PASS' if has_technical_action else 'FAIL',
        'details': f"Found {len(found_keywords)} action keywords: {', '.join(found_keywords) if found_keywords else 'None'}",
        'score': 30 if has_technical_action else 0
    }
    validation_report['checks'].append(check_result)
    validation_report['score_breakdown']['technical_keywords'] = check_result['score']
    if has_technical_action:
        validation_report['passed_checks'] += 1
    else:
        validation_report['failed_checks'] += 1
    
    # Check 2: File references
    file_references = ['requirements.txt', 'package.json', 'dockerfile', '.env', 'config', 'yaml', 'yml', 'json', 'py', 'js', 'ts', 'java', 'go', 'rs']
    found_files = [ref for ref in file_references if ref in fix_description.lower()]
    has_file_reference = len(found_files) > 0
    
    check_result = {
        'name': 'File/Configuration References',
        'status': 'PASS' if has_file_reference else 'FAIL',
        'details': f"Found {len(found_files)} file references: {', '.join(found_files) if found_files else 'None'}",
        'score': 40 if has_file_reference else 0
    }
    validation_report['checks'].append(check_result)
    validation_report['score_breakdown']['file_references'] = check_result['score']
    if has_file_reference:
        validation_report['passed_checks'] += 1
    else:
        validation_report['failed_checks'] += 1
    
    # Check 3: Content substance
    is_substantial = len(fix_description) > 20
    is_very_substantial = len(fix_description) > 50
    
    substance_score = 10 if is_substantial else 0
    if is_very_substantial:
        substance_score = 20
    
    check_result = {
        'name': 'Content Substance',
        'status': 'PASS' if is_substantial else 'FAIL',
        'details': f"Description length: {len(fix_description)} characters (min: 20)",
        'score': substance_score
    }
    validation_report['checks'].append(check_result)
    validation_report['score_breakdown']['content_substance'] = check_result['score']
    if is_substantial:
        validation_report['passed_checks'] += 1
    else:
        validation_report['failed_checks'] += 1
    
    # Check 4: Log relevance (bonus)
    log_relevance_score = 0
    if logs:
        # Check if fix mentions errors from logs
        log_keywords = ['error', 'failed', 'timeout', 'exception', 'missing', 'not found', 'connection']
        found_log_keywords = [kw for kw in log_keywords if kw in logs.lower() and kw in fix_description.lower()]
        if len(found_log_keywords) > 0:
            log_relevance_score = 10
        
        check_result = {
            'name': 'Log Relevance (Bonus)',
            'status': 'PASS' if log_relevance_score > 0 else 'INFO',
            'details': f"Found {len(found_log_keywords)} matching keywords in both logs and fix",
            'score': log_relevance_score
        }
        validation_report['checks'].append(check_result)
        validation_report['score_breakdown']['log_relevance'] = log_relevance_score
    
    # Calculate total confidence score
    confidence_score = sum(validation_report['score_breakdown'].values())
    
    # Validation decision - consider error type
    if error_type in ['infrastructure', 'external']:
        is_valid = False  # Don't create PRs for infrastructure/external issues
        confidence_score = 0  # Override score for non-application errors
        validation_message = f"{guidance_message} Error type: {error_type.upper()}. PR creation disabled for this error type."
    else:
        is_valid = confidence_score >= 50
        if is_valid:
            validation_message = f"Fix appears relevant (confidence: {confidence_score}%) - {validation_report['passed_checks']}/{len(validation_report['checks'])} checks passed"
        else:
            failed_check_names = [check['name'] for check in validation_report['checks'] if check['status'] == 'FAIL']
            validation_message = f"Fix may not be actionable (confidence: {confidence_score}%) - Failed: {', '.join(failed_check_names)}"
    
    return is_valid, validation_message, confidence_score, validation_report


def create_fix_pr(fix_description, logs=None, branch_type="feature"):
    """
    Create a GitHub PR with an AI-generated fix
    
    Args:
        fix_description: Description of the fix
        logs: Original CI/CD logs for validation (optional)
        branch_type: Type of branch - "feature" or "hotfix" (default: "feature")
    """

    # Note: PR creation uses GitHub API, not Gemini API, so TEST_MODE doesn't block it
    # TEST_MODE only affects Gemini API calls in gemini_client.py

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_NAME = os.getenv("REPO_NAME") or os.getenv("GITHUB_REPO")

    if not GITHUB_TOKEN or not REPO_NAME:
        return "Missing GitHub configuration"

    # Validate fix relevance
    is_valid, validation_message, confidence_score, validation_report = validate_fix_relevance(fix_description, logs or "")
    
    if not is_valid:
        # Extract error type and guidance from validation report
        error_type = validation_report.get('error_type', 'unknown')
        guidance = validation_report.get('guidance', 'No guidance available')
        
        # Build detailed failure message
        detailed_failure = f"Validation failed: {validation_message}\n\n**Error Type:** {error_type.upper()}\n**Guidance:** {guidance}\n\n**Detailed Report:**\n"
        for check in validation_report['checks']:
            icon = "✅" if check['status'] == 'PASS' else "❌"
            detailed_failure += f"{icon} **{check['name']}** ({check['status']}): {check['details']}\n"
        
        return detailed_failure

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

        # Create more meaningful fix documentation
        file_path = "AI_FIX_NOTES.md"
        
        # Build detailed validation section
        validation_details = "\n".join([
            f"- **{check['name']}** ({check['status']}): {check['details']}" 
            for check in validation_report['checks']
        ])
        
        content = f"""# AI-Generated Fix Notes

## Fix Description
{fix_description}

## Validation Results
- **Overall Status:** {'PASSED' if is_valid else 'FAILED'}
- **Confidence Score:** {confidence_score}%
- **Branch Type:** {branch_type}
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Detailed Validation Report
{validation_details}

## Score Breakdown
- Technical Keywords: {validation_report['score_breakdown'].get('technical_keywords', 0)}%
- File References: {validation_report['score_breakdown'].get('file_references', 0)}%
- Content Substance: {validation_report['score_breakdown'].get('content_substance', 0)}%
- Log Relevance: {validation_report['score_breakdown'].get('log_relevance', 0)}%

## Implementation Notes
This fix was automatically generated by GeminiGuard based on CI/CD log analysis.
Please review and implement the suggested changes manually.

## Related Logs
```
{logs[:500] if logs else "No logs provided"}
```

---
*Automatically created by GeminiGuard CI/CD Analyzer*
"""

        try:
            contents = repo.get_contents(file_path, ref=new_branch)
            repo.update_file(
                path=contents.path,
                message="Update AI fix notes",
                content=content,
                sha=contents.sha,
                branch=new_branch
            )
            print("Updated existing fix notes")
        except Exception:
            repo.create_file(
                path=file_path,
                message="Add AI fix notes",
                content=content,
                branch=new_branch
            )
            print("Created new fix notes")

        # Create Pull Request with enhanced information
        validation_details = "\n".join([
            f"- **{check['name']}** ({check['status']}): {check['details']}" 
            for check in validation_report['checks']
        ])
        
        pr = repo.create_pull(
            title=pr_title,
            body=f"""## AI-Generated Fix

### Validation Results
- **Status:** {validation_message}
- **Confidence:** {confidence_score}%
- **Branch Type:** {branch_type}

### Detailed Validation Report
{validation_details}

### Score Breakdown
- Technical Keywords: {validation_report['score_breakdown'].get('technical_keywords', 0)}%
- File References: {validation_report['score_breakdown'].get('file_references', 0)}%
- Content Substance: {validation_report['score_breakdown'].get('content_substance', 0)}%
- Log Relevance: {validation_report['score_breakdown'].get('log_relevance', 0)}%

### Proposed Fix
{fix_description}

### Implementation Required
This PR contains documentation for the AI-suggested fix. Please:
1. Review the fix notes in `AI_FIX_NOTES.md`
2. Implement the suggested changes manually
3. Test the changes
4. Update this PR with actual code modifications

### Context
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Analyzer:** GeminiGuard CI/CD
- **Branch:** `{new_branch}`

---
*Please review and implement the fix manually. This PR provides documentation and validation for the AI-suggested solution.*
""",
            head=new_branch,
            base=base_branch
        )

        # Build detailed success message
        error_type = validation_report.get('error_type', 'unknown')
        detailed_success = f"PR Created: {pr.html_url}\n\n**Error Type:** {error_type.upper()}\n**Validation Summary:** {validation_message}\n\n**Detailed Report:**\n"
        for check in validation_report['checks']:
            icon = "✅" if check['status'] == 'PASS' else "❌"
            detailed_success += f"{icon} **{check['name']}** ({check['status']}): {check['details']}\n"
        
        return detailed_success

    except Exception as e:
        return f"GitHub Error: {str(e)}"