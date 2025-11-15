from fastapi import FastAPI, HTTPException
from app.schema import PostCreate


app = FastAPI()


text_post = {
    1: {"title": "Daily Update", "content": "System check completed successfully."},
    2: {"title": "Reminder", "content": "Don't forget to review your tasks for today."},
    3: {"title": "Announcement", "content": "New feature rollout scheduled this week."},
    4: {"title": "Alert", "content": "Unusual login detected. Please verify."},
    5: {"title": "Info Post", "content": "API version 2.0 will be available soon."},
    6: {"title": "Quick Tip", "content": "Use caching to improve API response time."},
    7: {"title": "Motivation", "content": "Keep pushing your limits every day."},
    8: {"title": "Dev Update", "content": "Microservice deployment successful."},
    9: {"title": "Bug Fix", "content": "Resolved data mismatch issue in reports."},
    10: {"title": "Fun Fact", "content": "Python was named after Monty Python."},
    11: {
        "title": "Quote",
        "content": "Code is like humor. When you have to explain it, it's bad.",
    },
    12: {
        "title": "Release Note",
        "content": "Version 1.3 includes performance improvements.",
    },
    13: {"title": "Server Status", "content": "All services are running smoothly."},
    14: {"title": "Update", "content": "Logging system migrated to new pipeline."},
    15: {"title": "Patch Note", "content": "Security vulnerabilities addressed."},
    16: {"title": "Upgrade", "content": "Database server upgraded to latest version."},
    17: {"title": "New Post", "content": "Testing async endpoints in FastAPI."},
    18: {"title": "Feature Highlight", "content": "Background tasks now available."},
    19: {"title": "Team Update", "content": "New developer joined the backend team."},
    20: {"title": "Maintenance", "content": "Scheduled downtime this Sunday."},
}


@app.get("/posts")
def get_all_posts():
    return text_post


@app.get("/posts/{id}")
def get_individual_post(id: int):
    if id not in text_post:
        raise HTTPException(status_code=404, detail="Page Not Found")
    return text_post.get(id)


# Getting post as per query parameters -> the one with ?


@app.get("/all_posts")
def get_all_posts_limit(
    limit: int = None,
):  # Now this is an optional part if one doesnot want to keep it optional he can remove None and make it something like <def get_all_posts_limit(limit:int):> so one will need to pass it
    if limit:
        return list(text_post.values())[:limit]
    return text_post


@app.post("/create_post")
def create_post(post:PostCreate):
    new_post = {"title":post.title,"content":post.content}
    text_post[max(text_post.keys())+1] = new_post
    return new_post

@app.delete("/delete/{id}")
def delete_post(id:int):
    text_post.pop(id)
    return {"Post Deleted":{id}}