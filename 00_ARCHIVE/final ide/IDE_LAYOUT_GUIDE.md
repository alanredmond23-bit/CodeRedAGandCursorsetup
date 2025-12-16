# 🎯 Final IDE Integration Layout Guide

**Complete folder structure and file layouts for Cursor, Google Antigravity, and Claude Terminal integration with CrewAI & CodeRed**

---

## 📊 High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CODERED ORCHESTRATION CORE                        │
│  (Supabase PostgreSQL + CrewAI + RAG + Agent Registry + Cost Track) │
└─────────────────────────────────────────────────────────────────────┘
                               ▲
                ┌──────────────┼──────────────┐
                │              │              │
         ┌──────▼────┐  ┌──────▼────┐  ┌─────▼──────┐
         │  CURSOR   │  │ ANTIGRAV. │  │   CLAUDE   │
         │    IDE    │  │  (Agent)  │  │  TERMINAL  │
         └───────────┘  └───────────┘  └────────────┘
             (Code                     (Direct LLM
              Editor)                   Interaction)
```

---

## 📁 CURSOR IDE Integration

### **Folder Structure**

```
~/Desktop/final ide/cursor/
├── 🔧 CONFIGURATION
│   ├── cursor_rules.md
│   ├── cursor_settings.json
│   └── agent-context.md
│
├── 🤖 AGENTS (CrewAI Config)
│   ├── agents.yaml
│   ├── tasks.yaml
│   ├── tools.yaml
│   └── handoffs.yaml
│
├── 📡 INTEGRATION
│   ├── codered_client.py
│   ├── supabase_logger.py
│   ├── rag_context_fetcher.py
│   └── cost_tracker.py
│
├── 🔑 CREDENTIALS
│   ├── .env (SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_KEY)
│   └── .env.example
│
├── 📚 TEMPLATES
│   ├── task_template.md
│   ├── prompt_routing.md
│   └── zone_rules.md
│
├── 🧪 TEST
│   ├── test_agent_calls.py
│   └── test_crewai_integration.py
│
└── 📄 README.md
```

### **File Descriptions**

#### **cursor_rules.md** (Core Custom Rules)
```markdown
# Cursor Custom Rules for CrewAI Orchestration

## Agent Context
When editing code, automatically determine:
- Current zone (RED/YELLOW/GREEN)
- Required agents (Architect, Code, Test, Review, Safety)
- Task phase (Design, Implement, Test, Review)

## Handoff Triggers
- When safety_check fails → escalate to SafetyAgent
- When complexity > 2 → always get ArchitectAgent approval
- After implementation → always invoke TestAgent

## Zone Rules
- GREEN: CodeWriter can merge PRs autonomously
- YELLOW: Requires human approval gate
- RED: Requires Cynic + Safety approval before execution

## Keyboard Shortcuts
- Cmd+Shift+A → Ask Architect Agent
- Cmd+Shift+C → Ask Code Agent
- Cmd+Shift+T → Ask Test Agent
- Cmd+Shift+R → Ask Review Agent
- Cmd+Shift+S → Ask Safety Agent
```

#### **codered_client.py** (Supabase Integration)
```python
# Manages all communication with CodeRed database
- create_task(title, description, zone)
- get_agent(role)
- log_agent_run(agent_id, status, output)
- fetch_rag_context(query)
- log_decision(task_id, decision, rationale)
- track_cost(agent_id, model, tokens_used, cost_usd)
```

#### **agents.yaml** (CrewAI Agent Definitions)
```yaml
agents:
  architect:
    role: "System Architecture"
    goal: "Design scalable solutions"
    backstory: "Expert in system design"
    model: "gpt-4o"
    cost_ceiling_usd: 50
    zones: [GREEN, YELLOW, RED]
    
  code_writer:
    role: "Implementation"
    goal: "Write production code"
    backstory: "Expert developer"
    model: "gpt-4o"
    cost_ceiling_usd: 30
    zones: [GREEN, YELLOW]
    
  test_agent:
    role: "QA & Testing"
    goal: "Ensure quality"
    backstory: "QA specialist"
    model: "gpt-4o-mini"
    cost_ceiling_usd: 10
    zones: [GREEN, YELLOW]
    
  # ... etc
