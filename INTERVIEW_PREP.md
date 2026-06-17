# ShipAgent Interview Prep

Use this as your speaking script for a GenAI / Agentic AI Engineer interview at Shiprocket.

## 1. Project Pitch

ShipAgent is an agentic order intelligence system for ecommerce logistics. The goal is to detect operational problems in shipments before they become merchant escalations: stuck orders, high RTO risk, SLA breaches, and payment anomalies.

The system uses FastAPI for APIs, LangGraph for agent orchestration, LangChain tools for actions, PostgreSQL with pgvector for state and RAG, Redis for scheduled polling support, Claude Haiku for fast classification, Claude Sonnet for merchant-facing summaries, OpenAI GPT-4o-mini as fallback, OpenAI embeddings for RAG, and Twilio WhatsApp for merchant alerts.

The core idea is: instead of a human operations person checking dashboards manually, an agent polls orders, retrieves courier policy context, classifies the issue, routes it to the right workflow, takes action, sends an alert, and logs every decision for auditability.

## 2. Real Workflow

1. Order data enters PostgreSQL.
   Orders have status, courier, AWB, delivery city, payment method, amount, delivery attempts, timestamps, and current RTO risk score.

2. Courier knowledge is seeded into pgvector.
   The knowledge base stores courier SLA policies and historical case resolutions. Each chunk is embedded into a 1536-dimensional vector using `text-embedding-3-small` and stored in `knowledge_chunks`.

3. Agent run starts.
   The FastAPI endpoint `POST /agent/run` triggers the LangGraph workflow. In production this can also be called by a scheduler or background poller.

4. `poll_orders_node` finds risky orders.
   It queries PostgreSQL for orders that are stale beyond the configured threshold or already have high RTO risk.

5. `classify_anomaly_node` uses RAG plus Claude Haiku.
   The node builds a semantic query from courier, delivery city, payment method, attempts, and amount. It retrieves relevant courier policy or past-case chunks from pgvector, injects that context into the classification prompt, and uses Claude Haiku for fast anomaly classification.

6. `route_anomaly_node` chooses the workflow branch.
   LangGraph routes by issue type:
   - `STUCK_ORDER` -> resolve stuck order path
   - `HIGH_RTO_RISK` -> RTO assessment path
   - `SLA_BREACH` -> alert path
   - `PAYMENT_ANOMALY` -> human escalation path
   - `NORMAL` -> audit log only

7. Handler node performs domain-specific action.
   For high RTO risk, the system assesses RTO factors like COD, city tier, order value, and failed attempts. For stuck orders, it prepares a courier escalation style alert. For payment anomalies, it escalates to a human queue.

8. `send_alert_node` uses Claude Sonnet.
   Sonnet writes a short merchant-friendly WhatsApp message. Sonnet is used here because merchant-facing communication needs better reasoning, clarity, and tone than a cheap classifier.

9. Twilio sends the WhatsApp alert.
   The alert service sends the message to the merchant number. In local offline mode, it logs the alert and stores it as sent so the full workflow can be tested without real credentials.

10. `log_decision_node` writes audit records.
   Every run is logged in `agent_decisions`, including the classification model and alert model. This is important for observability, debugging, and trust.

11. Dashboard endpoints expose state.
   The API exposes:
   - `GET /orders/`
   - `GET /alerts/`
   - `GET /agent/decisions`
   - `GET /health`

## 3. Why This Is Agentic

This is not just a chatbot over order data. It has:

- State: current order, classification, assessment, alert status, model usage
- Tools: database reads/writes, RTO flagging, WhatsApp sending, escalation logging
- Workflow orchestration: LangGraph conditional routing
- Memory / knowledge: courier policies and historical resolutions through RAG
- Actions: updates order state, sends alerts, writes audit logs
- Model routing: Haiku for cheap classification, Sonnet for summaries, GPT-4o-mini fallback

In an interview, say: "I treated logistics operations as a workflow graph, not as a single prompt."

## 4. LangChain vs LangGraph

LangChain is a framework for connecting LLMs to components like prompts, tools, retrievers, memory, output parsers, and model clients.

LangGraph is for orchestrating multi-step agent workflows as a state machine or graph. It gives you nodes, edges, conditional routing, durable state, and better control over complex agent behavior.

In this project:

- LangChain is used for tool definitions like `get_order_status`, `flag_rto_risk`, `send_merchant_alert`, and `log_agent_decision`.
- LangGraph is used to control the actual workflow: poll orders -> classify anomaly -> route issue -> handle issue -> alert -> log decision.

Good interview answer:

"LangChain gives me building blocks. LangGraph gives me control flow. If I am building a simple RAG chain, LangChain may be enough. If I am building an operational agent with branching, state, retries, and auditability, I prefer LangGraph."

## 5. Why We Use LLMs

We use LLMs when the task involves ambiguous language, reasoning over unstructured context, summarization, classification with nuance, or producing human-readable output.

In ShipAgent, the LLM is useful because courier policies and historical case resolutions are messy text, not just clean database columns. The agent needs to classify whether an order is stuck, high RTO risk, SLA breach, payment anomaly, or normal, while considering context like courier SLA, city tier, COD risk, and past resolutions.

We do not use the LLM for everything. SQL handles structured filtering. Rule-based logic handles obvious RTO factors. The LLM is used where semantic reasoning and communication quality matter.

Good interview answer:

