from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
from bs4 import BeautifulSoup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CommandRequest(BaseModel):
    command: str

async def fetch_philgeps_advisories():
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = await client.get("https://notices.philgeps.gov.ph", headers=headers, timeout=15.0)
            if response.status_code != 200:
                return f"Failed to retrieve advisories. HTTP Status: {response.status_code}"
            
            # Use response.text which handles encoding better, or explicitly set it
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            
            announcements = soup.find_all('h6')
            
            if not announcements:
                announcements = soup.find_all('a', href=True)
                results = []
                for a in announcements:
                    if '/about-ps/news/' in a['href']:
                        results.append(a.get_text().strip())
            else:
                results = [item.get_text().strip() for item in announcements]
            
            filtered_results = [r for r in results if len(r) > 15 and "Login" not in r]
            
            if not filtered_results:
                return "No specific advisories found."
            
            # Ensure the result is encoded as UTF-8 explicitly when joining
            formatted_results = "\n".join([f"- {r}" for r in filtered_results[:5]])
            return formatted_results
    except Exception as e:
        return f"Error scraping PhilGEPS: {str(e)}"

@app.post("/api/agent")
async def handle_command(request: CommandRequest):
    cmd = request.command.lower()
    print(f"Received Command: {cmd}")

    if "status" in cmd:
        response = "All systems nominal. Agent is idling in standby mode."
    elif "help" in cmd:
        response = "Available commands: 'status', 'scan', 'deploy', 'philgeps'. Try 'philgeps' to fetch advisories."
    elif "philgeps" in cmd or "advisory" in cmd:
        data = await fetch_philgeps_advisories()
        response = "Accessing PhilGEPS portal... fetching latest advisories...\n\n" + data
    elif "scan" in cmd:
        response = "Scanning local environment... 0 vulnerabilities found. System optimized."
    elif "deploy" in cmd:
        response = "Initiating deployment sequence... Sub-agents spawned. Monitoring progress."
    else:
        response = f"Command '{cmd}' received. Processing via AI core... (Prototype response: Task acknowledged)."

    return {"response": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