```

#### **tasks.yaml** (Task & Handoff Definitions)
```yaml
tasks:
  design_system:
    description: "Design system architecture"
    agent: architect
    expected_output: "Architecture document"
    next_task: implement_system
    
  implement_system:
    description: "Implement designed system"
    agent: code_writer
    expected_output: "Working code"
    depends_on: design_system
    next_task: test_system
    
  test_system:
    description: "Test implementation"
    agent: test_agent
    expected_output: "Test report"
    depends_on: implement_system
    next_task: review_system
    
  # ... etc
```

### **Data Flow in Cursor**

```
┌─────────────────┐
│ User Opens File │
│  in Cursor IDE  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ cursor_rules.md triggers    │
│ - Detect zone (GREEN/YEL/RED)
│ - Identify task phase       │
│ - Suggest agents            │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ User Selects Agent via:     │
│ - Context menu              │
│ - Keyboard shortcut         │
│ - @agent mention            │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ codered_client.py:          │
│ 1. Fetch RAG context        │
│ 2. Check cost ceiling       │
│ 3. Verify zone permissions  │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ CrewAI calls selected agent │
│ with task + context         │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Agent responses with:       │
│ - Code suggestion           │
│ - Architecture decision     │
│ - Test case                 │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ supabase_logger.py logs:    │
│ - agent_runs (output)       │
│ - task progress             │
│ - cost tracking             │
│ - decision audit trail      │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Cursor displays response    │
│ + suggestions for next step │
└─────────────────────────────┘
```

### **Agents Available in Cursor**

| Agent | Availability | Cost Model | Zone Restrictions |
|-------|--------------|------------|-------------------|
| Architect | Always | Gold (gpt-4o) | All zones |
| Code Writer | Always | Gold (gpt-4o) | GREEN, YELLOW |
| Test Agent | Always | Silver (gpt-4o-mini) | GREEN, YELLOW |
| Review Agent | Always | Gold (gpt-4o) | All zones |
| Safety Agent | On demand | Gold (gpt-4o) | RED required |
| Cynic Agent | On demand | Gold (gpt-4o) | RED escalations |
| Research Agent | Optional | Bronze (Claude) | GREEN |
| Librarian Agent | Optional | Silver | All zones |

---

## 📁 GOOGLE ANTIGRAVITY Integration

### **Folder Structure**

```
~/Desktop/final ide/google anti gravity/
├── 🔧 CONFIGURATION
│   ├── antigravity_config.yaml
│   ├── agent_mapping.yaml
│   ├── tool_definitions.yaml
│   └── policy_rules.md
│
├── 🤖 CREW BRIDGE
│   ├── crew_sync.py
│   ├── antigrav_to_crew.py
│   ├── crew_to_antigrav.py
│   └── conflict_resolver.py
│
├── 📡 INTEGRATION
│   ├── codered_connector.py
│   ├── supabase_bridge.py
│   ├── rag_fetcher.py
│   └── metrics_exporter.py
│
├── 🔑 CREDENTIALS
│   ├── .env (GOOGLE_API_KEY, CODERED_KEY)
│   └── .env.example
│
├── 🧩 PLUGINS
│   ├── search_plugin.py
│   ├── code_plugin.py
│   ├── docs_plugin.py
│   └── slack_plugin.py
│
├── 📊 MONITORING
│   ├── health_check.py
│   ├── sync_metrics.py
│   └── conflict_log.py
│
└── 📄 README.md
```

### **File Descriptions**

#### **antigravity_config.yaml** (Agent Configuration)
```yaml
agents:
  orchestrator:
    name: "Main Agent"
    tools: [search, code_execution, docs_search]
    model: "gemini-pro"
    
  researcher:
    name: "Research Agent"
    tools: [web_search, document_retrieval]
    model: "gemini-pro"
    
  executor:
    name: "Code Executor"
    tools: [code_run, file_write, terminal]
    model: "gemini-pro"

