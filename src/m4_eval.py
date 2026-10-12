from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass, asdict
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS evaluation."""
    from config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL, EMBEDDING_MODEL
    if not (len(questions) == len(answers) == len(contexts) == len(ground_truths)):
        raise ValueError('Evaluation inputs must have equal lengths')
    try:
        if not OPENAI_API_KEY or not questions:
            raise ValueError('Evaluation requires an API key and nonempty input')
        # Nap torch truoc pyarrow/pandas (do ragas/datasets keo vao) de tranh WinError 1114 (c10.dll) tren Windows
        import torch  # noqa: F401
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
        from ragas.embeddings import HuggingfaceEmbeddings
        from ragas.run_config import RunConfig
        from langchain_openai import ChatOpenAI
        from datasets import Dataset
        dataset = Dataset.from_dict({'question': questions, 'answer': answers,
                                     'contexts': contexts, 'ground_truth': ground_truths})
        llm = ChatOpenAI(model=LLM_MODEL, api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL,
                         temperature=0, timeout=90, max_retries=1)
        embeddings = HuggingfaceEmbeddings(model_name=EMBEDDING_MODEL,
                                           encode_kwargs={'batch_size': 8})
        result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                          llm=llm, embeddings=embeddings,
                          run_config=RunConfig(timeout=180, max_retries=2, max_workers=2))
        frame = result.to_pandas()
        rows = [EvalResult(q, a, c, gt, **{m: float(frame.iloc[i][m]) for m in METRICS})
                for i, (q, a, c, gt) in enumerate(zip(questions, answers, contexts, ground_truths))]
        complete = all(math.isfinite(getattr(row, m)) for row in rows for m in METRICS)
        return {**{m: float(frame[m].mean()) for m in METRICS}, 'per_question': rows,
                'status': 'complete' if complete else 'partial', 'requested_questions': len(questions),
                # Model IDs thực sự dùng trong lượt đánh giá (LLM của RAGAS + embedding)
                'metadata': {'evaluator_models': [LLM_MODEL, EMBEDDING_MODEL]}}
    except Exception as exc:
        print(f'RAGAS evaluation unavailable: {type(exc).__name__}: {exc}', flush=True)
        return {**{m: float('nan') for m in METRICS}, 'per_question': [],
                'status': 'failed', 'error': type(exc).__name__, 'requested_questions': len(questions)}


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    tree = {
        'faithfulness': ('Answer may contain unsupported claims', 'Check claims against context; tighten answer prompt'),
        'context_recall': ('Relevant evidence may be missing', 'Inspect missing facts; improve chunking or hybrid retrieval'),
        'context_precision': ('Retrieved context may contain irrelevant evidence', 'Inspect reranking and document versions'),
        'answer_relevancy': ('Answer may not address the question', 'Inspect question and answer; improve prompt'),
    }
    failures = []
    for result in eval_results:
        scores = {m: getattr(result, m) for m in METRICS}
        if not all(math.isfinite(s) for s in scores.values()):
            continue
        worst = min(scores, key=scores.get)
        diagnosis, fix = tree[worst]
        failures.append({'question': result.question, 'answer': result.answer,
                         'ground_truth': result.ground_truth, 'contexts': result.contexts,
                         'worst_metric': worst, 'score': scores[worst],
                         'average_score': sum(scores.values()) / len(scores),
                         'diagnosis': diagnosis, 'suggested_fix': fix})
    return sorted(failures, key=lambda r: r['average_score'])[:max(0, bottom_n)]


METRICS = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    report = {
        "aggregate": {k: results.get(k) for k in METRICS},
        "status": results.get('status', 'unknown'),
        "error": results.get('error'),
        "requested_questions": results.get('requested_questions'),
        "per_question": [asdict(r) for r in results.get('per_question', [])],
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        def clean(value):
            if isinstance(value, float) and not math.isfinite(value):
                return None
            if isinstance(value, dict):
                return {k: clean(v) for k, v in value.items()}
            if isinstance(value, list):
                return [clean(v) for v in value]
            return value
        json.dump(clean(report), f, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
