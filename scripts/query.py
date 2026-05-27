"""CLI: Interactive query tool for testing the RAG pipeline.

Usage:
    python scripts/query.py
"""
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from retrieval.search import vector_search
from retrieval.generator import generate_answer
from conversation_logging.logger import log_query

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def main():
    print("RAG Knowledge Base — Interactive Query")
    print("Type 'quit' to exit\n")

    while True:
        try:
            query = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if query.lower() in ("quit", "exit", "q"):
            break

        if not query:
            continue

        chunks = vector_search(query)

        if not chunks:
            print("\nNo relevant documents found.\n")
            continue

        result = generate_answer(query, chunks)

        print(f"\n{result['answer']}")
        print(f"\n  Sources: {', '.join(result['sources'])}")
        print(f"  Latency: {result['latency_ms']}ms | Tokens: {result['input_tokens']} in / {result['output_tokens']} out")
        print()

        log_query(
            query=query,
            retrieved_chunks=chunks,
            answer=result["answer"],
            sources=result["sources"],
            latency_ms=result["latency_ms"],
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
        )


if __name__ == "__main__":
    main()