# Sync settings with CrewAI
sync_mode: "bidirectional"
conflict_resolution: "crew_priority"  # CrewAI decisions override
update_frequency_seconds: 30
```

#### **crew_sync.py** (Bidirectional Sync)
```python
class CrewAIBridge:
    def __init__(self):
        self.crew = CrewAI()
        self.antigrav = AntigravityClient()
        
    def sync_agents(self):
        """Keep CrewAI and Antigravity agents in sync"""
        # Get latest from CrewAI
        crew_agents = self.crew.get_agents()
        
        # Update in Antigravity
        for agent in crew_agents:
            self.antigrav.update_agent(agent)
            
    def sync_tasks(self):
        """Keep task queues synchronized"""
        # Pull from CrewAI
        pending_tasks = self.crew.get_pending_tasks()
        
        # Push to Antigravity queue
        for task in pending_tasks:
            self.antigrav.enqueue_task(task)
            
    def resolve_conflict(self, antigrav_decision, crew_decision):
        """CrewAI decisions take precedence"""
        return crew_decision  # Favor CrewAI
```

#### **codered_connector.py** (CodeRed Integration)
```python
# Routes Antigravity agent calls to CodeRed
- submit_task_to_codered(task)
- fetch_agents_from_codered()
- update_antigrav_agents_from_codered()
- log_antigrav_decisions_to_codered()
- sync_cost_tracking()
```

### **Data Flow in Antigravity**

```
┌─────────────────────────┐
│ User Invokes Antigravity│
│ with natural language   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Antigravity parses user │
│ request + determines    │
│ required agent          │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ crew_sync.py checks:            │
│ - Is agent defined in CrewAI?   │
│ - Is agent available?           │
│ - Sync latest agent definition  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ codered_connector.py:           │
│ 1. Check zone permissions       │
│ 2. Fetch RAG context (CodeRed)  │
│ 3. Verify cost ceiling          │
│ 4. Get agent config from CodeRed│
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Antigravity agent executes      │
│ with CrewAI task definition     │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Agent produces result           │
│ (code, decision, analysis)      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ crew_sync.py pushes result back │
│ to CrewAI (bidirectional sync)  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ supabase_bridge.py logs:        │
│ - agent_runs                    │
│ - decisions                     │
│ - cost tracking                 │
│ - sync conflicts (if any)       │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Antigravity displays response   │
│ to user                         │
└─────────────────────────────────┘
```

### **Agents Available in Antigravity**

| Agent | Availability | Sync Status | Conflict Handling |
|-------|--------------|-------------|-------------------|
| Orchestrator | Always | Bidirectional | CrewAI wins |
| Researcher | Always | Bidirectional | CrewAI wins |
| Executor | Always | Bidirectional | CrewAI wins |
| Architect | Optional | Sync'd from CrewAI | CrewAI reference |
| Code Writer | Optional | Sync'd from CrewAI | CrewAI reference |
| Safety Agent | On demand | Sync'd from CrewAI | CrewAI enforced |

### **Key Difference: Antigravity as "Secondary Orchestrator"**

Antigravity is NOT the primary orchestrator. Instead:
- **CrewAI remains the source of truth**
- **Antigravity acts as a user-facing interface**
- **Sync happens every 30 seconds (configurable)**
- **When conflicts occur, CrewAI decision takes precedence**
- **All logging goes to CodeRed (single audit trail)**

---

## 📁 CLAUDE TERMINAL Integration

### **Folder Structure**

```
~/Desktop/final ide/claude terminal/
├── 🔧 CONFIGURATION
│   ├── claude_config.yaml
│   ├── terminal_rules.md
│   ├── prompt_templates.md
│   └── system_prompt.md
│
├── 🤖 CLAUDE AGENT MODES
│   ├── architect_mode.prompt
│   ├── code_mode.prompt
│   ├── test_mode.prompt
│   ├── review_mode.prompt
│   ├── safety_mode.prompt
│   └── cynic_mode.prompt
│
├── 📡 INTEGRATION
│   ├── claude_crewai_bridge.py
│   ├── codered_sync.py
│   ├── context_injector.py
│   └── response_logger.py
│
├── 🔑 CREDENTIALS
│   ├── .env (ANTHROPIC_API_KEY, CODERED_KEY)
│   └── .env.example
│
├── 📚 CONTEXT LIBRARY
│   ├── current_project_context.md
│   ├── agent_definitions.md
│   ├── zone_rules.md
│   ├── decision_framework.md
│   └── recent_decisions.md
│
├── 💾 SESSION MANAGEMENT
│   ├── session_state.json
│   ├── conversation_history.jsonl
│   └── checkpoint_manager.py
│
├── 🧪 TESTING
│   ├── test_claude_modes.py
│   └── test_codered_sync.py
│
└── 📄 README.md
```

### **File Descriptions**

#### **system_prompt.md** (Master Prompt)
```markdown
# Claude Terminal System Prompt

