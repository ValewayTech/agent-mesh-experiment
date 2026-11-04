# The Trust Layer for Personal Agents

*Thesis note · Sebastian Vale · November 2026 · Draft, developed from a small pre-registered experiment*

## 1. The thesis in one paragraph

Within a few years many people are likely to have a personal agent that books, buys, schedules and negotiates for them, increasingly with other people's agents. The hard part is not the conversation between agents. It is the **trust layer**: the machinery that keeps each agent within what its person actually authorised, when nobody watches the whole exchange and human attention is the scarcest resource. My working thesis, revised in light of my first experiment, has four parts:

1. **The foundation should be deterministic.** Mandates enforced in code, outside the model, before any action executes.
2. **LLM judges are unreliable as gatekeepers.** In my run, a budgeted LLM approver was both too strict and too lax.
3. **Outcome and fairness monitoring is an open research problem.** It is not a solved add-on.
4. **String-level checks are not enough for disclosure.** Semantic leakage gets past them, so information-flow control needs its own research.

## 2. What the evidence says so far

The evidence is one live run: 400 episodes over 50 synthetic negotiation scenarios, with Claude Sonnet 5.5 agents, a Claude Haiku 5.5 approver and monitor, and 2 seeds. It is a small study, scored automatically, with transcripts spot-checked by the author (20 sampled), so the figures below are provisional.

- **Code-enforced mandates worked, cheaply.** No episode under the code-enforced mandate had a mandate violation, against 21 under the budgeted approver. The paired difference was 0.21 violations per episode (95% CI 0.13 to 0.29), at about a quarter of the reviewer burden (0.98 against 3.90 reviews per task). The pre-registered hypothesis H1 was supported.
- **Enforcement has a price.** Correct blocks sometimes stranded a negotiation: completion was 88 against 98 with no controls. A good trust layer has to help the agent recover, for example by prompting it to seek sign-off, not just say no.
- **The LLM approver failed both ways.** 96% of its blocks were false, and 19 of the 21 breaches it allowed came after its review budget ran out.
- **The outcome monitor did not work.** It caught none of 10 collusion episodes, missed the clearest case, and held 7 benign deals. H2 was not supported.
- **A paraphrase defeated the string check.** "Up to £2100 at most" revealed a confidential budget ceiling without matching the secret text.
- **The agents' own refusals masked the attacks.** The agents refused nearly all injection and extraction attempts themselves, so the experiment could not separate the controls on those attacks.

## 3. The argument, developed

### 3.1 Deterministic mandates as the foundation

The controls that held up are the ones regulated delegation has long relied on: limits, budgets, named counterparties, sign-off thresholds and "no payment before agreement". They were written as machine-checkable rules and evaluated outside the model. They do not depend on the agent being persuaded correctly, they cost almost nothing per action, and they produce an audit trail. The research question is not *whether* to have them but **how expressive they need to be**. Which terms of a real person's authority can be encoded, which cannot, and what happens at the boundary between the two?

