"""Helpers for merging project-level and global git configuration."""


def merge_git_config(project_config: dict, global_config: dict) -> dict:
    """Merge project-level git config with global fallback.

    Identity layer (git_author_name + git_author_email):
      Both name AND email must be present on the project to use project-level identity.
      If either is missing, fall back to the global config entirely.

    Credential layer:
      Each credential field is merged individually with project taking priority.
      This allows both SSH and HTTPS credentials to be available simultaneously,
      so the correct one is used regardless of the remote URL protocol.
    """
    result: dict = {}

    # Identity: all-or-nothing
    if project_config.get("git_author_name") and project_config.get("git_author_email"):
        result["git_author_name"] = project_config["git_author_name"]
        result["git_author_email"] = project_config["git_author_email"]
    else:
        result["git_author_name"] = global_config.get("git_author_name")
        result["git_author_email"] = global_config.get("git_author_email")

    # Credential: merge each field individually, project overrides global
    for field in ("git_credential_type", "git_ssh_key_path",
                  "git_https_username", "git_https_token"):
        result[field] = project_config.get(field) or global_config.get(field)

    return result


def settings_to_dict(settings_obj) -> dict:
    """Convert a GlobalSettings ORM object (or None) to a plain dict."""
    if settings_obj is None:
        return {}
    return {
        "git_author_name": settings_obj.git_author_name,
        "git_author_email": settings_obj.git_author_email,
        "git_credential_type": settings_obj.git_credential_type,
        "git_ssh_key_path": settings_obj.git_ssh_key_path,
        "git_https_username": settings_obj.git_https_username,
        "git_https_token": settings_obj.git_https_token,
    }
