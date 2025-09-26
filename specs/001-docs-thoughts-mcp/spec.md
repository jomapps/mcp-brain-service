# Feature Specification: MCP Brain Service

**Feature Branch**: `001-docs-thoughts-mcp`  
**Created**: 2025-09-26
**Status**: Draft  
**Input**: User description: "@docs/thoughts/mcp-brain-service.md has my plan for this app. pls also read @docs/thoughts/Domain-configs.md for reference"

## Clarifications
### Session 2025-09-26
- Q: What is the data retention policy for character data when a project is deleted? → A: Delete all associated character data immediately and permanently.
- Q: How should the MCP Brain Service handle a temporary outage of the Jina v4 embedding service? → A: Reject incoming requests with an error indicating the service is unavailable.
- Q: What is the expected average response time for a semantic search query under normal load (p95)? → A: 1min
- Q: Should character embeddings be updated if the character's description changes? → A: Yes, automatically and synchronously update embeddings on every change.
- Q: What should be the system's behavior on its first-ever run? → A: A and C

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies  
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a developer of the Auto-Movie app, I want to connect to the MCP Brain Service to create characters with personality and appearance embeddings, and find similar characters using semantic search, so that the main application can leverage a knowledge graph for rich character interactions.

### Acceptance Scenarios
1. **Given** the MCP Brain Service is running, **When** the Auto-Movie app connects via WebSocket, **Then** a successful connection is established.
2. **Given** a connection is established, **When** the Auto-Movie app sends a request to create a character with specific traits, **Then** the character is created in the Neo4j database with corresponding Jina v4 embeddings.
3. **Given** characters exist in the knowledge graph, **When** the Auto-Movie app sends a semantic search query, **Then** the service returns a list of similar characters.

### Edge Cases
- During a Jina v4 service outage, the system MUST reject incoming requests with an error indicating the service is unavailable.
- How does the system handle invalid or incomplete character data?
- What is the behavior when a search query returns no results?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: The system MUST provide a WebSocket server implementing the MCP protocol.
- **FR-002**: The system MUST integrate with Jina v4 for generating embeddings.
- **FR-003**: The system MUST use a Neo4j database to store the knowledge graph.
- **FR-004**: The system MUST expose a tool to create new characters with personality and appearance attributes.
- **FR-005**: The system MUST expose a tool for semantic search to find similar characters.
- **FR-006**: The system MUST support project-scoped data isolation.
- **FR-007**: The system MUST be configurable for different environments (local, dev, prod) based on `Domain-configs.md`.
- **FR-008**: The system MUST permanently delete all character data associated with a project upon project deletion.
- **FR-009**: The system MUST automatically and synchronously update character embeddings whenever a character's description is modified.
- **FR-010**: On its first run, the system MUST initialize with an empty knowledge graph and perform a self-check to ensure connectivity to dependent services (Jina, Neo4j), reporting status.

### Non-Functional Requirements
- **NFR-001**: The p95 response time for a semantic search query MUST be under 1 minute.

### Key Entities *(include if feature involves data)*
- **Character**: Represents a character in the story. Attributes include name, personality description, appearance description, and their corresponding embeddings.
- **Project**: Represents a container for data, ensuring isolation between different projects.

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous  
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] User scenarios defined
- [ ] Requirements generated
- [ ] Entities identified
- [ ] Review checklist passed

---