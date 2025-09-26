# Tasks: MCP Brain Service

**Input**: Design documents from `/specs/001-docs-thoughts-mcp/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/

## Phase 3.1: Setup
- [X] T001 Create the project structure in the `mcp-brain-service` directory as per the `plan.md`.
- [X] T002 Initialize a Python project with `Poetry` and add `fastapi`, `uvicorn`, `jina`, `neo4j`, and `pytest` as dependencies.
- [X] T003 [P] Configure `ruff` for linting and formatting.

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [X] T004 [P] Create a contract test for the `create_character` WebSocket endpoint in `tests/contract/test_websocket.py`.
- [X] T005 [P] Create a contract test for the `find_similar_characters` WebSocket endpoint in `tests/contract/test_websocket.py`.
- [X] T006 [P] Create an integration test for the character creation user story in `tests/integration/test_character_creation.py`.
- [X] T007 [P] Create an integration test for the semantic search user story in `tests/integration/test_semantic_search.py`.

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [X] T008 [P] Implement the `Character` and `Project` data models in `src/models/` based on `data-model.md`.
- [X] T009 [P] Implement the `CharacterService` in `src/services/character_service.py` with methods for creating and finding characters.
- [X] T010 Implement the WebSocket endpoint in `src/main.py` to handle incoming messages.
- [X] T011 Implement the `create_character` tool in the WebSocket endpoint.
- [X] T012 Implement the `find_similar_characters` tool in the WebSocket endpoint.
- [X] T013 Implement input validation for the WebSocket messages.
- [X] T014 Implement error handling and logging for the WebSocket endpoint.

## Phase 3.4: Integration
- [X] T015 Connect the `CharacterService` to the Neo4j database.
- [X] T016 Integrate the Jina v4 client into the `CharacterService` to generate embeddings.

## Phase 3.5: Polish
- [X] T017 [P] Add unit tests for the input validation in `tests/unit/test_validation.py`.
- [X] T018 Create a performance test script to verify the p95 response time of the semantic search.
- [X] T019 [P] Update the `README.md` with instructions on how to run the service and the tests.

## Dependencies
- Tests (T004-T007) before implementation (T008-T014)
- T008 blocks T009, T015
- T016 is blocked by T009
- Implementation before polish (T017-T019)

## Parallel Example
```
# Launch T004-T007 together:
Task: "Create a contract test for the `create_character` WebSocket endpoint in `tests/contract/test_websocket.py`"
Task: "Create a contract test for the `find_similar_characters` WebSocket endpoint in `tests/contract/test_websocket.py`"
Task: "Create an integration test for the character creation user story in `tests/integration/test_character_creation.py`"
Task: "Create an integration test for the semantic search user story in `tests/integration/test_semantic_search.py`"
```
