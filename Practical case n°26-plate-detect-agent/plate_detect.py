import streamlit as st
import json
import os
import warnings
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from inference import InferencePipeline
from twilio.rest import Client
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

# ================== GLOBAL SETUP ==================
roboflow_key = os.getenv('ROBOFLOW_API_KEY')
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

MAX_FRAMES = 60
DONE_PLATES = []

# ================== LOAD DATA ==================
with open('vehicle_violations.json', 'r') as f:
    data = json.load(f)

# ================== TOOL ==================
def send_alert(message: str):
    msg = client.messages.create(
        from_=os.getenv('TWILIO_FROM_NUMBER'),
        to=os.getenv('TWILIO_TO_NUMBER'),
        body=message
    )
    return msg.sid

# ================== AGENTS ==================

router_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="""
    You receive a JSON vehicle violation object.
    Decide routing:
    - If severity is 'high' → return 'critical'
    - Otherwise → return 'normal'
    Return ONLY one word: normal or critical.
    """
)

normal_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[send_alert],
    instructions=dedent("""
    Generate a NORMAL alert.
    Format:
    ⚠️ Vehicle [license_plate] detected at [location].
    Violation: [crime] on [date].
    Fine: £[fine_amount].

    Send using send_alert().
    Return JSON status.
    """)
)

critical_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[send_alert],
    instructions=dedent("""
    Generate a CRITICAL alert.
    Use RED emojis 🚨🔴🔥.

    Format:
    🚨🚨 CRITICAL ALERT 🚨🚨
    Vehicle [license_plate] detected at [location]
    SEVERE VIOLATION: [crime]
    Date: [date]
    Fine: £[fine_amount]
    Immediate attention required.

    Send using send_alert().
    Return JSON status.
    """)
)

# ================== LOOKUP ==================
def plate_detection(plate):
    for d in data:
        if d["license_plate"] == plate and plate not in DONE_PLATES:
            return d
    return None

# ================== CALLBACK ==================
def my_sink(result, video_frame):
    if video_frame.frame_id == MAX_FRAMES:
        pipeline.terminate()
        return

    frame_plates = set()
    for group in result["open_ai"]:
        for res in group:
            if res.get("output"):
                frame_plates.add(res["output"].strip())

    for plate in frame_plates:
        plate_info = plate_detection(plate)
        if plate_info:
            DONE_PLATES.append(plate)
            st.success(f"✅ Plate matched: {plate}")

            route = router_agent.run(json.dumps(plate_info)).content.strip()

            if route == "critical":
                response = critical_agent.run(json.dumps(plate_info))
            else:
                response = normal_agent.run(json.dumps(plate_info))

            for msg in reversed(response.messages):
                if msg.role == "assistant":
                    st.json(json.loads(msg.content))
                    break

# ================== UI ==================
st.title("🚓 Agentic License Plate Detection")

if st.button("▶ Start Detection"):
    pipeline = InferencePipeline.init_with_workflow(
        api_key=roboflow_key,
        workspace_name="tp-qpwtk",
        workflow_id="custom-workflow",
        video_reference="video/traffic-3.mp4",
        on_prediction=my_sink
    )
    pipeline.start()
    pipeline.join()
    st.success("✅ Processing finished")
