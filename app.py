from flask import Flask, jsonify
from flask_restful import Api, Resource
from bs4 import BeautifulSoup as bs
import requests


app = Flask(__name__)
api = Api(app)


class Scraper:
    def __init__(self, username):
        self.username = username

    def fetchResponse(self):
        BASE_URL = f'https://auth.geeksforgeeks.org/user/{self.username}/practice/'

        def extract_text_from_elements(elements, element_keys):
            result = {}
            index = 0
            for element in elements:
                try:
                    inner_text = element.text
                    if inner_text == '_ _':
                        result[element_keys[index]] = ""
                    else:
                        result[element_keys[index]] = inner_text
                except:
                    result[element_keys[index]] = ""
                index += 1
            return result

        def extract_details(soup):
            basic_details_by_index = ["institution", "languagesUsed"]
            coding_scores_by_index = ["codingScore", "totalProblemsSolved", "monthlyCodingScore", "articlesPublished"]
            basic_details = soup.find_all("div", class_="basic_details_data")
            coding_scores = soup.find_all("span", class_="score_card_value")
            response = {}
            response["basic_details"] = extract_text_from_elements(basic_details, basic_details_by_index)
            response["coding_scores"] = extract_text_from_elements(coding_scores, coding_scores_by_index)
            return response

        def extract_questions_by_difficulty(soup, difficulty):
            try:
                response = {}
                questions = []
                question_list_by_difficulty_tag = soup.find("div", id=difficulty.replace("#", "")).find_all("a")
                response["count"] = len(question_list_by_difficulty_tag)

                for question_tag in question_list_by_difficulty_tag:
                    question = {}
                    question["question"] = question_tag.text
                    question["questionUrl"] = question_tag["href"]
                    questions.append(question)

                response["questions"] = questions
                return response
            except:
                return {"count": 0, "questions": []}

        def extract_questions_solved_count(soup):
            difficulties = ["#school", "#basic", "#easy", "#medium", "#hard"]
            result = {}
            for difficulty in difficulties:
                result[difficulty] = extract_questions_by_difficulty(soup, difficulty)
            return result

        try:
            profilePage = requests.get(BASE_URL)
            profilePage.raise_for_status()  # Raise an exception for bad status codes

            response = {}
            solvedStats = {}
            generalInfo = {}
            soup = bs(profilePage.content, 'html.parser')

            generalInfo["userName"] = self.username

            profile_pic = soup.find("img", class_="profile_pic")
            institute_rank = soup.find("span", class_="rankNum")
            streak_count = soup.find("div", class_="streakCnt")

            try:
                generalInfo["profilePicture"] = profile_pic["src"]
            except:
                generalInfo["profilePicture"] = ""

            try:
                generalInfo["instituteRank"] = institute_rank.text
            except:
                generalInfo["instituteRank"] = ""

            try:
                streak_details = streak_count.text.replace(" ", "").split("/")
                generalInfo["currentStreak"] = streak_details[0]
                generalInfo["maxStreak"] = streak_details[1]
            except:
                generalInfo["currentStreak"] = "00"
                generalInfo["maxStreak"] = "00"

            additional_details = extract_details(soup)
            question_count_details = extract_questions_solved_count(soup)

            for _, value in additional_details.items():
                for _key, _value in value.items():
                    generalInfo[_key] = _value

            for key, value in question_count_details.items():
                solvedStats[key.replace("#", "")] = value

            response["info"] = generalInfo
            response["solvedStats"] = solvedStats
            return response

        except requests.exceptions.RequestException as e:
            return {"error": "Profile Not Found", "details": str(e)}, 404


class GeeksForGeeksAPI(Resource):
    def get(self, username):
        scraper = Scraper(username)
        return scraper.fetchResponse()


@app.route('/')
def home():
    api_docs = {
        "name": "GeeksForGeeks Profile Scraper API",
        "version": "1.0",
        "description": "API to fetch user profiles and coding statistics from GeeksForGeeks",
        "endpoints": {
            "GET /": {
                "description": "API documentation and information"
            },
            "GET /<username>": {
                "description": "Fetch profile data for a specific user",
                "parameters": {
                    "username": "GeeksForGeeks username"
                },
                "returns": {
                    "info": {
                        "userName": "User's username",
                        "profilePicture": "URL to profile picture",
                        "instituteRank": "User's institute rank",
                        "currentStreak": "Current coding streak",
                        "maxStreak": "Maximum coding streak",
                        "institution": "User's institution",
                        "languagesUsed": "Programming languages used",
                        "codingScore": "Overall coding score",
                        "totalProblemsSolved": "Total problems solved",
                        "monthlyCodingScore": "Monthly coding score",
                        "articlesPublished": "Number of articles published"
                    },
                    "solvedStats": {
                        "school": {"count": "Number of school level problems", "questions": []},
                        "basic": {"count": "Number of basic level problems", "questions": []},
                        "easy": {"count": "Number of easy level problems", "questions": []},
                        "medium": {"count": "Number of medium level problems", "questions": []},
                        "hard": {"count": "Number of hard level problems", "questions": []}
                    }
                }
            }
        }
    }
    return jsonify(api_docs)


api.add_resource(GeeksForGeeksAPI, "/<string:username>")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)