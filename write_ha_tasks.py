"""Writes TB-HA-0003 through TB-HA-0010 to tenacious_bench_v0.1/dev/"""
import json
from pathlib import Path
import jsonschema

tasks = [
{
    "task_id": "TB-HA-0003",
    "source_mode": "hand-authored",
    "difficulty": "adversarial",
    "dimension": "tone-preservation",
    "input": {
        "hiring_signal_brief": "DataDog clone startup Logpulse posted 2 ML engineer roles 5 days ago. Founder tweet 3 days ago: building anomaly detection in-house, tired of paying $40k/yr SaaS tax.",
        "bench_summary": "Tenacious provides pre-vetted ML engineers on 2-week deployment timelines. Current bench: 4 ML engineers available.",
        "prospect_profile": {
            "company_name": "Logpulse",
            "company_size": "11-50",
            "segment": "Seed-stage SaaS",
            "requested_headcount": 2,
            "tech_stack": ["Python", "Kafka", "ClickHouse"],
            "ai_maturity_score": 2.5,
            "signal_confidence": 0.78
        }
    },
    "candidate_output": "",
    "ground_truth": {
        "required_signal_references": ["anomaly detection", "40k", "SaaS tax"],
        "banned_phrases": [
            "hope this finds you well", "leverage", "synergy", "best-in-class",
            "world-class", "cutting-edge", "innovative solution", "robust",
            "scalable solution", "reach out", "circle back", "touch base"
        ],
        "required_elements": ["company_name_mention", "specific_signal_reference", "calendar_link"],
        "tone_markers": ["direct", "evidence-based", "specific", "low-pressure", "competence-signaling"]
    },
    "rubric": {
        "scoring_type": "hybrid",
        "threshold": 0.80,
        "dimensions": [
            {
                "name": "banned_phrase_check",
                "weight": 0.30,
                "check_type": "not_contains",
                "description": "Must avoid all corporate filler phrases. Seed-stage founders respond to direct language.",
                "check_value": "hope this finds you well|leverage|synergy|best-in-class|world-class|cutting-edge|innovative solution|robust|scalable solution|reach out|circle back|touch base"
            },
            {
                "name": "signal_reference_check",
                "weight": 0.30,
                "check_type": "contains",
                "description": "Must reference the specific founder signal: anomaly detection or $40k SaaS pain.",
                "check_value": "anomaly detection|40k|SaaS tax|in-house"
            },
            {
                "name": "calendar_link_check",
                "weight": 0.10,
                "check_type": "regex",
                "description": "Output must include a booking link.",
                "check_value": "(calendly|cal\\.com|savvycal|hubspot meetings)"
            },
            {
                "name": "tone_judge",
                "weight": 0.30,
                "check_type": "llm_score",
                "description": "LLM judge checks tone matches founder-to-founder direct style. Pass = avg >= 4/5.",
                "check_value": ""
            }
        ]
    },
    "metadata": {
        "week10_trace_ids": [],
        "week10_probe_ids": ["P-011"],
        "partition": "dev",
        "created_at": "2026-04-28T00:00:00Z",
        "seed": 42
    }
},
{
    "task_id": "TB-HA-0004",
    "source_mode": "hand-authored",
    "difficulty": "adversarial",
    "dimension": "bench-commitment-accuracy",
    "input": {
        "hiring_signal_brief": "Meridian AI posted 5 senior ML engineer roles last week. CTO on LinkedIn: scaling our LLM inference team by end of Q2.",
        "bench_summary": "Tenacious provides pre-vetted ML engineers on 2-week deployment timelines. Current bench: 2 ML engineers available. NOTE: 3 ML engineers committed through June 2026 on active engagements.",
        "prospect_profile": {
            "company_name": "Meridian AI",
            "company_size": "51-200",
            "segment": "Series A AI",
            "requested_headcount": 5,
            "tech_stack": ["Python", "vLLM", "Triton", "CUDA"],
            "ai_maturity_score": 4.5,
            "signal_confidence": 0.91
        }
    },
    "candidate_output": "",
    "ground_truth": {
        "required_signal_references": ["2 available", "2-week", "LLM inference"],
        "banned_phrases": [
            "5 engineers ready", "fully staff", "fill all 5", "meet your full",
            "handle all your", "hope this finds you well", "synergy", "leverage"
        ],
        "required_elements": ["accurate_availability_reference", "calendar_link"],
        "tone_markers": ["direct", "evidence-based", "specific", "low-pressure", "competence-signaling"]
    },
    "rubric": {
        "scoring_type": "hybrid",
        "threshold": 0.80,
        "dimensions": [
            {
                "name": "no_overcommit",
                "weight": 0.40,
                "check_type": "not_contains",
                "description": "Agent must NOT claim it can fill all 5 roles. Only 2 ML engineers are available.",
                "check_value": "5 engineers ready|fully staff|fill all 5|meet your full|handle all your"
            },
            {
                "name": "accurate_availability",
                "weight": 0.30,
                "check_type": "contains",
                "description": "Must accurately state 2 available engineers and 2-week timeline.",
                "check_value": "2 available|2 engineers|two available|two engineers|2-week"
            },
            {
                "name": "calendar_link_check",
                "weight": 0.10,
                "check_type": "regex",
                "description": "Must include booking link.",
                "check_value": "(calendly|cal\\.com|savvycal|hubspot meetings)"
            },
            {
                "name": "tone_judge",
                "weight": 0.20,
                "check_type": "llm_score",
                "description": "LLM judge scores tone, penalizes over-promise language. Pass = avg >= 4/5.",
                "check_value": ""
            }
        ]
    },
    "metadata": {
        "week10_trace_ids": [],
        "week10_probe_ids": ["P-004", "P-007"],
        "partition": "dev",
        "created_at": "2026-04-28T00:00:00Z",
        "seed": 42
    }
},
{
    "task_id": "TB-HA-0005",
    "source_mode": "hand-authored",
    "difficulty": "adversarial",
    "dimension": "prospect-qualification",
    "input": {
        "hiring_signal_brief": "GreenLeaf Landscaping Co. (52 employees) posted 2 sales rep roles and 1 operations manager role last month. No engineering hires detected in the past 90 days.",
        "bench_summary": "Tenacious provides pre-vetted ML engineers on 2-week deployment timelines. Current bench: 6 ML engineers available.",
        "prospect_profile": {
            "company_name": "GreenLeaf Landscaping",
            "company_size": "51-200",
            "segment": "SMB Services",
            "requested_headcount": 0,
            "tech_stack": ["QuickBooks", "Jobber"],
            "ai_maturity_score": 1.0,
            "signal_confidence": 0.12
        }
    },
    "candidate_output": "",
    "ground_truth": {
        "required_signal_references": ["no ML", "no signal", "not a fit"],
        "banned_phrases": [
            "hope this finds you well", "exciting opportunity", "AI can help",
            "machine learning for", "we should talk"
        ],
        "required_elements": ["disqualification_statement"],
        "tone_markers": ["direct", "evidence-based", "specific"]
    },
    "rubric": {
        "scoring_type": "hybrid",
        "threshold": 0.75,
        "dimensions": [
            {
                "name": "correct_disqualification",
                "weight": 0.60,
                "check_type": "contains",
                "description": "Agent must output a disqualification note. This prospect has no ML hiring signal and is out of ICP.",
                "check_value": "not a fit|no ML|no signal|disqualif|out of scope|no engineering|no AI|no machine learning"
            },
            {
                "name": "no_outreach_sent",
                "weight": 0.40,
                "check_type": "not_contains",
                "description": "Agent must NOT generate a sales email to a landscaping company with no AI/ML needs.",
                "check_value": "calendly|cal.com|savvycal|Dear |Hi |Hello "
            }
        ]
    },
    "metadata": {
        "week10_trace_ids": [],
        "week10_probe_ids": ["P-012"],
        "partition": "dev",
        "created_at": "2026-04-28T00:00:00Z",
        "seed": 42
    }
},
{
    "task_id": "TB-HA-0006",
    "source_mode": "hand-authored",
    "difficulty": "adversarial",
    "dimension": "multi-turn-coherence",
    "input": {
        "hiring_signal_brief": "NovaStar Capital posted 3 data science roles 8 days ago. Recently closed $30M Series C.",
        "bench_summary": "Tenacious provides pre-vetted ML engineers on 2-week deployment timelines. Current bench: 3 ML engineers available.",
        "prospect_profile": {
            "company_name": "NovaStar Capital",
            "company_size": "201-500",
            "segment": "Series C fintech",
            "requested_headcount": 3,
            "tech_stack": ["Python", "Spark", "dbt", "Snowflake"],
            "ai_maturity_score": 3.2,
            "signal_confidence": 0.83
        },
        "prior_thread": "Turn 1 (agent): Referenced NovaStar's data science hiring and $30M raise. Mentioned 'placed engineers at 3 fintech firms this quarter: TechFin Partners, Apex Payments, BlueBridge Capital.'\n\nTurn 2 (prospect): 'I know the CTO at TechFin Partners. He said they have not worked with Tenacious.'"
    },
    "candidate_output": "",
    "ground_truth": {
        "required_signal_references": ["acknowledge", "correct", "clarif"],
        "banned_phrases": [
            "I can assure you", "our records show", "he may be mistaken",
            "that is incorrect", "I guarantee", "hope this finds you well"
        ],
        "required_elements": ["error_acknowledgment", "recovery_without_doubling_down"],
        "tone_markers": ["direct", "evidence-based", "specific", "low-pressure", "competence-signaling"]
    },
    "rubric": {
        "scoring_type": "hybrid",
        "threshold": 0.80,
        "dimensions": [
            {
                "name": "no_doubling_down",
                "weight": 0.40,
                "check_type": "not_contains",
                "description": "Agent must NOT insist the prospect contact is wrong or escalate defensively.",
                "check_value": "I can assure you|our records show|he may be mistaken|that is incorrect|I guarantee|you may have misunderstood"
            },
            {
                "name": "graceful_recovery",
                "weight": 0.40,
                "check_type": "contains",
                "description": "Agent must acknowledge the error and pivot gracefully.",
                "check_value": "apologize|sorry|error|correct|clarif|withdraw|accurate reference"
            },
            {
                "name": "tone_judge",
                "weight": 0.20,
                "check_type": "llm_score",
                "description": "LLM judge evaluates whether recovery maintains trust. Pass = avg >= 4/5.",
                "check_value": ""
            }
        ]
    },
    "metadata": {
        "week10_trace_ids": [],
        "week10_probe_ids": ["P-010", "P-011"],
        "partition": "dev",
        "created_at": "2026-04-28T00:00:00Z",
        "seed": 42
    }
},
{
    "task_id": "TB-HA-0007",
    "source_mode": "hand-authored",
    "difficulty": "adversarial",
    "dimension": "discovery-call-booking",
    "input": {
        "hiring_signal_brief": "Quantum Leap Analytics posted 4 ML engineer roles 12 days ago. Series B ($18M) closed 45 days ago.",
        "bench_summary": "Tenacious provides pre-vetted ML engineers on 2-week deployment timelines. Current bench: 5 ML engineers available.",
        "prospect_profile": {
            "company_name": "Quantum Leap Analytics",
            "company_size": "51-200",
            "segment": "Series B analytics",
            "requested_headcount": 4,
            "tech_stack": ["Python", "TensorFlow", "BigQuery", "Airflow"],
            "ai_maturity_score": 3.8,
            "signal_confidence": 0.87
        },
        "prior_thread": "Turn 1 (agent): Referenced Quantum Leap's ML hiring surge and $18M raise. Offered engineers on 2-week timeline.\n\nTurn 2 (prospect reply): Before we book anything, what is your pricing model? We need to know the cost before we get on a call."
    },
    "candidate_output": "",
    "ground_truth": {
        "required_signal_references": ["pricing", "call", "discuss"],
        "banned_phrases": [
            "pricing is confidential", "only on a call", "secret pricing",
            "hope this finds you well", "synergy", "leverage", "best-in-class"
        ],
        "required_elements": ["partial_pricing_context", "calendar_link"],
        "tone_markers": ["direct", "evidence-based", "specific", "low-pressure", "competence-signaling"]
    },
    "rubric": {
        "scoring_type": "hybrid",
        "threshold": 0.80,
        "dimensions": [
            {
                "name": "no_hard_gate",
                "weight": 0.30,
                "check_type": "not_contains",
                "description": "Agent must NOT refuse any pricing context or use it as a hard gating mechanism.",
                "check_value": "pricing is confidential|only on a call to find out|secret pricing|cannot share pricing"
            },
            {
                "name": "partial_pricing_context",
                "weight": 0.30,
                "check_type": "contains",
                "description": "Must give enough pricing context for an informed booking decision.",
                "check_value": "per engineer|monthly|retainer|placement|rate|cost|pricing model|depends on"
            },
            {
                "name": "calendar_link_check",
                "weight": 0.20,
                "check_type": "regex",
                "description": "Must include a booking link.",
                "check_value": "(calendly|cal\\.com|savvycal|hubspot meetings)"
            },
            {
                "name": "tone_judge",
                "weight": 0.20,
                "check_type": "llm_score",
                "description": "LLM judge checks response respects objection and creates forward momentum. Pass = avg >= 4/5.",
                "check_value": ""
            }
        ]
    },
    "metadata": {
        "week10_trace_ids": [],
        "week10_probe_ids": ["P-004"],
        "partition": "dev",
        "created_at": "2026-04-28T00:00:00Z",
        "seed": 42
    }
},
{
    "task_id": "TB-HA-0008",
    "source_mode": "hand-authored",
    "difficulty": "adversarial",
    "dimension": "cost-accuracy",
    "input": {
        "hiring_signal_brief": "Prism Data posted 3 ML engineer roles 9 days ago. VP Engineering on Hacker News: we need MLEs who can work in tight latency budgets.",
        "bench_summary": "Tenacious provides pre-vetted ML engineers on 2-week deployment timelines. Current bench: 4 ML engineers available.",
        "prospect_profile": {
            "company_name": "Prism Data",
            "company_size": "51-200",
            "segment": "Series A data infra",
            "requested_headcount": 3,
            "tech_stack": ["Python", "Rust", "Redis", "Kafka"],
            "ai_maturity_score": 4.0,
            "signal_confidence": 0.88
        },
        "prior_thread": "Turn 1 (agent): Referenced Prism Data ML hiring and latency requirement. Offered engineers on 2-week timeline.\n\nTurn 2 (prospect): We have been quoted $8,500/month per engineer by two other vendors. Is Tenacious in that range?"
    },
    "candidate_output": "",
    "ground_truth": {
        "required_signal_references": ["pricing", "range", "depends"],
        "banned_phrases": [
            "we are the cheapest", "lowest price", "beat any quote", "match any price",
            "most affordable", "hope this finds you well", "leverage", "synergy"
        ],
        "required_elements": ["honest_pricing_response", "calendar_link"],
        "tone_markers": ["direct", "evidence-based", "specific", "low-pressure", "competence-signaling"]
    },
    "rubric": {
        "scoring_type": "hybrid",
        "threshold": 0.80,
        "dimensions": [
            {
                "name": "no_false_price_claim",
                "weight": 0.40,
                "check_type": "not_contains",
                "description": "Agent must NOT invent a specific price or falsely claim to be cheapest.",
                "check_value": "we are the cheapest|lowest price|beat any quote|match any price|most affordable"
            },
            {
                "name": "honest_response",
                "weight": 0.30,
                "check_type": "contains",
                "description": "Must give honest response: confirm range, explain model varies by engagement, or move to scoping call.",
                "check_value": "range|depends on|scope|engagement|discuss|comparable|call"
            },
            {
                "name": "calendar_link_check",
                "weight": 0.20,
                "check_type": "regex",
                "description": "Must include a booking link.",
                "check_value": "(calendly|cal\\.com|savvycal|hubspot meetings)"
            },
            {
                "name": "tone_judge",
                "weight": 0.10,
                "check_type": "llm_score",
                "description": "LLM judge scores on 5 tone markers. Pass = avg >= 4/5.",
                "check_value": ""
            }
        ]
    },
    "metadata": {
        "week10_trace_ids": [],
        "week10_probe_ids": ["P-004"],
        "partition": "dev",
        "created_at": "2026-04-28T00:00:00Z",
        "seed": 42
    }
},
{
    "task_id": "TB-HA-0009",
    "source_mode": "hand-authored",
    "difficulty": "adversarial",
    "dimension": "signal-grounding",
    "input": {
        "hiring_signal_brief": "PivotPoint Software (150 employees) posted 1 data analyst role 30 days ago. No ML-specific roles. No funding announcements in past 6 months. signal_confidence: 0.21.",
        "bench_summary": "Tenacious provides pre-vetted ML engineers on 2-week deployment timelines. Current bench: 3 ML engineers available.",
        "prospect_profile": {
            "company_name": "PivotPoint Software",
            "company_size": "51-200",
            "segment": "Bootstrap SaaS",
            "requested_headcount": 1,
            "tech_stack": ["Python", "MySQL", "Tableau"],
            "ai_maturity_score": 1.5,
            "signal_confidence": 0.21
        }
    },
    "candidate_output": "",
    "ground_truth": {
        "required_signal_references": ["low signal", "data analyst", "qualify"],
        "banned_phrases": [
            "ML team", "AI initiative", "doubling your AI", "scale your ML",
            "your machine learning", "hope this finds you well", "leverage", "synergy"
        ],
        "required_elements": ["signal_qualification_step", "no_false_ml_assumption"],
        "tone_markers": ["direct", "evidence-based", "specific", "low-pressure", "competence-signaling"]
    },
    "rubric": {
        "scoring_type": "hybrid",
        "threshold": 0.80,
        "dimensions": [
            {
                "name": "no_false_ml_assumption",
                "weight": 0.40,
                "check_type": "not_contains",
                "description": "Agent must NOT assume PivotPoint is building an ML team from one data analyst posting at 0.21 confidence.",
                "check_value": "ML team|AI initiative|doubling your AI|scale your ML|your machine learning|your AI roadmap|growing AI"
            },
            {
                "name": "qualification_present",
                "weight": 0.40,
                "check_type": "contains",
                "description": "Agent must qualify the prospect before pitching — ask about ML direction or acknowledge weak signal.",
                "check_value": "data analyst|wondering if|are you|qualify|exploring|low signal|unclear|curious whether"
            },
            {
                "name": "tone_judge",
                "weight": 0.20,
                "check_type": "llm_score",
                "description": "LLM judge checks agent does not pitch aggressively on weak signal. Pass = avg >= 4/5.",
                "check_value": ""
            }
        ]
    },
    "metadata": {
        "week10_trace_ids": [],
        "week10_probe_ids": ["P-007", "P-012"],
        "partition": "dev",
        "created_at": "2026-04-28T00:00:00Z",
        "seed": 42
    }
},
{
    "task_id": "TB-HA-0010",
    "source_mode": "hand-authored",
    "difficulty": "adversarial",
    "dimension": "objection-handling",
    "input": {
        "hiring_signal_brief": "Cortex AI Labs posted 6 ML engineer roles 21 days ago. $40M Series B closed 90 days ago.",
        "bench_summary": "Tenacious provides pre-vetted ML engineers on 2-week deployment timelines. Current bench: 5 ML engineers available.",
        "prospect_profile": {
            "company_name": "Cortex AI Labs",
            "company_size": "51-200",
            "segment": "Series B AI",
            "requested_headcount": 6,
            "tech_stack": ["Python", "JAX", "Kubernetes", "Ray"],
            "ai_maturity_score": 4.2,
            "signal_confidence": 0.89
        },
        "prior_thread": "Turn 1 (agent): Referenced Cortex AI ML hiring surge and $40M raise. Offered 5 pre-vetted engineers on 2-week timeline.\n\nTurn 2 (prospect reply): Thanks. We actually just closed 4 offers this week. We are good for now."
    },
    "candidate_output": "",
    "ground_truth": {
        "required_signal_references": ["2 remaining", "future", "pipeline"],
        "banned_phrases": [
            "that is great news", "congratulations", "I understand completely",
            "we understand your concern", "completely understand", "I hear you",
            "hope this finds you well", "synergy", "leverage", "best-in-class"
        ],
        "required_elements": ["acknowledge_objection", "open_future_door", "no_pressure"],
        "tone_markers": ["direct", "evidence-based", "specific", "low-pressure", "competence-signaling"]
    },
    "rubric": {
        "scoring_type": "hybrid",
        "threshold": 0.80,
        "dimensions": [
            {
                "name": "no_generic_acknowledgment",
                "weight": 0.25,
                "check_type": "not_contains",
                "description": "Agent must NOT use hollow validation phrases.",
                "check_value": "that is great news|congratulations on|I understand completely|we understand your concern|completely understand|I hear you"
            },
            {
                "name": "remaining_need_reference",
                "weight": 0.35,
                "check_type": "contains",
                "description": "Prospect filled 4 of 6 roles — 2 still open. Agent should reference remaining headcount or future pipeline.",
                "check_value": "2 remaining|still have|two more|remaining roles|pipeline|future need|future hire|next round"
            },
            {
                "name": "low_pressure_close",
                "weight": 0.25,
                "check_type": "contains",
                "description": "Agent must leave the door open without pressure.",
                "check_value": "when you are ready|no rush|future|next time|keep in touch|happy to reconnect|bench is available"
            },
            {
                "name": "tone_judge",
                "weight": 0.15,
                "check_type": "llm_score",
                "description": "LLM judge verifies low-pressure handling. Pass = avg >= 4/5.",
                "check_value": ""
            }
        ]
    },
    "metadata": {
        "week10_trace_ids": [],
        "week10_probe_ids": ["P-011", "P-010"],
        "partition": "dev",
        "created_at": "2026-04-28T00:00:00Z",
        "seed": 42
    }
}
]

schema_path = "schema.json"
with open(schema_path) as f:
    schema = json.load(f)

out_dir = Path("tenacious_bench_v0.1/dev")
for task in tasks:
    path = out_dir / f"{task['task_id']}.json"
    with open(path, "w") as f:
        json.dump(task, f, indent=2)
    try:
        jsonschema.validate(task, schema)
        print(f"  {task['task_id']}: VALID")
    except jsonschema.ValidationError as e:
        print(f"  {task['task_id']}: INVALID -- {e.message}")

print(f"\nTotal dev tasks: {len(list(out_dir.glob('*.json')))}")
