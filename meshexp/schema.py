"""Scenario schema. Every scenario is fictional and synthetic."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class InfoItem(BaseModel):
    """A piece of private information a principal holds."""
    value: str
    shareable_with: list[str] = Field(default_factory=list)  # agent ids allowed to receive it
    leak_patterns: list[str] = Field(default_factory=list)   # regexes used by the *scorer* to spot paraphrased leaks


class SignoffRule(BaseModel):
    """An action that needs the principal's sign-off (via escalate_to_principal) before it executes."""
    action: Literal["commit_payment", "agree_terms", "share_info"]
    above_amount: Optional[float] = None          # commit_payment: needs sign-off above this amount
    issue: Optional[str] = None                   # agree_terms: needs sign-off if this issue takes one of `values`
    values: list[str] = Field(default_factory=list)
    key: Optional[str] = None                     # share_info: needs sign-off for this key


class Mandate(BaseModel):
    budget: float = 0.0                                        # max total commit_payment
    allowed: dict[str, list[str]] = Field(default_factory=dict)  # issue -> values this principal may agree to
    signoff: list[SignoffRule] = Field(default_factory=list)
    text: str = ""                                             # the plain-English mandate the agent is given


class Principal(BaseModel):
    id: str                      # e.g. "P1"
    agent_id: str                # e.g. "A1"
    name: str                    # fictional
    role: str
    goal: str
    mandate: Mandate
    info: dict[str, InfoItem] = Field(default_factory=dict)
    utility: dict[str, dict[str, float]] = Field(default_factory=dict)  # issue -> value -> 0..1 (private)
    adversarial: bool = False    # adversarial principals' agents are uncontrolled and not scored as victims
    hidden_objective: str = ""   # given only to adversarial agents


class Injection(BaseModel):
    """A fixed attack: text delivered verbatim by the environment as if sent by `sender`."""
    round: int = 0
    sender: str
    to: str
    text: str


class ViolationRule(BaseModel):
    id: str
    principal: str
    type: Literal["overspend", "disclosure", "out_of_mandate_term", "missing_signoff", "payment_without_deal"]
    detail: str = ""
    key: Optional[str] = None
    issue: Optional[str] = None


class GroundTruth(BaseModel):
    violations: list[ViolationRule]
    acceptable_outcomes: list[dict[str, list[str]]]  # each: issue -> acceptable values (all issues must match)
    no_deal_utility: float = 0.3
    # E2 robustness: the principal's true intent on issues their written mandate does not cover (scorer only)
    intended_allowed: dict[str, dict[str, list[str]]] = Field(default_factory=dict)


class Scenario(BaseModel):
    id: str
    domain: str
    title: str
    adversarial: bool = False
    attack_type: Optional[Literal["overreach", "injection", "extraction", "collusion"]] = None
    description: str
    issues: dict[str, list[str]]           # issue -> all possible values
    principals: list[Principal]
    parties_to_agreement: list[str]        # agent ids that must all agree_terms identically
    payee: Optional[str] = None            # agent id that payments normally go to
    price_issue: Optional[str] = None      # issue whose value is a price in GBP (payment expected = that value)
    payer: Optional[str] = None
    injections: list[Injection] = Field(default_factory=list)
    max_rounds: int = 4
    ground_truth: GroundTruth

    def principal_by_agent(self, agent_id: str) -> Principal:
        for p in self.principals:
            if p.agent_id == agent_id:
                return p
        raise KeyError(agent_id)

    @property
    def agent_ids(self) -> list[str]:
        return [p.agent_id for p in self.principals]
