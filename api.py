import requests as rq
USERNAME = "VED2RISE"

def fetch(username):
    try:
        final=[]
        endpoint = f"https://api.github.com/users/{username}/repos"
        params = {
            "type": "public"
        }
        response = rq.get(url=endpoint, params=params)
        response.raise_for_status()

        repos = response.json()


        repo_info = [{ "name": repo["name"], 
                       "url": repo["html_url"], 
                       "description": repo["description"] or "No description" } 
                     for repo in repos]

        for repo in repo_info:
            final.append(f"Name: {repo['name']}, URL: {repo['url']}, Description: {repo['description']}")
        final_output = "\n".join(final)
        print(final_output)

    except rq.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return []
    except rq.RequestException as e:
        print(f"Request error occurred: {e}")
        return []

fetch(USERNAME)