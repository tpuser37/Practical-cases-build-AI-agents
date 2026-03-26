import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

# ============================
# Configure Logging & Neo4j
# ============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ----------------------------
# Neo4j Connection Settings
# ----------------------------
NEO4J_URI      = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", None)

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise ValueError("❗️ You must set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD")

# ----------------------------
# Helpers
# ----------------------------
def iso_timestamp_days_ago(days: int) -> str:
    """Return ISO formatted timestamp N days ago."""
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

def generate_uuid() -> str:
    """Generate a unique UUID string."""
    return str(uuid.uuid4())

# ----------------------------
# Sample Episodes
# ----------------------------
def create_sample_episodes():
    """Return a list of sample fitness episodes."""
    episodes = []

    sample_data = [
        {"user": "john_doe", "activity_type": "running", "distance_km": 6,  "duration_min": 35, "days_ago": 7},
        {"user": "john_doe", "activity_type": "cycling", "distance_km": 20, "duration_min": 60, "days_ago": 3},
        {"user": "john_doe", "activity_type": "running", "distance_km": 4,  "duration_min": 25, "days_ago": 2},
    ]

    for idx, data in enumerate(sample_data, start=1):
        activity_id = f"activity_{idx}_{generate_uuid()}"
        content = {
            "user": data["user"],
            "activity_id": activity_id,
            "activity_type": data["activity_type"],
            "distance_km": data["distance_km"],
            "duration_min": data["duration_min"],
            "timestamp": iso_timestamp_days_ago(data["days_ago"]),
        }
        episodes.append({
            "name": f"Fitness Event {idx}",
            "body": json.dumps(content),
            "type": EpisodeType.json,
            "description": f"{data['days_ago']} days ago: {data['user']} {data['activity_type']} {data['distance_km']} km",
        })

    return episodes

# ----------------------------
# Query Function
# ----------------------------
async def query_activities(graphiti: Graphiti, query_text: str):
    """Run a query with Graphiti and handle exceptions."""
    try:
        logger.info(f"🔍 Running query: \"{query_text}\"")
        results = await graphiti.search(query=query_text)
        return results
    except Exception as e:
        logger.error(f"❌ Query failed: {e}")
        return []

# ----------------------------
# Main Async Routine
# ----------------------------
async def main():
    # Initialize Graphiti client
    graphiti = Graphiti(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # Build indices & constraints (run once for a fresh DB)
        await graphiti.build_indices_and_constraints()
        logger.info("✔ Indices and constraints built.")

        # Add sample episodes
        episodes = create_sample_episodes()
        for ep in episodes:
            await graphiti.add_episode(
                name=ep["name"],
                episode_body=ep["body"],
                source=ep["type"],
                source_description=ep["description"],
                reference_time=datetime.now(timezone.utc),
            )
            logger.info(f"✔ Added episode: {ep['name']}")

        # Define queries
        queries = [
            ("Activities in last 5 days", f"john_doe activity since {iso_timestamp_days_ago(5)}"),
            ("Running > 5 km in last 7 days", f"john_doe running distance > 5 since {iso_timestamp_days_ago(7)}"),
            ("Activities in last 30 days", f"john_doe activity since {iso_timestamp_days_ago(30)}"),
        ]

        # Execute queries
        for label, q_text in queries:
            results = await query_activities(graphiti, q_text)
            print(f"\n--- {label} ---")
            for r in results:
                print(f"• UUID: {r.uuid} | Fact: {r.fact} | Time: {r.valid_at or r.ingested_at}")

    finally:
        await graphiti.close()
        logger.info("✔ Graphiti connection closed.")

# ----------------------------
# Entry Point
# ----------------------------
if __name__ == "__main__":
    asyncio.run(main())
