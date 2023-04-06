from datetime import datetime
import requests


class GitProvider:
    def __get_url_info(self, url : str):
        protocol_prefix_end_index = url.index("://") + 3
        domain_name_end_index = url.index("/", protocol_prefix_end_index) + 1
        return (protocol_prefix_end_index, domain_name_end_index)
    
    def __get_github_api_url(self, repository_url):
        protocol_prefix_end_index, domain_name_end_index = self.__get_url_info(repository_url)
        api_url = repository_url[:domain_name_end_index] + "repos/" + repository_url[domain_name_end_index:]
        api_url = api_url[:protocol_prefix_end_index] + "api." + api_url[protocol_prefix_end_index:]
        return api_url

    def __get_gitlab_api_url(self, repository_url):
        _, domain_name_end_index = self.__get_url_info(repository_url)
        project_path = repository_url[domain_name_end_index:]
        project_path = project_path.replace("/", "%2F")
        api_url = repository_url[:domain_name_end_index] + "api/v4/projects/" + project_path
        return api_url
    
    def __init__(self, git_provider : str, repo_url : str, headers={}):
        self.__fields = {
            "name": "",
            "tag_name": "",
            "date": "",
            "description": ""
        }
        self.__git_provider = git_provider.lower()
        self.__repo_url = repo_url
        self.__fields["name"] = "name"
        self.__fields["tag_name"] = "tag_name"
        self.__default_date_format = "%Y-%m-%dT%H:%M:%SZ"
        if self.__git_provider == "github":
            self.__fields["release_date"] = "published_at" #Not working for github
            self.__fields["description"] = "body"
            self.__api_url = self.__get_github_api_url(repo_url)
            self.__headers = {"Accept": "application/vnd.github+json"}
            self.__headers.update(headers)
            self.__error_message_path = ['errors', 0, 'code']
            self.__date_format = "%Y-%m-%dT%H:%M:%SZ"
        elif self.__git_provider == "gitlab" :
            self.__fields["release_date"] = "released_at"
            self.__fields["description"] = "description"
            self.__api_url = self.__get_gitlab_api_url(repo_url)
            self.__headers = headers
            self.__error_message_path = ['message']
            self.__date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        else:
            raise ValueError(f"{self.__git_provider} is unknown git provider! Must be 'github' or 'gitlab'.")
        
    
    def get_repo_url(self):
        return self.__repo_url
    
    def get_api_url(self):
        return self.__api_url
    
    def get_fields(self):
        return self.__fields
    
    def get_headers(self):
        return self.__headers
    
    def get_git_provider(self):
        return self.__git_provider
    
    def __format_releases(self, releases : list):
        releases_list = []
        for release in releases:
            release_name = release[self.__fields["name"]]
            if release_name == "":
                release_name = release[self.__fields["tag_name"]]
            release_date = release[self.__fields["release_date"]]
            release_date = datetime.strptime(release_date, self.__date_format)
            release_date = release_date.strftime(self.__default_date_format)
            preformatted_release = {
                "name" : release_name,
                "tag_name" : release[self.__fields["tag_name"]],
                "release_date" : release_date,
                "description" : release[self.__fields["description"]],
            }
            releases_list.append(preformatted_release)
        return releases_list
    
    def __get_releases_list(self, request_url, raw=False):
        releases = requests.get(request_url, headers=self.__headers)
        releases = releases.json()
        if raw:
            return releases
        return self.__format_releases(releases)
    
    def get_releases(self, sort_first2latest=True):
        base_releases_api_url = self.__api_url + "/releases"
        releases_list = []
        is_releases_raw = False
        page_number = 1
        while True:
            releases_api_url = f"{base_releases_api_url}?per_page=100&page={page_number}"
            releases = self.__get_releases_list(releases_api_url, is_releases_raw)
            releases_list.extend(releases)                
            if len(releases) != 100:
                break
        if sort_first2latest:
            releases_list.reverse()
        return releases_list
    
    def send_releases(self, releases_list : list):
        def get_error_reason(response : dict, path : list):
            for item in path:
                response = response[item]
            return response
        
        releases_api_url = self.__api_url + "/releases"
        for release in releases_list:
            print(release["release_date"])
            post_release = requests.post(
                releases_api_url, headers=self.__headers, verify=True,
                json={
                    self.__fields["name"]: release["name"],
                    self.__fields["tag_name"]: release["tag_name"],
                    self.__fields["release_date"]: release["release_date"],
                    self.__fields["description"]: release["description"],
                }
            )
            print(f"Release name: {release['name']}")
            if post_release.status_code == 201:
                print("Status: Successfully created\n")
            else:
                print(f"Status: {get_error_reason(post_release.json(), self.__error_message_path)}\n")