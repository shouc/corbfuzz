from github import Github
g = Github("REPLACE ME", per_page=1000) # put your GitHub API token here

repositories = g.search_code(query='mysqli language:php', sort="indexed")
# repositories2 = g.search_code(query='language:php')
arr = set()

def crawl(i):
    for j in repositories.get_page(i):
        arr.add(j.repository.full_name)
print("If the error is rate limit exceeds, it is expected and the script is exited as expected.")

for i in range(1, 1000):
    try:
        print(i)
        crawl(i)
    except Exception as e:
        print(e)
        break


print(len(arr))
with open("repos.txt", "w") as fp:
    import json
    json.dump(list(arr), fp)