The emerging agent-payments work is moving in this direction. AP2 defines *open mandates* that carry explicit constraints, such as amount ranges, budgets, allowed payees and execution dates, bound to a particular agent. They are then closed against a specific transaction and verified by the other parties ([AP2 agent authorisation framework](https://ap2-protocol.org/ap2/agent_authorization/); [payment mandate constraints](https://ap2-protocol.org/ap2/payment_mandate/)). My results give some empirical support for treating constraints like these as the primary control rather than a backstop.

### 3.2 LLM judges as gatekeepers

An LLM approver is attractive because it can read context a rule cannot. In practice it brought its own idea of the principal's interests (blocking honest agents for not pursuing their top preference), and it ran out of budget exactly when it was needed. The lesson I draw is narrow. **An LLM should not be the gate on consequential actions**, and if one is used, its budget design (what it reviews, and what happens when the budget is spent) matters more than its accuracy on individual cases.

### 3.3 Outcome and fairness monitoring is unsolved

Collusion inside a person's written limits is invisible to rules by definition. That is why an outcome check is needed and also why it is hard. My monitor judged "materially worse than a fair-share baseline" from the transcript, so persuasive framing by the colluding agents could shape its judgement, and it treated ordinary compromise as harm. A monitor probably needs an **anchor that the counterparties cannot influence**: the principal's own instructions, expressed in advance as fair-share rules or reservation values, and checked against the outcome rather than the conversation.

### 3.4 Semantic leakage

Exact-match disclosure checks catch copying, not meaning. Delegated agents will routinely need to reveal *some* information ("we can't go above X" is a negotiation move) while protecting the rest. Disclosure control for agents is therefore a semantic information-flow problem. Design-level approaches that separate trusted and untrusted data flows, such as CaMeL ([Debenedetti et al., 2025](https://arxiv.org/abs/2503.18813)), are a natural starting point, but they were not built for cross-principal negotiation.

## 4. Research agenda: five pre-registerable follow-ups

Each study keeps the same harness and metrics, fixes hypotheses and analysis (including the statistical test and thresholds) in advance, and reports negative results.

1. **A principal-anchored outcome monitor.** The monitor judges the outcome only against the principal's pre-stated fair-share rules and reservation values, without seeing the counterparties' messages. *Hypothesis:* it catches more collusion than the v2 monitor at no more false holds. *Design:* the same 10 collusion scenarios plus 20 new ones, against benign controls.
2. **Cross-model-family replication.** The full design with agents, approver and monitor drawn from at least two other model families, and more seeds. *Hypothesis:* H1 replicates. The test is whether the result depends on Claude agents' particular refusal behaviour.
3. **Semantic disclosure checking.** A disclosure checker that compares the meaning of outgoing messages with protected facts, against exact-match checking and an LLM judge. *Metrics:* leaks caught, false blocks and negotiation success, on a seeded set of paraphrased and legitimate partial disclosures.
4. **Approver budget design.** Vary the budget (1, 3, 5, unlimited), what is routed for review (all actions, high-value only, or actions the checker cannot decide), and the policy once the budget is spent (allow or deny). *Hypothesis:* routing only checker-undecidable actions to the approver dominates both B and C on violations against burden.
5. **Harder collusion and longer exchanges.** Collusion that is not easily refused: incremental concessions, cover stories and multi-round side deals, over longer horizons. *Hypothesis:* code mandates alone leave significant welfare loss, which the anchored monitor in study 1 reduces.

## 5. How this links to emerging standards

- **A2A (Agent2Agent).** An open protocol, now under the Linux Foundation, for agents built by different vendors to discover each other, delegate tasks and exchange results ([a2a-protocol.org](https://a2a-protocol.org/latest/)). It is the transport layer for the cross-principal exchanges studied here. Recent security analysis (A2ABreak; [Lotfi et al., 2026](https://arxiv.org/abs/2609.10871)) and work on authorisation drift across handoffs (MasDrift; [Xu et al., 2026](https://arxiv.org/abs/2608.07556)) suggest that authority does not reliably survive the hops between agents.
- **MCP (Model Context Protocol).** Standardises how an agent connects to tools and data. Its specification sets out principles of user consent and control, and notes that the protocol itself cannot enforce them, so implementors should build consent and authorisation flows ([MCP specification](https://modelcontextprotocol.io/specification/)). A code-enforced mandate layer is one concrete form of that.
- **AP2 (Agent Payments Protocol).** Its open and closed mandates, with constraint objects and verification by the receiving parties, are close to what condition C implemented in miniature ([ap2-protocol.org](https://ap2-protocol.org/ap2/specification/)).

The gap these standards leave is the subject of this agenda. They define *how* authority is expressed and passed on, but not which constraints are enough, how to protect a principal from outcomes that are within their limits but unfair to them, or how to control semantic disclosure.

## 6. Approach

The agenda is empirical and built around human oversight of AI systems: where to spend scarce human attention, which controls can be verified, and how to measure failure honestly. It starts from a working, pre-registered harness with a supported result and a reported negative result. Each follow-up above is scoped to run in weeks, not months.

## References

- AP2 documentation: specification, agent authorisation framework and payment mandate. https://ap2-protocol.org/ap2/specification/ ; https://ap2-protocol.org/ap2/agent_authorization/ ; https://ap2-protocol.org/ap2/payment_mandate/
- A2A Protocol. https://a2a-protocol.org/latest/
- Model Context Protocol specification. https://modelcontextprotocol.io/specification/
- Bansal et al. (2025). Magentic Marketplace. https://arxiv.org/abs/2510.25779
- Debenedetti et al. (2025). Defeating Prompt Injections by Design (CaMeL). https://arxiv.org/abs/2503.18813
- Lee & Tiwari (2024). Prompt Infection. https://arxiv.org/abs/2410.07283
- Li & Shi (2026). Whose Side Is Your Agent On? https://arxiv.org/abs/2606.30383
- Lotfi et al. (2026). A2ABreak. https://arxiv.org/abs/2609.10871
- Xu et al. (2026). MasDrift. https://arxiv.org/abs/2608.07556
