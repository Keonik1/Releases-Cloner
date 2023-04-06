from git_provider import *


def releases_cloner(
    source_repo : tuple,
    destination_repo : tuple
):
    source_repo_provider, source_repo_url, source_headers  = source_repo
    destination_repo_provider, destination_repo_url, destination_headers = destination_repo
    source = GitProvider(source_repo_provider, source_repo_url, source_headers) # type: ignore
    destination = GitProvider(destination_repo_provider, destination_repo_url, destination_headers) # type: ignore
    releases_list = source.get_releases()
    destination.send_releases(releases_list)


# source_repo = "github", "https://github.com/<namespace>/<repo>", {"Authorization": "Bearer private_access_token"} #private
source_repo = "github", "https://github.com/<namespace>/<repo>", {} # public
destination_repo = "gitlab", "https://gitlab.com/<namespace>/<repo>", {"PRIVATE-TOKEN": "private_access_token"}
# source_repo = "gitlab", "https://gitlab.com/<namespace>/<repo>", {} # public 
# destination_repo = "github", "https://github.com/<namespace>/<repo>", {"Authorization": "Bearer private_access_token"}
releases_cloner(source_repo, destination_repo)