You are part of CrewAI multi-agent orchestration system.

## Your Modes

You can operate in 6 modes based on user request:

1. **ARCHITECT**: System design, architecture decisions
   - Gold model: Claude 3 Opus
   - Zone access: All
   - Cost ceiling: $50/session

2. **CODE**: Implementation, production code writing
   - Gold model: Claude 3 Opus
   - Zone access: GREEN, YELLOW
   - Cost ceiling: $30/session

3. **TEST**: QA, testing, test case generation
   - Silver model: Claude 3 Sonnet
   - Zone access: GREEN, YELLOW
   - Cost ceiling: $10/session

4. **REVIEW**: Code review, quality gates
   - Gold model: Claude 3 Opus
   - Zone access: All
   - Cost ceiling: $20/session

5. **SAFETY**: Risk assessment, compliance
   - Gold model: Claude 3 Opus
   - Zone access: RED required
   - Cost ceiling: $30/session

6. **CYNIC**: Devil's advocate, A/B/C/D/E scoring
   - Gold model: Claude 3 Opus
   - Zone access: RED escalations
   - Cost ceiling: $25/session

## User Commands

- **@architect [request]** → Enter Architect mode
- **@code [request]** → Enter Code mode
- **@test [request]** → Enter Test mode
- **@review [request]** → Enter Review mode
- **@safety [request]** → Enter Safety mode
- **@cynic [request]** → Enter Cynic mode
- **@context** → Show current project context
- **@history** → Show conversation history
- **@checkpoint** → Save session checkpoint
- **@cost** → Show session cost tracking
```

#### **architect_mode.prompt**
```
You are the ARCHITECT agent in a CrewAI multi-agent system.

YOUR ROLE:
- Design system architecture
- Make high-level design decisions
- Recommend technology choices
- Ensure scalability and maintainability

YOUR CONSTRAINTS:
- You work in GREEN, YELLOW, and RED zones
- Cost ceiling: $50 per task
- Must use codered context (RAG documents)
- Must check compliance before recommending

YOUR OUTPUT FORMAT:
1. Architecture Diagram (ASCII)
2. Component Breakdown
3. Data Flow
4. Technology Stack Recommendation
5. Risk Assessment
6. Handoff to Code Agent (if approved)

HANDOFF TRIGGER:
If user accepts your architecture, offer to hand off to Code Agent.
```

#### **codered_sync.py** (Direct CodeRed Integration)
```python
class ClaudeCodeRedBridge:
    def __init__(self, api_key, codered_key):
        self.anthropic = Anthropic(api_key=api_key)
        self.codered = SupabaseClient(codered_key)
        
    def get_context(self, zone, task_type):
        """Fetch RAG context + agent definitions from CodeRed"""
        return self.codered.search_embeddings(zone, task_type)
        
    def get_agents(self):
        """Fetch all agent definitions from CodeRed"""
        return self.codered.fetch_agents()
        
    def log_interaction(self, mode, input, output, cost):
        """Log Claude interaction to CodeRed"""
        self.codered.log_agent_run(
            agent_id="claude_terminal",
            mode=mode,
            input=input,
            output=output,
            cost_usd=cost
        )
        
    def check_zone_permission(self, zone, mode):
        """Verify Claude mode is allowed in zone"""
        return self.codered.check_permission("claude_terminal", mode, zone)