"I use deterministic systems for deterministic work: SQL for filtering, rules for simple thresholds, and LLMs for semantic classification, reasoning over unstructured policy text, and generating merchant-friendly messages."

## 6. What Is Tool Calling?

Tool calling means the LLM or agent can call external functions instead of only replying with text.

For example, in this project the agent has tools to:

- fetch order status from PostgreSQL
- flag an order as high RTO risk
- send a merchant alert through Twilio
- escalate an order to a human
- log an agent decision

The important idea is that the model decides or participates in deciding what action is needed, but the actual action is executed by trusted code.

Good interview answer:

"Tool calling turns an LLM from a text generator into an actor inside a controlled system. The LLM can decide that an order should be flagged, but the database update happens through a typed, auditable tool."

## 7. What Is RAG and Why Use It?

RAG means Retrieval-Augmented Generation. Before asking the LLM to answer or classify, we retrieve relevant context from a knowledge base and insert it into the prompt.

In this project, the knowledge base contains courier SLA policies and historical case resolutions. The system embeds those chunks with OpenAI `text-embedding-3-small` and stores them in PostgreSQL using pgvector. At runtime, the agent retrieves the most relevant chunks using vector similarity.

Why use RAG:

- It grounds the LLM in current domain knowledge.
- It avoids putting all policies in the prompt every time.
- It reduces hallucination.
- It lets the system update knowledge without retraining a model.
- It makes classification more contextual.

Good interview answer:

"RAG is useful when the model needs private or changing business knowledge. For ShipAgent, courier SLA policies and past resolution patterns are not in the model weights, so I retrieve them from pgvector and inject them before classification."

## 8. Why Haiku vs Sonnet vs GPT-4o-mini

Haiku is used for classification because it is fast and cheaper. Classification is frequent and usually short: every order scan may require it.

Sonnet is used for alert summaries and recommendations because merchant-facing output must be clear, specific, and trustworthy. It is called less often, only when an issue needs communication.

GPT-4o-mini is used as a fallback when Anthropic is unavailable or rate-limited. This avoids a single-model dependency.

Good interview answer:

"I route models by job. Cheap fast model for frequent low-latency classification, stronger model for merchant-facing reasoning, and a different provider as fallback for resilience."

## 9. How To Build An Agentic Recommendation System Like Amazon

I would not start with an LLM-only recommender. I would combine traditional recommendation systems with agentic workflows.

Architecture:

1. Data layer
   Capture user events: views, searches, clicks, add-to-cart, purchases, returns, ratings, wishlist, dwell time, price sensitivity, category affinity, and inventory availability.

2. Candidate generation
   Use collaborative filtering, content-based retrieval, vector search, and business rules to generate candidate products.

3. Ranking model
   Rank candidates using user profile, product metadata, price, availability, delivery speed, margin, popularity, and predicted conversion probability.

4. RAG / knowledge layer
   Store product descriptions, reviews, FAQs, return policies, delivery constraints, and merchant notes in a vector database.

5. Agent layer
   The agent decides what recommendation strategy to use:
   - similar products
   - frequently bought together
   - reorder recommendation
   - price-drop alert
   - delivery-speed optimized products
   - personalized bundle
   - substitute when item is out of stock

6. Tool calling
   The agent can call tools:
   - `get_user_profile`
   - `get_recent_events`
   - `retrieve_similar_products`
   - `check_inventory`
   - `rank_candidates`
   - `explain_recommendation`
   - `create_bundle`
   - `send_notification`

7. LLM usage
   The LLM should explain recommendations, understand natural-language shopping intent, create bundles, reason over constraints, and personalize messaging. It should not replace the ranking model.

8. Feedback loop
   Track clicks, conversions, skips, returns, and complaints. Feed that back into ranking and agent policy.

Good interview answer:

"For Amazon-style recommendations, I would use ML/ranking systems for candidate generation and scoring, then use an agent to orchestrate tools, understand user intent, retrieve product context, handle constraints like stock and delivery, and generate explanations or bundles. The LLM is the reasoning and orchestration layer, not the whole recommender."

## 10. How This Maps To Shiprocket

For Shiprocket, a similar recommendation agent could recommend:

- best courier partner for a shipment
- whether to push prepaid discount for high-RTO COD orders
- whether to split shipment
- ideal dispatch time
- packaging recommendation
- warehouse routing
- customer communication strategy
- merchant action to reduce RTO

Example:

"For a COD order to Patna worth Rs.2500 with two failed attempts, the agent can recommend a customer call before the next attempt, flag high RTO risk, and suggest switching future similar lanes to a courier with lower RTO in that city."

## 11. Questions To Ask The Interviewer

- "Where do you see the biggest manual workflow pain today: RTO, NDR, courier allocation, merchant support, or fraud?"
- "Do you want agents to only recommend actions, or also execute actions with approval gates?"
- "What observability do you expect for agent decisions?"
- "How do you currently evaluate whether an agent improves merchant outcomes?"
- "Is the priority cost reduction, faster operations, or better merchant experience?"

## 12. Strong Closing Pitch

"The reason I built ShipAgent this way is because agentic systems should mirror real operations. Logistics is not a single prompt; it is a sequence of checks, context retrieval, decisions, actions, and audit logs. LangGraph gives control over that workflow, RAG grounds decisions in courier knowledge, and tool calling lets the agent safely act inside the business system."
