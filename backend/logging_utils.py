"""
Logging and feedback utilities for Pasupathy RAG system.
Logs user queries, answers, and missed cases for continuous improvement.
"""
import datetime
import os

LOG_FILE = os.environ.get("PASUPATHY_LOG_FILE", "pasupathy_rag.log")

def log_query(query, answer, source="agent", score=None):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.datetime.now().isoformat()}] QUERY: {query}\n")
        f.write(f"[{datetime.datetime.now().isoformat()}] ANSWER: {answer}\n")
        f.write(f"[{datetime.datetime.now().isoformat()}] SOURCE: {source}\n")
        if score is not None:
            f.write(f"SCORE: {score}\n")
        f.write("\n")

def log_missed_case(query):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.datetime.now().isoformat()}] MISSED: {query}\n\n")

def get_usage_stats():
    stats = {"total": 0, "missed": 0, "by_source": {}}
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                if line.startswith("[" ) and "QUERY:" in line:
                    stats["total"] += 1
                if "MISSED:" in line:
                    stats["missed"] += 1
                if "SOURCE:" in line:
                    src = line.split("SOURCE:")[-1].strip()
                    stats["by_source"].setdefault(src, 0)
                    stats["by_source"][src] += 1
    except Exception:
        pass
    return stats