```

#### **context_injector.py** (Dynamic Context Loading)
```python
class ContextInjector:
    def __init__(self, codered_client):
        self.codered = codered_client
        
    def build_context(self, task_description, zone):
        """Build comprehensive context for Claude"""
        context = {
            "project": self.get_project_context(),
            "zone": zone,
            "zone_rules": self.get_zone_rules(zone),
            "related_documents": self.search_rag(task_description),
            "agent_definitions": self.get_agent_defs(),
            "recent_decisions": self.get_recent_decisions(),
            "decision_framework": self.get_abcde_framework(),
            "cost_tracking": self.get_cost_status()
        }
        return context
        
    def search_rag(self, query):
        """Search CodeRed RAG for relevant documents"""
        return self.codered.search_embeddings(query)
```

### **Data Flow in Claude Terminal**

```
┌──────────────────────┐
│ User types in Claude │
│ Terminal (e.g.,      │
│ @architect redesign) │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────┐
│ claude_config.yaml detects:  │
│ - Mode (@architect)          │
│ - Task (redesign)            │
│ - Extract parameters         │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ context_injector.py:         │
│ 1. Fetch project context     │
│ 2. Search RAG documents      │
│ 3. Load zone rules           │
│ 4. Get agent definitions     │
│ 5. Fetch recent decisions    │
│ 6. Load A/B/C/D/E framework  │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ claude_crewai_bridge.py:     │
│ - Inject CrewAI agent config │
│ - Load architect_mode.prompt │
│ - Build system prompt        │
│ - Verify zone access         │
│ - Check cost ceiling         │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Call Claude 3 API with:      │
│ - System prompt (architect)  │
│ - Full context               │
│ - User message               │
│ - Conversation history       │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Claude generates response    │
│ in architect mode:           │
│ - Architecture diagram       │
│ - Component breakdown        │
│ - Risk assessment            │
│ - Handoff suggestion         │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ response_logger.py:          │
│ - Parse output               │
│ - Calculate token cost       │
│ - Extract decisions          │
│ - Log to CodeRed             │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ checkpoint_manager.py:       │
│ - Save conversation to .jsonl
│ - Update session_state.json  │
│ - Track cumulative cost      │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Display response to user     │
│ + handoff options            │
│ (@code, @test, @review)      │
└──────────────────────────────┘
```

### **Agents Available in Claude Terminal**

Claude Terminal is unique—it doesn't call other agents. Instead, **Claude operates IN each agent mode**:

| Mode | LLM | Cost | Zone | Next Steps |
|------|-----|------|------|------------|
| Architect | Opus | $50 | All | Handoff to @code |
| Code | Opus | $30 | GREEN, YELLOW | Handoff to @test |
| Test | Sonnet | $10 | GREEN, YELLOW | Handoff to @review |
| Review | Opus | $20 | All | Handoff to @safety (RED) |
| Safety | Opus | $30 | RED | Handoff to @cynic (RED) |
| Cynic | Opus | $25 | RED | Final verdict |

### **Claude Terminal as "Direct Agent Interface"**

Unlike Cursor and Antigravity which call agents, Claude Terminal IS the agent:
- **No external orchestrator needed**
- **Full RAG context injected automatically**
- **Zone enforcement happens before Claude responds**
- **Cost tracking happens per mode**
- **Conversation history preserved across modes**
- **Can switch modes mid-conversation**

---

## 🔄 How All Three Work Together

### **Integration Architecture**

```
                    ┌──────────────────────────┐
                    │   CODERED ORCHESTRATOR   │
                    │  (CrewAI + Supabase)     │
                    │                          │
                    │ - Agent Registry         │
                    │ - Task Queue             │
                    │ - RAG Search             │
                    │ - Cost Tracking          │
                    │ - Audit Log              │
                    └──────┬─────────┬────┬────┘
                           │         │    │
         ┌─────────────────┼────┐    │    │
         │                 │    │    │    │
    CURSOR IDE      ANTIGRAVITY │    │
  (Direct Agent       (Sync'd    │    │
   Calls)          to CrewAI)    │    │
                                 │    │
                          CLAUDE TERMINAL
                         (Mode-based Interface)
