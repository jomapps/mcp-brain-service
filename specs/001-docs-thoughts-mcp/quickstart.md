# Quickstart Guide

**Feature**: MCP Brain Service

This guide provides a quick way to test the core functionality of the MCP Brain Service.

## Prerequisites

- A WebSocket client (e.g., `websocat`, `wscat`, or a simple Python script).
- The MCP Brain Service must be running.

## 1. Establish a WebSocket Connection

Connect your WebSocket client to the appropriate endpoint (e.g., `ws://localhost:8002` for local testing).

## 2. Create a Character

Send a JSON message with the following structure:

```json
{
  "tool": "create_character",
  "project_id": "your_project_id",
  "name": "Gandalf",
  "personality_description": "A wise and powerful wizard, mentor to Frodo Baggins.",
  "appearance_description": "An old man with a long white beard, a pointy hat, and a staff."
}
```

**Expected Response**:

A JSON message confirming the character was created, including the character's new ID.

```json
{
  "status": "success",
  "message": "Character created successfully.",
  "character_id": "some_unique_id"
}
```

## 3. Find Similar Characters

Send a JSON message with the following structure:

```json
{
  "tool": "find_similar_characters",
  "project_id": "your_project_id",
  "query": "A powerful magic user"
}
```

**Expected Response**:

A JSON message containing a list of characters that are semantically similar to the query.

```json
{
  "status": "success",
  "results": [
    {
      "id": "some_unique_id",
      "name": "Gandalf",
      "similarity_score": 0.95
    }
    // ... other similar characters
  ]
}
```
