from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from generate_service import generate_official_rules

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, HTTPException, status
import secrets

security = HTTPBasic()

def verify(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = "internal"
    correct_password = "TryMarkSecure123"

    if not (
        secrets.compare_digest(credentials.username, correct_username)
        and secrets.compare_digest(credentials.password, correct_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# MODELS
# -----------------------------

class Prize(BaseModel):
    type: str
    amount: float | None = None
    description: str | None = None


class EntryMethod(BaseModel):
    channel: str
    url: str | None = None
    required_fields: list[str] = []


class SweepstakesRequest(BaseModel):
    name: str
    door_count: int
    door_location: str
    primary_prize_type: str
    states: list[str]
    min_age: int
    start_time: str
    end_time: str
    winner_selection_time: str
    winner_response_deadline: str
    prizes: list[Prize]

    # 🔥 NEW
    entry_method: EntryMethod


# -----------------------------
# GENERATE ENDPOINT
# -----------------------------

@app.post("/generate")
def generate_rules(
    request: SweepstakesRequest,
    credentials: HTTPBasicCredentials = Depends(verify)
):
    buffer = generate_official_rules(request.dict())

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=official_rules.docx"}
    )


# -----------------------------
# FRONTEND UI
# -----------------------------

@app.get("/", response_class=HTMLResponse)
def homepage(credentials: HTTPBasicCredentials = Depends(verify)):
    return """
<!DOCTYPE html>
<html>
<head>
<title>TryMark.AI</title>
<style>
body { font-family: sans-serif; background: #f4f4f4; display:flex; justify-content:center; padding:40px; }
.card { background:white; width:700px; padding:30px; border-radius:10px; box-shadow:0 8px 20px rgba(0,0,0,0.1);}
h2 { margin-top:0;}
input, select { width:100%; padding:8px; margin:8px 0;}
button { padding:10px 15px; background:black; color:white; border:none; margin-top:10px; cursor:pointer;}
.prize-block { border:1px solid #ddd; padding:10px; margin-top:10px; border-radius:6px;}
.section { margin-top:20px; padding-top:10px; border-top:1px solid #eee;}
</style>
</head>
<body>

<div class="card">
<h2>TryMark.AI – Official Rules Generator</h2>

<input id="name" placeholder="Sweepstakes Name">
<input id="door_count" type="number" placeholder="Door Count">
<input id="door_location" placeholder="Door Location">

<select id="primary_prize_type">
  <option value="cash">Cash</option>
  <option value="giftcard">Gift Card</option>
</select>

<input id="min_age" type="number" placeholder="Minimum Age (18 or 21)">
<input id="states" placeholder="Eligible States (comma separated)">
<input id="start_time" placeholder="Start Time">
<input id="end_time" placeholder="End Time">
<input id="winner_selection_time" placeholder="Winner Selection Time">
<input id="winner_response_deadline" placeholder="Winner Response Deadline">

<div class="section">
<h3>Entry Method</h3>

<select id="entry_channel" onchange="toggleEntryFields()">
  <option value="web">Web</option>
  <option value="mail">Mail</option>
  <option value="in_store">In-Store</option>
  <option value="social">Social Media</option>
</select>

<div id="webFields">
  <input id="entry_url" placeholder="Website URL">
  <input id="entry_fields" placeholder="Required fields (comma separated e.g. name,email,phone)">
</div>
</div>

<h3>Prize Levels</h3>
<div id="prizeContainer"></div>
<button onclick="addPrize()">+ Add Prize Level</button>

<button onclick="generate()">Generate Document</button>

<div id="status"></div>

</div>

<script>

let prizeCount = 0;

function toggleEntryFields() {
  const channel = document.getElementById("entry_channel").value;
  const webFields = document.getElementById("webFields");

  if(channel === "web"){
    webFields.style.display = "block";
  } else {
    webFields.style.display = "none";
  }
}

toggleEntryFields();

function addPrize() {
  prizeCount++;
  const container = document.getElementById("prizeContainer");

  const block = document.createElement("div");
  block.className = "prize-block";
  block.innerHTML = `
    <label>Level ${prizeCount}</label>
    <select class="prize-type">
      <option value="cash">Cash</option>
      <option value="giftcard">Gift Card</option>
    </select>
    <input placeholder="Amount (cash) or Description (gift card)" class="prize-value">
  `;
  container.appendChild(block);
}

async function generate() {

  const prizes = [];
  document.querySelectorAll(".prize-block").forEach(block => {
    const type = block.querySelector(".prize-type").value;
    const value = block.querySelector(".prize-value").value;

    if(type === "cash") {
      prizes.push({
        type: "cash",
        amount: parseFloat(value)
      });
    } else {
      prizes.push({
        type: "giftcard",
        description: value
      });
    }
  });

  const entryChannel = document.getElementById("entry_channel").value;

  const payload = {
    name: document.getElementById("name").value,
    door_count: parseInt(document.getElementById("door_count").value),
    door_location: document.getElementById("door_location").value,
    primary_prize_type: document.getElementById("primary_prize_type").value,
    states: document.getElementById("states").value.split(",").map(s=>s.trim()),
    min_age: parseInt(document.getElementById("min_age").value),
    start_time: document.getElementById("start_time").value,
    end_time: document.getElementById("end_time").value,
    winner_selection_time: document.getElementById("winner_selection_time").value,
    winner_response_deadline: document.getElementById("winner_response_deadline").value,
    prizes: prizes,

    entry_method: {
      channel: entryChannel,
      url: entryChannel === "web" ? document.getElementById("entry_url").value : null,
      required_fields: entryChannel === "web"
        ? document.getElementById("entry_fields").value.split(",").map(f=>f.trim())
        : []
    }
  };

  document.getElementById("status").innerText = "Generating...";

  const response = await fetch("/generate", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload)
  });

  if(!response.ok){
    document.getElementById("status").innerText = "Error generating document.";
    return;
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "official_rules.docx";
  a.click();

  document.getElementById("status").innerText = "Done.";
}

</script>

</body>
</html>
"""