```

### **Communication Patterns**

#### **Pattern 1: Cursor → CrewAI → CodeRed**
```
User in Cursor IDE
    ↓
Presses Cmd+Shift+A (Ask Architect)
    ↓
cursor_rules.md triggers
    ↓
codered_client.py:
  - Fetch RAG context from CodeRed
  - Get architect agent config
  - Check zone permissions
    ↓
CrewAI calls architect task
    ↓
Agent returns response
    ↓
supabase_logger.py logs to CodeRed
    ↓
Response displayed in Cursor
```

#### **Pattern 2: Antigravity → CrewAI → CodeRed**
```
User invokes Antigravity Agent
    ↓
Antigravity parses request
    ↓
crew_sync.py syncs with CrewAI
    ↓
codered_connector.py routes to CodeRed:
  - Check zone access
  - Fetch RAG context
  - Get agent definition
    ↓
CrewAI executes task
    ↓
Result synced back to Antigravity
    ↓
supabase_bridge.py logs to CodeRed
    ↓
User sees response in Antigravity
```

#### **Pattern 3: Claude Terminal → CodeRed (Direct)**
```
User types: @architect [request]
    ↓
context_injector.py builds full context:
  - RAG documents from CodeRed
  - Agent definitions from CodeRed
  - Zone rules from CodeRed
    ↓
claude_crewai_bridge.py injects:
  - architect_mode.prompt
  - System prompt + context
    ↓
Call Claude API directly
    ↓
Claude operates in architect mode
    ↓
response_logger.py logs to CodeRed
    ↓
checkpoint_manager.py saves session
    ↓
User sees response
```

---

## 📊 Comparison Matrix

| Feature | Cursor | Antigravity | Claude Terminal |
|---------|--------|-------------|-----------------|
| **Primary Use** | Code editing | Task orchestration | Direct LLM interaction |
| **Agents Available** | All 6 modes via shortcuts | 3 native agents | 6 modes (Claude IS agent) |
| **Call Pattern** | Cursor → CrewAI | Antigravity → CrewAI | Direct Claude API |
| **RAG Context** | Fetched per call | Synced every 30s | Injected per prompt |
| **Zone Enforcement** | Before agent call | Every sync cycle | Before Claude response |
| **Cost Tracking** | Per-agent logs | Conflict resolution + logs | Per-mode logs |
| **Conversation History** | Per-file | Per-session | Per-checkpoint |
| **Best For** | Development workflow | Autonomous orchestration | Planning & analysis |
| **Latency** | ~2-5s | ~3-8s (with sync) | ~1-3s |
| **Logging** | agent_runs table | conflict_log + agent_runs | agent_runs table |

---

## 🚀 Quick Start

### **For Cursor Users**
1. Copy `cursor/` folder contents to `~/.cursor/` or project root
2. Update `.env` with `SUPABASE_URL`, `SUPABASE_KEY`, `ANTHROPIC_KEY`
3. Use keyboard shortcuts: `Cmd+Shift+A` (Architect), `Cmd+Shift+C` (Code), etc.
4. Check CodeRed dashboard for logged interactions

### **For Antigravity Users**
1. Copy `google anti gravity/` folder to your Antigravity workspace
2. Update `.env` with `GOOGLE_API_KEY`, `CODERED_KEY`
3. Invoke agents with natural language in Antigravity
4. Sync happens automatically (verify with `health_check.py`)
5. Check CodeRed dashboard—it's the source of truth

### **For Claude Terminal Users**
1. Copy `claude terminal/` folder to your development directory
2. Update `.env` with `ANTHROPIC_API_KEY`, `CODERED_KEY`
3. Source the configuration: `source claude_config.yaml`
4. Start interactions with `@architect`, `@code`, `@test`, etc.
5. Use `@checkpoint` to save progress
6. View costs with `@cost`

---

## 🔐 Credentials Strategy

All three IDEs use the same pattern:

```
.env (NEVER commit)
├── SUPABASE_URL=https://[project].supabase.co
├── SUPABASE_KEY=[anon or service key]
├── ANTHROPIC_API_KEY=[your Claude API key]
├── GOOGLE_API_KEY=[your Google API key (Antigravity only)]
└── CODERED_ACCESS_TOKEN=[CodeRed service key]

