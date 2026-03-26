# n8n Social Media Analytics Workflow - Setup Guide

## 📖 Overview

This guide explains how to use Claude AI to generate custom n8n workflows by providing documentation and requirements. This example demonstrates creating a weekly social media analytics automation workflow.

---

## 🎯 What This Workflow Does

The generated n8n workflow automates the collection and reporting of social media analytics:

- **Triggers** every Monday at 8:00 AM
- **Fetches analytics data** from Twitter and LinkedIn for the previous week
- **Calculates key metrics**: engagement rate, impressions, reach, and platform-specific stats
- **Aggregates data** from all platforms into a unified report
- **Sends an HTML email** with visual metrics and breakdowns to specified recipients
- **Handles errors gracefully** - continues processing even if one platform fails

---

## 🚀 Step-by-Step Process

### Step 1: Create a Project in Claude

1. Go to [claude.ai](https://claude.ai)
2. Start a new conversation
3. Optionally create a Project for organizing related workflows

### Step 2: Add Knowledge Base Documents

Upload your reference documents to provide context to Claude:

1. **Platform Documentation** (e.g., `Activepieces.txt`, `n8n-docs.txt`)
   - Explains the automation platform's concepts and structure
   
2. **Workflow Requirements** (e.g., `workflow-requirements.txt`)
   - Details the specific automation tasks needed
   - Includes data sources, processing logic, scheduling requirements
   - Specifies error handling and formatting needs

**Example documents used:**
- Platform concepts and architecture
- API integration requirements
- Scheduling specifications
- Data processing rules
- Error handling strategies

### Step 3: Provide Your Prompt

Send Claude a clear prompt describing what you need:

```
Please generate the JSON for an n8n workflow that automates the weekly
collection of media analytics from Twitter and LinkedIn. The workflow should:
- Trigger every Monday at 8:00 AM
- Fetch analytics data for the previous week from each platform
- Calculate engagement rate, reach, and impressions
- Aggregate all data into a summary report
- Send the summary via email to a specified list
- Include error handling and modular node design
Provide the full workflow JSON for direct import.
```

### Step 4: Claude Generates the Workflow JSON

Claude will:
- Analyze your requirements and knowledge base
- Create a complete n8n workflow in JSON format
- Include all necessary nodes, connections, and configurations
- Add proper error handling and data processing logic
- Generate ready-to-import code

### Step 5: Review the Generated Workflow

Claude provides:
- **Complete JSON** ready for import
- **Feature explanation** of what the workflow does
- **Setup instructions** for credentials and configuration
- **Customization tips** for adapting to your needs
### Output: 
<img width="1276" height="488" alt="531723079-7489b7b8-2158-45ca-9e3a-0f205190a20f" src="https://github.com/user-attachments/assets/65951b93-5a44-4986-8981-dbdbff0fc1e4" />

