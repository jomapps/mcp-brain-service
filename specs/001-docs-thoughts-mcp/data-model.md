# Data Model

**Feature**: MCP Brain Service

This document outlines the data models for the key entities in the MCP Brain Service.

## Character

Represents a character in the story.

**Attributes**:

| Name | Type | Description | Constraints |
|---|---|---|---|
| `id` | string | Unique identifier for the character (e.g., UUID) | Required, Primary Key |
| `project_id` | string | Identifier for the project this character belongs to | Required, Foreign Key |
| `name` | string | The name of the character | Required |
| `personality_description` | string | A textual description of the character's personality | Required |
| `appearance_description` | string | A textual description of the character's appearance | Required |
| `embedding_personality` | vector | Embedding vector for the personality description | Required |
| `embedding_appearance` | vector | Embedding vector for the appearance description | Required |
| `created_at` | datetime | Timestamp of when the character was created | Required |
| `updated_at` | datetime | Timestamp of when the character was last updated | Required |

## Project

Represents a container for data, ensuring isolation between different projects.

**Attributes**:

| Name | Type | Description | Constraints |
|---|---|---|---|
| `id` | string | Unique identifier for the project (e.g., UUID) | Required, Primary Key |
| `name` | string | The name of the project | Required |
| `created_at` | datetime | Timestamp of when the project was created | Required |
