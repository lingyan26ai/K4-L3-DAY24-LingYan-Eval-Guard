from __future__ import annotations

"""Phase A: RAGAS Production Evaluation — 50q, 3 distributions, cluster analysis."""

import json
import math
import os
import sys
from dataclasses import asdict, dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH, ANSWERS_PATH, ARTIFACTS_DIR
from src.experiment_support import write_json

Distribution = str  # "factual" | "multi_hop" | "adversarial"

DIAGNOSTIC_TREE = {
    "faithfulness":      ("LLM hallucinating", "Tighten system prompt, lower temperature"),
    "context_recall":    ("Missing relevant chunks", "Improve chunking or add BM25"),
    "context_precision": ("Too many irrelevant chunks", "Add reranking or metadata filter"),
    "answer_relevancy":  ("Answer doesn't match question", "Improve prompt template"),
}


@dataclass
class RagasResult:
    question_id: int
    distribution: Distribution
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float

    @property
    def avg_score(self) -> float:
        return (self.faithfulness + self.answer_relevancy +
                self.context_precision + self.context_recall) / 4

    @property
    def worst_metric(self) -> str:
        scores = {
            "faithfulness":      self.faithfulness,
            "answer_relevancy":  self.answer_relevancy,
            "context_precision": self.context_precision,
            "context_recall":    self.context_recall,
        }
        return min(scores, key=scores.get)


# ─── Đã implement sẵn ────────────────────────────────────────────────────────

@dataclass
class RagasEvaluation:
    """Task 2 output: measured rows plus model identifiers reported by m4."""
    results: list[RagasResult]
    evaluator_models: list[str]

def load_test_set_50q(path: str = TEST_SET_PATH) -> list[dict]:
    """Load 50q test set với 3 distributions."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_answers(path: str = ANSWERS_PATH) -> list[dict]:
    """Load pre-generated answers từ setup_answers.py."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"answers_50q.json không tìm thấy tại {path}\n"
            "→ Chạy trước: python scripts/setup_answers.py --live"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_phase_a_report(results: list[RagasResult], clusters: dict, bottom: list[dict]) -> dict:
    """Provided exporter: preserve the student-produced Task 3 rows verbatim."""
    per_dist: dict[str, dict] = {}
    for dist in ["factual", "multi_hop", "adversarial"]:
        subset = [r for r in results if r.distribution == dist]
        if subset:
            per_dist[dist] = {
                "count": len(subset),
                "faithfulness":      sum(r.faithfulness for r in subset) / len(subset),
                "answer_relevancy":  sum(r.answer_relevancy for r in subset) / len(subset),
                "context_precision": sum(r.context_precision for r in subset) / len(subset),
                "context_recall":    sum(r.context_recall for r in subset) / len(subset),
                "avg_score":         sum(r.avg_score for r in subset) / len(subset),
            }

    report = {
        "total_questions": len(results),
        "per_question": [asdict(r) for r in results],
        "per_distribution": per_dist,
        "failure_clusters": clusters,
        "bottom_10": bottom,
    }
    return report


def save_phase_a_report(results: list[RagasResult], clusters: dict, bottom: list[dict],
                        path: str = os.path.join(ARTIFACTS_DIR, "ragas_50q.json")) -> None:
    write_json(path, build_phase_a_report(results, clusters, bottom))



# ─── Tasks 1-4: Sinh viên implement ──────────────────────────────────────────

DISTRIBUTIONS = ("factual", "multi_hop", "adversarial")
METRICS = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")

# Ghi chú bổ sung theo distribution để diagnosis cụ thể hơn cây chẩn đoán chung.
_DIST_NOTES = {
    "factual": "câu factual một nguồn — lỗi thường do chunk chứa con số bị cắt hoặc rerank sai",
    "multi_hop": "câu multi-hop cần ghép nhiều tài liệu — top_k nhỏ dễ thiếu một vế",
    "adversarial": "câu bẫy (policy cũ/mới, điều kiện phủ định) — dễ lấy nhầm phiên bản cũ",
}


def group_by_distribution(test_set: list[dict]) -> dict[str, list[dict]]:
    """Task 1: Nhóm 50 câu hỏi theo 3 distributions.

    Returns:
        {"factual": [...], "multi_hop": [...], "adversarial": [...]}
    """
    groups: dict[str, list[dict]] = {d: [] for d in DISTRIBUTIONS}
    for item in test_set:
        dist = item.get("distribution")
        if dist not in groups:
            raise ValueError(f"Câu {item.get('id')}: distribution không hợp lệ: {dist!r}")
        groups[dist].append(item)
    return groups


def _metric_value(record, name: str) -> float:
    """Đọc metric từ object (thuộc tính) hoặc dict; ép về float Python hữu hạn trong [0,1]."""
    if isinstance(record, dict):
        value = record[name]
    else:
        value = getattr(record, name)
    value = float(value)  # chuyển scalar NumPy/Pandas về float Python
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"Metric {name}={value!r} không hữu hạn hoặc ngoài [0,1]; "
                         "không thay NaN bằng điểm giả — kiểm tra lại m4.")
    return value


