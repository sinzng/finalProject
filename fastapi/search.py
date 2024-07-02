from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import requests
import os

API_KEY = os.getenv("CUSTOM_SEARCH_API")
CX = os.getenv("GOOGLE_CX")



async def search_query(query: str) -> HTMLResponse:
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": query
    }

    response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
    data = response.json()
    results = []
    
    if 'items' in data:
        for item in data['items']:
            link = item.get('link', '')
            title = item.get('title', 'No title')
            results.append({
                "title": title,
                "link": link,
            })

    result_html = "<h2>Results for \"{}\":</h2><ul>".format(query)
    for result in results:
        result_html += "<li><a href='{}' target='_blank'>{}</a></li>".format(result['link'], result['title'])
    result_html += "</ul>"

    html_content = """
    <html>
    <body>
        <h1>Google Custom Search</h1>
        <form action="/search" method="post">
            <input type="text" name="query" placeholder="Enter search term">
            <input type="submit" value="Search">
        </form>
        {}
    </body>
    </html>
    """.format(result_html)

    return HTMLResponse(content=html_content)