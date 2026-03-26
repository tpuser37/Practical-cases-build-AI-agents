import os
import streamlit as st
from agno.agent import Agent
from agno.models.mistral import MistralChat
from firecrawl import FirecrawlApp

# --- CONFIGURATION DES API ---
firecrawl = FirecrawlApp(api_key="fc-37aef7ac75e14c5c8e12866c7b404c92")
api_key=os.getenv("MISTRAL_API_KEY")

agent = Agent(
    model=MistralChat(api_key=api_key, id="mistral-medium-2508"),
    instructions="Réponds de manière concise et claire, en te basant uniquement sur le contenu fourni."
)

# --- STREAMLIT APP ---
st.title("Extraction Web (Firecrawl) + Q&A (AGNO)")

url_input = st.text_input("👉 Entrez l'URL du document (HTML ou PDF) :")

if url_input:
    with st.spinner("🔎 Extraction du contenu..."):
        try:
            
            doc = firecrawl.scrape(
                url_input,
                formats=["markdown", "summary"]
            )

            # Récupérer Markdown ou résumé
            text_md = getattr(doc, "markdown", None)
            text_sum = getattr(doc, "summary", None)

            # Combine Markdown + résumé si disponible
            content = ""
            if text_md:
                content += text_md + "\n\n"
            if text_sum:
                content += "\n\nRésumé :\n" + text_sum

            if not content.strip():
                st.error("❌ Impossible d'extraire le contenu de cette URL.")
            else:
                st.success("✔️ Contenu extrait avec succès !")
                st.text_area("📄 Contenu extrait :", content, height=300)

                # ➤ Question utilisateur
                user_question = st.text_input("❓ Posez votre question :")
                if user_question:
                    with st.spinner("🤖 L'agent réfléchit..."):
                        prompt = f"Voici le texte extrait :\n\n{content}\n\nQuestion : {user_question}"
                        answer = agent.run(prompt)

                        st.subheader("🧠 Réponse :")
                        if hasattr(answer, "content"):
                            st.write(answer.content)
                        else:
                            st.write(answer)

        except Exception as e:
            st.error(f"Erreur : {e}")
