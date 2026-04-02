import json
import re
from datetime import datetime
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from app.db.session import get_db
from app.core.rag import rag_service


class ComplianceState(TypedDict):
    receipt_data: dict
    user_profile: dict
    policy_rules: List[dict]
    reasoning_steps: List[str]
    verdict: str | None
    explanation: str | None
    normalized_data: dict | None
    retrieved_rules: List[dict] | None


class ComplianceAgent:
    def __init__(self):
        self.db = get_db()
        self.llm = ChatOpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio",
            model="qwen3.5-9b-claude-4.6-opus-uncensored-distilled",
            temperature=0.0 ,
            timeout=360.0
        )

    async def check_compliance(self, receipt_data: dict, user_profile: dict) -> dict:
        state = ComplianceState(
            receipt_data=receipt_data,
            user_profile=user_profile,
            policy_rules=[],
            reasoning_steps=[],
            verdict=None,
            explanation=None,
            normalized_data=None,
            retrieved_rules=None
        )

        graph = StateGraph(ComplianceState)
        graph.add_node("extract", self._step_extract_normalize)
        graph.add_node("retrieve_rules", self._step_retrieve_rules)
        graph.add_node("generate_verdict", self._step_generate_verdict)

        graph.set_entry_point("extract")
        graph.add_edge("extract", "retrieve_rules")
        graph.add_edge("retrieve_rules", "generate_verdict")
        graph.add_edge("generate_verdict", END)

        compiled = graph.compile()
        result = await compiled.ainvoke(state)

        return {
            "verdict": result.get('verdict', 'FLAGGED'),
            "explanation": result.get('explanation', 'Error processing'),
            "reasoning_steps": result.get('reasoning_steps', []),
            "compliance_score": result.get('compliance_score', 0.5)
        }

    async def _step_extract_normalize(self, state: ComplianceState) -> dict:
        steps = state.get('reasoning_steps', [])
        raw = state['receipt_data']
        normalized = {
            'merchant': raw.get('merchant', 'Unknown'),
            'amount': round(abs(float(raw.get('amount', 0))), 2),
            'date': raw.get('date', 'Unknown'),
            'category': raw.get('category', 'Other')
        }
        steps.append(f"✓ Normalized data: ${normalized['amount']} at {normalized['merchant']}")
        return {"normalized_data": normalized, "reasoning_steps": steps}

    async def _step_retrieve_rules(self, state: ComplianceState) -> dict:
        steps = state.get('reasoning_steps', [])
        norm = state.get('normalized_data', {})
        prof = state.get('user_profile', {})

        query = f"merchant: {norm.get('merchant')} location: {prof.get('city')} spending limits rules"
        results = rag_service.find_similar_transactions(query=query)

        rules = [{"text": r.get('metadata', {}).get('rule_text', '')} for r in results]
        steps.append(f"✓ Retrieved {len(rules)} relevant policy rules from RAG")

        return {"retrieved_rules": rules, "reasoning_steps": steps}

    async def _step_generate_verdict(self, state: ComplianceState) -> dict:
        steps = state.get('reasoning_steps', [])
        norm = state.get('normalized_data', {})
        rules = state.get('retrieved_rules', [])
        prof = state.get('user_profile', {})

        policy_context = "\n".join([r['text'] for r in rules]) if rules else "No specific policies found."

        prompt = PromptTemplate.from_template(
            """You are the Lead Corporate Expense Auditor for Tarion, a Canadian corporation. Evaluate claims against the 'Tarion Travel & Expense Reimbursement Policy'. Use SUCCESS, FLAGGED, or REJECTED. Assume all values are in CAD. Pay attention to the $35 lunch cap and GTA mileage rules.

            EMPLOYEE PROFILE:
            User ID: {user_id}
            Office Location: {office_location}
            Manager Pre-Approval on File: {manager_approval}

            RECEIPT DATA:
            Merchant: {merchant}
            Amount: ${amount}
            Date: {date}
            Category: {category}

            RELEVANT POLICY RULES FROM TARION'S POLICY:
            {policies}

            Based strictly on the above policies, is this expense SUCCESS, REJECTED, or FLAGGED for manual review?

            Format your response exactly as:
            VERDICT: [SUCCESS/REJECTED/FLAGGED]
            EXPLANATION: [Your detailed explanation referencing the specific Tarion policy section]"""
        )

        formatted_prompt = prompt.format(
            user_id=prof.get('user_id', 'Unknown'),
            office_location=prof.get('office_location', 'Unknown'),
            manager_approval=prof.get('manager_approval', False),
            merchant=norm.get('merchant'),
            amount=norm.get('amount'),
            date=norm.get('date'),
            category=norm.get('category'),
            policies=policy_context
        )

        steps.append(f"✓ Sending data to {self.llm.model_name}...")
        try:
            ai_response = await self.llm.ainvoke(formatted_prompt)
            resp = ai_response.content.upper()

            verdict = (
                "SUCCESS" if "VERDICT: SUCCESS" in resp
                else "REJECTED" if "VERDICT: REJECTED" in resp
                else "FLAGGED"
            )
            score = 0.95 if verdict == "SUCCESS" else 0.1 if verdict == "REJECTED" else 0.5
            explanation_parts = re.split(r"EXPLANATION:", ai_response.content, maxsplit=1, flags=re.IGNORECASE)
            if len(explanation_parts) > 1:
                expl = explanation_parts[1].strip()
            else:
                expl = ai_response.content

            steps.append(f"✓ AI decided: {verdict}")
            return {
                "verdict": verdict,
                "explanation": expl,
                "compliance_score": score,
                "reasoning_steps": steps
            }

        except Exception as e:
            steps.append(f"✗ AI Error: {str(e)}")
            return {
                "verdict": "FLAGGED",
                "explanation": f"AI Error: {e}",
                "compliance_score": 0.5,
                "reasoning_steps": steps
            }