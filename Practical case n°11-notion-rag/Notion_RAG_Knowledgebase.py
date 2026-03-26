import os
from notion_client import Client
from agno.agent import Agent
from agno.models.mistral import MistralChat
from agno.knowledge import Knowledge
from typing import List, Optional

notion = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = "2dcd7221b8d58053bd5ded5cc61485a4"
api_key=os.getenv("MISTRAL_API_KEY")

def search_notion_kb(query: str, max_results: int = 3) -> List[str]:
    try:
        results = notion.databases.query(database_id=DATABASE_ID)
        matching_docs = []
        query_lower = query.lower()
        query_words = query_lower.split()
        
        for page in results['results']:
            props = page['properties']
            
            question = props['question']['rich_text'][0]['plain_text'] if props['question']['rich_text'] else ""
            answer = props['answer']['rich_text'][0]['plain_text'] if props['answer']['rich_text'] else ""
            department = props['department']['rich_text'][0]['plain_text'] if props['department']['rich_text'] else ""
            tags = [t['name'] for t in props['tags']['multi_select']]
            
            searchable = f"{question} {answer} {department} {' '.join(tags)}".lower()
            matches = sum(1 for word in query_words if word in searchable)
            
            if matches > 0:
                score = matches / len(query_words)
                content = f"""Question: {question}
Answer: {answer}
Department: {department}
Tags: {', '.join(tags) if tags else 'None'}"""
                matching_docs.append({'content': content, 'score': score})
        
        matching_docs.sort(key=lambda x: x['score'], reverse=True)
        return [doc['content'] for doc in matching_docs[:max_results]]
        
    except Exception as e:
        return []


class NotionKnowledge(Knowledge):
    
    def __init__(self, database_id: str):
        super().__init__()
        self.database_id = database_id
    
    def search(self, query: str, num_documents: Optional[int] = None) -> List[str]:
        return search_notion_kb(query, num_documents or 3)


notion_kb = NotionKnowledge(DATABASE_ID)

agent = Agent(
    model=MistralChat(id="ministral-14b-2512", api_key=api_key),
    knowledge=notion_kb,
    search_knowledge=True,
    instructions=[
        "You are a helpful assistant with access to a company knowledge base in Notion.",
        "When you find information in the knowledge base, ALWAYS use it to answer questions.",
        "The knowledge base contains accurate information - cite it in your responses.",
        "If you search and find relevant data, incorporate it into your answer."
    ],
    markdown=True,
)

prompt = input("Your question: ")
agent.print_response(prompt)