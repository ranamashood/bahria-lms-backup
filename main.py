import requests
import os
from bs4 import BeautifulSoup

session = requests.Session()

session_cookie = input("Enter session cookie: ")

if not session_cookie:
    raise SystemExit("Set session cookie value first")

cookies = {
    "PHPSESSID": session_cookie,
}
session.cookies.update(cookies)

headers = {
    "Cookie": f"PHPSESSID={session_cookie}",
}

url = "https://lms.bahria.edu.pk/Student/Dashboard.php"
response = session.get(url, headers=headers)

if response.url != url:
    raise SystemExit("Session cookie value is not correct")

print("Logged in to LMS")

backup_path = "LMS Backup"
os.makedirs(backup_path, exist_ok=True)

soup = BeautifulSoup(response.text, "html.parser")

url = "https://lms.bahria.edu.pk/Student/CourseOutline.php"
response = session.get(url, headers=headers)

semesters = {
    option.text.strip(): str(option["value"])
    for option in reversed(soup.select("#semesterId option"))
}

for key, value in list(semesters.items()):
    url = f"https://lms.bahria.edu.pk/Student/CourseOutline.php?s={value}"
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    if len(soup.select("table td")) == 1:
        semesters.pop(key)


def download_file(url_param: str, dir_path: str, prefix: str):
    if not url_param:
        return

    if prefix:
        prefix += " - "

    url = f"https://lms.bahria.edu.pk/Student/{url_param}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return

    filename = response.headers["content-disposition"].split('filename="')[1][:-1]
    filepath = f"{dir_path}/{prefix}{filename}"

    with open(filepath, "wb") as file:
        file.write(response.content)


def get_soup(url: str):
    response = session.get(url, headers=headers)
    return BeautifulSoup(response.text, "html.parser")


def scrape_papers(soup: BeautifulSoup):
    items = {
        cells[1].text.strip(): {
            "upload": [cells[2].find("a").get("href") if cells[2].find("a") else ""],
            "submission": cells[4].find("a").get("href") if cells[4].find("a") else "",
        }
        for row in soup.select("tr")
        if (len(cells := row.find_all("td")) > 1)
    }

    return items


def scrape_lecture_notes(soup: BeautifulSoup):
    items = {
        cells[1].text.strip(): {
            "upload": [link.get("href") for link in cells[2].find_all("a")],
        }
        for row in soup.select("tr")
        if (len(cells := row.find_all("td")) > 1)
    }

    return items


def scrape_assignments(soup: BeautifulSoup):
    items = {
        cells[1].text.strip(): {
            "upload": [cells[2].find("a").get("href") if cells[2].find("a") else ""],
            "submission": cells[3].find("a").get("href") if cells[3].find("a") else "",
            "solution": cells[2].find_all("a")[-1]["href"]
            if len(cells[2].find_all("a")) == 2
            else "",
        }
        for row in soup.select("tr")
        if (len(cells := row.find_all("td")) > 1)
    }

    return items


def scrape_quizzes(soup: BeautifulSoup):
    items = {
        cells[1].text.strip(): {
            "upload": [cells[2].find("a").get("href") if cells[2].find("a") else ""],
            "solution": cells[4].find("a").get("href") if cells[4].find("a") else "",
        }
        for row in soup.select("tr")
        if (len(cells := row.find_all("td")) > 1)
    }

    return items


data = [
    {"name": "Papers", "scraper": scrape_papers},
    {"name": "Lecture Notes", "scraper": scrape_lecture_notes},
    {"name": "Assignments", "scraper": scrape_assignments},
    {"name": "Quizzes", "scraper": scrape_quizzes},
]


def download_item(
    item: dict, semester: str, course: str, semester_id: str, course_id: str
):
    name = item["name"].replace(" ", "")

    # won: with out name
    dir_path_won = f"{backup_path}/{semester}/{course}"
    dir_path = f"{backup_path}/{semester}/{course}/{item['name']}"

    soup = get_soup(
        f"https://lms.bahria.edu.pk/Student/{name}.php?s={semester_id}&oc={course_id}"
    )

    items = item["scraper"](soup)

    os.makedirs(dir_path, exist_ok=True)

    if not len(items):
        os.rename(
            dir_path,
            f"{dir_path_won}/{item['name']} (Empty)",
        )

    for i, item in enumerate(items):
        new_dir_path = f"{dir_path}/{i + 1:02} - {item}"

        os.makedirs(new_dir_path, exist_ok=True)

        for upload in items[item]["upload"]:
            download_file(upload, new_dir_path, "Upload")

        if items[item].get("submission"):
            download_file(items[item]["submission"], new_dir_path, "Submission")

        if items[item].get("solution"):
            download_file(items[item]["solution"], new_dir_path, "Solution")


for semester in semesters:
    os.makedirs(f"{backup_path}/{semester}", exist_ok=True)

    url = f"https://lms.bahria.edu.pk/Student/CoursePlan.php?s={semesters[semester]}"
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    courses = {
        option.text.strip(): str(option["value"])
        for option in soup.select("#courseId option")
    }
    courses.pop("Select Course")

    for course in courses:
        os.makedirs(f"{backup_path}/{semester}/{course}/Course Outline", exist_ok=True)

        for item in data:
            download_item(item, semester, course, semesters[semester], courses[course])

    ############################
    ###### Course Outline ######
    ############################

    url = f"https://lms.bahria.edu.pk/Student/CourseOutline.php?s={semesters[semester]}"
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    course_outlines = {
        cells[1].text.strip(): (
            cells[2].find("a").get("href") if cells[2].find("a") else ""
        )
        for row in soup.select("tr")
        if (cells := row.find_all("td"))
    }

    for course in course_outlines:
        url = f"https://lms.bahria.edu.pk/Student/{course_outlines[course]}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200 or not course_outlines[course]:
            os.rename(
                f"{backup_path}/{semester}/{course}/Course Outline",
                f"{backup_path}/{semester}/{course}/Course Outline (Empty)",
            )
            continue

        filename = response.headers["content-disposition"].split('filename="')[1][:-1]
        filepath = f"{backup_path}/{semester}/{course}/Course Outline/{filename}"

        with open(filepath, "wb") as file:
            file.write(response.content)