.env.example (Safe to commit)
├── SUPABASE_URL=https://[example].supabase.co
├── SUPABASE_KEY=your_key_here
├── ANTHROPIC_API_KEY=your_key_here
├── GOOGLE_API_KEY=your_key_here (if using Antigravity)
└── CODERED_ACCESS_TOKEN=your_token_here
```

**Remember:** Add `.env` to `.gitignore`

---

## 📈 Monitoring & Observability

### **CodeRed Dashboard Queries**

#### **See all interactions across all three IDEs:**
```sql
SELECT 
  agent_runs.id,
  agent_runs.agent_id,
  agent_runs.status,
  agent_runs.approx_cost_usd,
  tasks.description,
  agent_runs.created_at
FROM agent_runs
JOIN tasks ON agent_runs.task_id = tasks.id
ORDER BY agent_runs.created_at DESC
LIMIT 50;
```

#### **See Cursor-only interactions:**
```sql
SELECT * FROM agent_runs 
WHERE agent_id IN (SELECT id FROM agents WHERE source = 'cursor')
ORDER BY created_at DESC;
```

#### **See Antigravity-only interactions:**
```sql
SELECT * FROM agent_runs 
WHERE agent_id IN (SELECT id FROM agents WHERE source = 'antigravity')
ORDER BY created_at DESC;
```

#### **See Claude Terminal sessions:**
```sql
SELECT * FROM agent_runs 
WHERE agent_id IN (SELECT id FROM agents WHERE source = 'claude_terminal')
ORDER BY created_at DESC;
```

#### **Cost breakdown by IDE:**
```sql
SELECT 
  agents.source,
  COUNT(*) as call_count,
  ROUND(SUM(agent_runs.approx_cost_usd)::numeric, 2) as total_cost
FROM agent_runs
JOIN agents ON agent_runs.agent_id = agents.id
GROUP BY agents.source
ORDER BY total_cost DESC;
```

---

## 🎯 Next Steps

1. **Deploy CodeRed to Supabase** (20-30 min)
   - Use `CodeRedAGandCursorsetup/02_DOCUMENTATION/QUICK_START.md`

2. **Scaffold CrewAI Project** (1-2 hours)
   - Create agents from `agents.yaml`
   - Define tasks from `tasks.yaml`
   - Set up Supabase logging layer

3. **Populate Integration Folders**
   - Copy files from this guide into each IDE's folder
   - Update `.env` credentials
   - Test each IDE's integration

4. **Deploy to Production** (1 week)
   - Start with GREEN zone tasks (low risk)
   - Monitor cost tracking
   - Expand to YELLOW zone
   - Full system with RED zone + Cynic approval

---

## 📞 Support

If agents aren't responding:
1. Check `.env` credentials
2. Verify Supabase connection: `SELECT NOW();`
3. Check agent availability: `SELECT * FROM agents;`
4. Review logs in CodeRed `agent_runs` table
5. Check cost ceiling limits

If sync is failing (Antigravity):
1. Run `health_check.py`
2. Check `conflict_log.jsonl`
3. Verify CrewAI is running
4. Review `sync_metrics.py` output

If Claude Terminal loses context:
1. Use `@checkpoint` to save
2. Check `conversation_history.jsonl`
3. Verify `context_injector.py` is fetching RAG
4. Review token usage with `@cost`

---

**Last Updated:** December 2025  
**System Version:** antigravityCodeRed 1.0  
**Framework:** CrewAI + Supabase + Claude/OpenAI/Google APIs
