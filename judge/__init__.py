"""
LLM judge for conformity scoring on PR comments (FUN, NSI, INSI, ISI per CONFORMITY_SYSTEM_PROMPT).
Reads from cleaned table, runs Ollama or OpenAI, writes full schema to scores table.
"""
