"""M5: one JSON call per chunk with an extractive fallback."""
from __future__ import annotations
import json
import re
import os, sys
from dataclasses import dataclass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL

@dataclass
class EnrichedChunk:
    original_text: str
    enriched_text: str
    summary: str
    hypothesis_questions: list[str]
    auto_metadata: dict
    method: str


def _enrich_single_call(text: str, source: str) -> dict:
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if s.strip()]
    fallback = {'summary': ' '.join(sentences[:2]), 'questions': [],
                'context': f'Trích từ tài liệu {source}.' if source else 'Trích đoạn tài liệu.',
                'metadata': {'enrichment_status': 'fallback'}}
    if not OPENAI_API_KEY:
        return fallback
    try:
        from openai import OpenAI
        response = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL,
                          timeout=60, max_retries=1).chat.completions.create(
            model=LLM_MODEL, temperature=0, max_tokens=500,
            response_format={'type': 'json_object'},
            messages=[
                {'role': 'system', 'content': 'Phân tích đoạn văn, không thêm dữ kiện ngoài tài liệu. '
                 'Trả về JSON: {"summary":"tóm tắt ngắn hơn đoạn gốc", '
                 '"questions":["3 câu hỏi mà đoạn này trả lời được"], '
                 '"context":"1 câu giới thiệu vị trí/chủ đề đoạn văn", '
                 '"metadata":{"topic":"...","entities":[],"category":"policy|hr|it|finance","language":"vi|en"}}'},
                {'role': 'user', 'content': f'Tài liệu: {source}\n\n{text}'}])
        result = json.loads(response.choices[0].message.content)
        if not isinstance(result, dict) or not all(isinstance(result.get(k), str) for k in ['summary', 'context']):
            raise ValueError('Invalid enrichment strings')
        if not isinstance(result.get('questions'), list) or not all(isinstance(q, str) for q in result['questions']):
            raise ValueError('Invalid enrichment questions')
        if not isinstance(result.get('metadata'), dict):
            raise ValueError('Invalid enrichment metadata')
        result['metadata']['enrichment_status'] = 'llm'
        return result
    except Exception as exc:
        print(f'Enrichment fallback: {type(exc).__name__}', flush=True)
        return fallback


def summarize_chunk(text: str) -> str:
    return _enrich_single_call(text, '')['summary']


def generate_hypothesis_questions(text: str, n_questions: int = 3) -> list[str]:
    return _enrich_single_call(text, '')['questions'][:max(0, n_questions)]


def contextual_prepend(text: str, document_title: str = '') -> str:
    context = _enrich_single_call(text, document_title)['context']
    return f'{context}\n\n{text}' if context else text


def extract_metadata(text: str) -> dict:
    return _enrich_single_call(text, '')['metadata']


def enrich_chunks(chunks: list[dict], methods: list[str] | None = None) -> list[EnrichedChunk]:
    methods = ['combined'] if methods is None else methods
    if set(methods) - {'combined', 'summary', 'hyqa', 'contextual', 'metadata'}:
        raise ValueError('Unknown enrichment method')
    enriched = []
    for i, chunk in enumerate(chunks):
        text, metadata = chunk['text'], chunk.get('metadata', {})
        source = metadata.get('source', '')
        if 'combined' in methods:
            result = _enrich_single_call(text, source)
            summary, questions, auto = result['summary'], result['questions'], result['metadata']
            enriched_text = f"{result['context']}\n\n{text}"
        else:
            summary = summarize_chunk(text) if 'summary' in methods else ''
            questions = generate_hypothesis_questions(text) if 'hyqa' in methods else []
            auto = extract_metadata(text) if 'metadata' in methods else {}
            enriched_text = contextual_prepend(text, source) if 'contextual' in methods else text
        # Generated text helps retrieval; answers use the original parent.
        if summary:
            enriched_text += '\n\nTóm tắt: ' + summary
        if questions:
            enriched_text += '\n\nCâu hỏi: ' + '\n'.join(questions)
        enriched.append(EnrichedChunk(text, enriched_text, summary, questions,
                                      {**auto, **metadata}, '+'.join(methods)))
        if (i + 1) % 10 == 0 or i + 1 == len(chunks):
            print(f'  Enriched {i + 1}/{len(chunks)} chunks...', flush=True)
    return enriched