def run_ragas_50q(answers: list[dict]) -> RagasEvaluation:
    """Task 2: Chạy RAGAS 4 metrics trên toàn bộ 50 câu hỏi qua m4.evaluate_ragas."""
    try:
        from src.m4_eval import evaluate_ragas
    except ImportError as exc:
        raise ValueError("Thiếu src/m4_eval.py — copy module m4 từ bài RAG trước; "
                         "không thể khai evaluator models thực tế.") from exc

    if not answers:
        raise ValueError("answers rỗng — chạy scripts/setup_answers.py --live trước.")

    questions = [a["question"] for a in answers]
    ans_texts = [a["answer"] for a in answers]
    contexts = [list(a["contexts"]) for a in answers]
    ground_truths = [a["ground_truth"] for a in answers]

    raw = evaluate_ragas(questions, ans_texts, contexts, ground_truths)
    per_q = list(raw.get("per_question", []))
    if len(per_q) != len(answers):
        raise ValueError(f"m4 trả {len(per_q)} kết quả cho {len(answers)} câu — "
                         "không zip lệch thứ tự.")

    metadata = raw.get("metadata") or {}
    evaluator_models = list(metadata.get("evaluator_models") or [])
    if not evaluator_models or not all(isinstance(m, str) and m.strip() for m in evaluator_models):
        raise ValueError("m4 phải trả metadata.evaluator_models (model IDs thực tế); "
                         "không dùng JUDGE_MODEL để điền thay.")

    results: list[RagasResult] = []
    for a, pq in zip(answers, per_q):
        results.append(RagasResult(
            question_id=a["id"],
            distribution=a["distribution"],
            question=a["question"],
            answer=a["answer"],
            contexts=a["contexts"],
            ground_truth=a["ground_truth"],
            faithfulness=_metric_value(pq, "faithfulness"),
            answer_relevancy=_metric_value(pq, "answer_relevancy"),
            context_precision=_metric_value(pq, "context_precision"),
            context_recall=_metric_value(pq, "context_recall"),
        ))
    return RagasEvaluation(results, evaluator_models)


def bottom_10(results: list[RagasResult]) -> list[dict]:
    """Task 3: Lấy 10 câu hỏi có avg_score thấp nhất (tăng dần), kèm diagnosis/fix."""
    # Sort ổn định theo (avg_score, question_id) để kết quả tái lập được khi hoà điểm.
    ranked = sorted(results, key=lambda r: (r.avg_score, r.question_id))[:10]
    output = []
    for rank, r in enumerate(ranked, 1):
        diag, fix = DIAGNOSTIC_TREE[r.worst_metric]
        worst_value = getattr(r, r.worst_metric)
        output.append({
            "rank": rank,
            "question_id": r.question_id,
            "distribution": r.distribution,
            "question": r.question,
            "avg_score": r.avg_score,
            "worst_metric": r.worst_metric,
            "diagnosis": (f"{diag} ({r.worst_metric}={worst_value:.2f}); "
                          f"{_DIST_NOTES.get(r.distribution, r.distribution)}"),
            "suggested_fix": fix,
        })
    return output


def cluster_analysis(results: list[RagasResult]) -> dict:
    """Task 4: Matrix worst_metric × distribution và nhóm yếu nhất theo mean avg_score."""
    matrix = {m: {d: 0 for d in DISTRIBUTIONS} for m in METRICS}
    for r in results:
        matrix[r.worst_metric][r.distribution] += 1

    # Nhóm rỗng bị bỏ khỏi phép chia (không gán 0 điểm cho nhóm không có dữ liệu).
    means: dict[str, float] = {}
    for d in DISTRIBUTIONS:
        subset = [r.avg_score for r in results if r.distribution == d]
        if subset:
            means[d] = sum(subset) / len(subset)
    if not means:
        raise ValueError("Không có kết quả để phân tích cluster.")

    dominant_dist = min(means, key=means.get)          # chất lượng thấp nhất, không phải nhóm lớn nhất
    totals = {m: sum(matrix[m].values()) for m in METRICS}
    dominant_metric = max(METRICS, key=lambda m: totals[m])
    in_weakest = {m: matrix[m][dominant_dist] for m in METRICS}
    weakest_metric_in_dist = max(METRICS, key=lambda m: in_weakest[m])

    mean_txt = ", ".join(f"{d}={v:.3f}" for d, v in means.items())
    insight = (
        f"Điểm trung bình theo nhóm: {mean_txt}. Nhóm yếu nhất là '{dominant_dist}' "
        f"(mean avg_score thấp nhất, không phải nhóm đông nhất). "
        f"Trên toàn bộ {len(results)} câu, '{dominant_metric}' là metric thấp nhất ở "
        f"{totals[dominant_metric]} câu → chẩn đoán: {DIAGNOSTIC_TREE[dominant_metric][0]}; "
        f"hướng sửa: {DIAGNOSTIC_TREE[dominant_metric][1]}. "
        f"Trong nhóm '{dominant_dist}', metric thấp nhất phổ biến là "
        f"'{weakest_metric_in_dist}' ({in_weakest[weakest_metric_in_dist]} câu). "
        "Matrix chỉ đếm worst_metric của mọi câu, cần đọc question/answer/contexts "
        "của bottom 10 trước khi kết luận nguyên nhân."
    )
    result = {
        "matrix": matrix,
        "dominant_failure_distribution": dominant_dist,
        "dominant_failure_metric": dominant_metric,
        "insight": insight,
    }
    if len(means) == len(DISTRIBUTIONS):
        result["distribution_avg_scores"] = means
    return result


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "a", *sys.argv[1:]]))
