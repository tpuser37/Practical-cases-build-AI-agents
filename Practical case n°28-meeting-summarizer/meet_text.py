import assemblyai as aai
from dotenv import load_dotenv
import os
from agno.agent import Agent
from agno.workflow import Workflow, Step, StepOutput
from agno.models.google import Gemini
import os
from agno.tools.file import FileTools
from agno.tools.gmail import GmailTools

#loading the env
load_dotenv()
id=os.getenv("id")
api_key=os.getenv("api_key_gemini_v2")

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")


def step_transcription(step_input) -> StepOutput:
    audio_path = step_input.input.get("audio_path")

    config = aai.TranscriptionConfig(speaker_labels=True)
    transcript = aai.Transcriber().transcribe(audio_path, config)

    with open("Conv_to_text.txt", "w", encoding="utf-8") as f:
        for utt in transcript.utterances:
            f.write(f"Speaker {utt.speaker}: {utt.text}\n")

    return StepOutput(
        content="Transcription completed and Conv_to_text.txt generated"
    )

summarizer_agent = Agent(
    name="Meeting Summarizer Agent",
    model=Gemini(id=id, api_key=api_key),
    tools=[FileTools()],
    markdown=True,
    instructions="""
You are a professional meeting summarization agent.

MANDATORY TASKS:
1. Read the full transcript from the file Conv_to_text.txt using FileTools
2. Generate a clear, structured, professional meeting summary
3. CREATE A DOCUMENT FILE named EXACTLY: Meeting_Summary.docx
4. WRITE the summary INSIDE the document
5. DO NOT return the summary as plain text

STRUCTURE INSIDE THE DOCUMENT:

Title: Meeting Summary

### Summary
(3–6 sentences)

### Key Topics Discussed
- Bullet points

### Notable Examples
- Bullet points if any

### Decisions or Action Items
- Bullet points if any

IMPORTANT RULES:
- Your final output MUST be a file creation using FileTools
- The result of your work is the file, not text output
- If you do not create the .docx file, the task is considered FAILED
""",
)


def step_generate_summary_doc(step_input) -> StepOutput:
    response = summarizer_agent.run(
        "Read Conv_to_text.txt, summarize the meeting and create Meeting_Summary.docx"
    )
    return StepOutput(content=response.content)


# Agent to send the docx file through gmail
Gmail_sender = Agent(
    name="Gmail mail sender",
    model=Gemini(id=id,api_key=api_key),
    tools=[GmailTools(credentials_path=r"D:\Agno\Meeting_text\client_secret_14840150298-jkg1i33kl9vgf0j1d6ro1aqu0va9e3qg.apps.googleusercontent.com.json"), FileTools()],
    instructions="""
    Your role is to send the 'Meeting_Summary.docx' document to the list of recipients provided in the user's message.
    
    1. Craft a clear, professional email message based on the meeting summary content.
    2. Use the file 'Meeting_Summary.docx' as an attachment.
    3. Accept a list of one or more email addresses to send the message to.
    4. Include a meaningful subject (e.g., "Meeting Summary – [Insert Date or Topic]").
    5. Use GmailTools to send the email with the attachment.
    6. Confirm that the email was successfully sent or report any errors.
    
    If the user provides additional context (e.g., meeting title, purpose, or message body preferences), incorporate that into the email.
       """,
       show_tool_calls=True,
)

def step_send_email(step_input) -> StepOutput:
    user_email = step_input.input.get("email")

    response = Gmail_sender.run(
        f"Send Meeting_Summary.docx to {user_email}"
    )
    return StepOutput(content=response.content)

workflow = Workflow(
    name="AudioToSummaryEmailWorkflow",
    steps=[
        Step(name="Transcription", executor=step_transcription),
        Step(name="SummarizeAndCreateDoc", executor=step_generate_summary_doc),
        Step(name="SendEmail", executor=step_send_email),
    ]
)

if __name__ == "__main__":
    result = workflow.run(
        {
            "audio_path": r"D:\Agno\Meeting_text\video\videoplayback.m4a",
            "email": "hajarmachmoum546@gmail.com"
        }
    )

    print("✅ Workflow finished")
    print(result.content)
