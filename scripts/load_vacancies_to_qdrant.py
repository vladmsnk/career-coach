#!/usr/bin/env python3
"""
Pipeline для загрузки вакансий в Qdrant на основе vladosy.ipynb
Использование: python scripts/load_vacancies_to_qdrant.py
"""
import asyncio
import os
import pickle
import json
import re
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid5, NAMESPACE_URL
from datetime import datetime

import numpy as np
import pandas as pd
from tenacity import retry, wait_exponential_jitter, stop_after_attempt, retry_if_exception_type
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
import tiktoken

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    VectorParams, Distance, PointStruct, 
    CollectionStatus, OptimizersConfigDiff
)

# ==================== НАСТРОЙКИ ====================
MODEL = "text-embedding-3-small"
DIM = 768  # 1536 максимум; 768 для экономии памяти
CONCURRENCY = 2  # УМЕНЬШЕНО: было 8 → стало 2 для обхода рейт-лимитов
BATCH_SIZE = 25   # УМЕНЬШЕНО: было 128 → стало 25 для обхода рейт-лимитов
DELAY_BETWEEN_BATCHES = 2  # ДОБАВЛЕНО: задержка между батчами в секундах

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "vacancies_tasks"
PICKLE_FILE = "scored_vacs.pickle"

# ==================== EMBEDDING ФУНКЦИИ ====================
enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Подсчитывает количество токенов в тексте."""
    return len(enc.encode(text or ""))

def chunk_by_tokens(text: str, max_tokens: int = 400, overlap: int = 40) -> List[str]:
    """Резка длинных текстов по токенам с перекрытием."""
    ids = enc.encode(text or "")
    if not ids:
        return [""]
    chunks, step = [], max_tokens - overlap
    for i in range(0, len(ids), step):
        sub = ids[i:i+max_tokens]
        if not sub: 
            break
        chunks.append(enc.decode(sub))
    return chunks or [""]

@retry(
    wait=wait_exponential_jitter(initial=2, max=60),  # УВЕЛИЧЕНО: больше задержки при ретраях
    stop=stop_after_attempt(10),  # УВЕЛИЧЕНО: больше попыток
    retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError))
)
async def embed_batch(client: AsyncOpenAI, texts: List[str], *, dimensions: int = DIM) -> np.ndarray:
    """Один батч в Embeddings API с улучшенными ретраями."""
    try:
        resp = await client.embeddings.create(
            model=MODEL,
            input=texts,
            dimensions=dimensions
        )
        vecs = np.array([d.embedding for d in resp.data], dtype=np.float32)
        # L2-нормирование под cosine/IP
        norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
        return vecs / norms
    except RateLimitError as e:
        print(f"⚠️  Рейт-лимит! Подождем дольше... {e}")
        raise
    except Exception as e:
        print(f"❌ Ошибка в embed_batch: {e}")
        raise

async def embed_long_docs(docs: List[str]) -> np.ndarray:
    """Длинные тексты: чанкинг (~400 токенов) + mean-pooling в 1 вектор на документ."""
    if not docs:
        print("⚠️  Пустой список документов!")
        return np.array([]).reshape(0, DIM)
    
    client = AsyncOpenAI()
    sem = asyncio.Semaphore(CONCURRENCY)

    print(f"🔄 Подготовка {len(docs)} документов для эмбеддинга...")
    print(f"🔧 Параметры: CONCURRENCY={CONCURRENCY}, BATCH_SIZE={BATCH_SIZE}, DELAY={DELAY_BETWEEN_BATCHES}s")

    # 1) готовим куски и обратную индексацию
    doc_spans: List[str] = []
    doc_ptrs: List[int] = []  # сколько спанов у i-го документа
    for text in docs:
        spans = chunk_by_tokens(text, max_tokens=400, overlap=40)
        doc_spans.extend(spans)
        doc_ptrs.append(len(spans))

    print(f"📊 Создано {len(doc_spans)} чанков из {len(docs)} документов")

    if not doc_spans:
        print("⚠️  Не удалось создать чанки!")
        return np.array([]).reshape(0, DIM)

    # 2) эмбеддим спаны батчами с задержками
    async def run_batch(start: int, end: int, batch_num: int):
        async with sem:
            # Добавляем дополнительную задержку для каждого батча
            if batch_num > 0:
                delay = DELAY_BETWEEN_BATCHES + (batch_num % 5) * 0.5  # Увеличиваем задержку каждые 5 батчей
                print(f"⏸️  Пауза {delay:.1f}s перед батчем #{batch_num}...")
                await asyncio.sleep(delay)
            
            batch = doc_spans[start:end]
            print(f"🤖 Обрабатываем батч #{batch_num}: {len(batch)} текстов")
            return await embed_batch(client, batch)

    tasks = []
    batch_num = 0
    for i in range(0, len(doc_spans), BATCH_SIZE):
        end_idx = min(i + BATCH_SIZE, len(doc_spans))
        tasks.append(asyncio.create_task(run_batch(i, end_idx, batch_num)))
        batch_num += 1
        
        # Показываем прогресс каждые 5 батчей (уменьшено для лучшего мониторинга)
        if len(tasks) % 5 == 0:
            print(f"⏳ Подготовлено батчей: {len(tasks)}")
    
    print(f"🤖 Отправляем {len(tasks)} батчей в OpenAI API с контролем рейт-лимитов...")
    print(f"⚡ Ожидаемое время: ~{len(tasks) * DELAY_BETWEEN_BATCHES / 60:.1f} минут")
    span_vecs = np.vstack(await asyncio.gather(*tasks))
    print(f"✅ Получены эмбеддинги для {len(span_vecs)} чанков")

    # 3) mean-pooling по документам
    out = np.zeros((len(docs), span_vecs.shape[1]), dtype=np.float32)
    idx = 0
    for doc_id, cnt in enumerate(doc_ptrs):
        if cnt > 0:
            out[doc_id] = span_vecs[idx:idx+cnt].mean(axis=0)
        idx += cnt
    
    # финальная нормализация
    norms = np.linalg.norm(out, axis=1, keepdims=True) + 1e-12
    return out / norms

# ==================== ПАРСИНГ PICKLE ====================
def _extract_json_from_md(s: str) -> Optional[Dict[str, Any]]:
    """В answers_list лежит строка с JSON, часто внутри ``` ... ```."""
    if not isinstance(s, str):
        return None
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", s, flags=re.S)
    payload = m.group(1) if m else s
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        cleaned = payload.replace("\u00a0", " ").strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return None

def _join_tasks(tasks: Any, max_chars: int = 8000) -> str:
    """Склеиваем список задач в одну строку для эмбеддинга."""
    if isinstance(tasks, list):
        parts = [t.strip() for t in tasks if isinstance(t, str) and t.strip()]
        return (". ".join(parts))[:max_chars]
    return ""

def parse_pickle_to_tasks(pickle_path: str) -> pd.DataFrame:
    """Парсит pickle файл в DataFrame с вакансиями."""
    print(f"🔄 Загружаю данные из {pickle_path}...")
    
    if not Path(pickle_path).exists():
        raise FileNotFoundError(f"Файл {pickle_path} не найден. Убедитесь что он находится в корне проекта.")
    
    with open(pickle_path, "rb") as f:
        rows = pickle.load(f)

    print(f"📦 Загружено записей из pickle: {len(rows)}")

    out: List[Dict[str, Any]] = []
    processed = 0
    
    for row in rows:
        processed += 1
        if processed % 1000 == 0:
            print(f"⏳ Обработано записей: {processed}/{len(rows)}")
            
        top_id = row.get("id")
        answers = row.get("answers_list") or []
        parsed: Optional[Dict[str, Any]] = None

        # берём первый валидный JSON из answers_list
        for ans in answers:
            parsed = _extract_json_from_md(ans)
            if isinstance(parsed, dict) and parsed:
                break
        if not parsed:
            continue

        url = parsed.get("url")
        # вытащим hh id из URL (если есть)
        m = re.search(r"/vacancy/(\d+)", url or "")
        hh_id = m.group(1) if m else None

        tasks_list = parsed.get("tasks") or []
        tasks_text = _join_tasks(tasks_list)
        
        # Пропускаем вакансии без описания задач
        if not tasks_text.strip():
            continue

        out.append({
            "id": top_id,
            "hh_id": hh_id,
            "url": url,
            "title": parsed.get("title"),
            "company": parsed.get("company"),
            "location": parsed.get("location"),
            "experience": parsed.get("experience"),
            "employment_type": parsed.get("employment_type"),
            "remote": parsed.get("remote"),
            "posted_at": parsed.get("posted_at"),
            "tasks_list": tasks_list,
            "tasks_text": tasks_text,
            "skills": parsed.get("skills") or [],
            "raw_category": parsed.get("category"),
            "confidence": parsed.get("confidence"),
        })

    df = pd.DataFrame(out)
    # удалим дубликаты id
    if not df.empty:
        df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    
    print(f"✅ Обработано валидных вакансий: {len(df)}")
    return df

# ==================== QDRANT ФУНКЦИИ ====================
def to_qdrant_id(x):
    """Конвертирует ID в формат подходящий для Qdrant."""
    s = str(x)
    if s.isdigit() and len(s) < 19:  # int64 лимит
        return int(s)
    try:
        return UUID(s)
    except Exception:
        return uuid5(NAMESPACE_URL, s)

def to_jsonable(v):
    """Конвертирует значения в JSON-совместимый формат."""
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, (list, tuple, np.ndarray)):
        return [to_jsonable(e) for e in v]
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.isoformat()
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    return v

async def setup_qdrant_collection(client: QdrantClient, collection_name: str, vector_dim: int):
    """Создает или пересоздает коллекцию Qdrant."""
    print(f"🔄 Настройка коллекции {collection_name}...")
    
    # Проверяем существование коллекции
    try:
        collection_info = client.get_collection(collection_name)
        print(f"⚠️ Коллекция {collection_name} уже существует. Пересоздаем...")
        client.delete_collection(collection_name)
    except Exception:
        print(f"ℹ️ Коллекция {collection_name} не существует. Создаем новую...")

    # Создаем коллекцию с оптимизациями
    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "tasks": VectorParams(size=vector_dim, distance=Distance.COSINE)
        },
        optimizers_config=OptimizersConfigDiff(
            default_segment_number=2,
            memmap_threshold=20000
        )
    )
    print(f"✅ Коллекция {collection_name} создана (размерность: {vector_dim})")

async def upload_to_qdrant(
    client: QdrantClient, 
    collection_name: str,
    df: pd.DataFrame,
    embeddings: np.ndarray,
    batch_size: int = 256
):
    """Загружает векторы и метаданные в Qdrant."""
    print(f"🔄 Загрузка {len(df)} вакансий в Qdrant...")
    
    # Подготовка metadata полей
    relevant_cols = ["url", "title", "company", "location", "remote",
                    "employment_type", "experience", "posted_at",
                    "skills", "tasks_list", "raw_category", "confidence",
                    "hh_id"]
    
    points = []
    uploaded = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            # Подготовка payload
            payload = {}
            for col in relevant_cols:
                if col in df.columns:
                    val = row[col]
                    if isinstance(val, np.ndarray):
                        val = val.tolist()
                    payload[col] = to_jsonable(val)
            
            # Создание point
            point_id = to_qdrant_id(row["id"])
            vector = embeddings[idx].tolist()
            
            point = PointStruct(
                id=point_id,
                vector={"tasks": vector},
                payload=payload
            )
            points.append(point)
            
            # Загружаем батчами
            if len(points) >= batch_size:
                client.upsert(collection_name=collection_name, points=points)
                uploaded += len(points)
                print(f"📤 Загружено {uploaded}/{len(df)} вакансий...")
                points.clear()
                
        except Exception as e:
            errors += 1
            print(f"⚠️ Ошибка при обработке вакансии {row.get('id', 'unknown')}: {e}")
            if errors > 100:  # Слишком много ошибок
                print(f"❌ Слишком много ошибок ({errors}). Останавливаем загрузку.")
                break
    
    # Загружаем остаток
    if points:
        client.upsert(collection_name=collection_name, points=points)
        uploaded += len(points)
    
    print(f"✅ Успешно загружено в Qdrant: {uploaded} вакансий")
    if errors > 0:
        print(f"⚠️ Ошибок при загрузке: {errors}")

async def test_search(client: QdrantClient, collection_name: str):
    """Тестирует поиск в созданной коллекции."""
    print(f"\n🔍 Тестирование поиска в коллекции {collection_name}...")
    
    test_queries = [
        "Разработка микросервисов на Python с FastAPI и PostgreSQL",
        "Frontend разработка на React и TypeScript",
        "Java разработчик с опытом Spring Boot",
        "DevOps инженер с Docker и Kubernetes"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Тест {i}: {query}")
        
        # Создаем эмбеддинг запроса
        query_embedding = (await embed_long_docs([query]))[0].tolist()
        
        # Ищем похожие вакансии
        search_results = client.search(
            collection_name=collection_name,
            query_vector=("tasks", query_embedding),
            limit=3,
            with_payload=True
        )
        
        if search_results:
            for j, result in enumerate(search_results, 1):
                payload = result.payload or {}
                title = payload.get('title', 'Без названия')
                company = payload.get('company', 'Без компании')
                category = payload.get('raw_category', 'Без категории')
                print(f"   {j}. {title} | {company} | {category} | Score: {result.score:.3f}")
        else:
            print("   Ничего не найдено")

# ==================== ОСНОВНОЙ PIPELINE ====================
async def main():
    """Основная функция pipeline."""
    start_time = datetime.now()
    print("🚀 ЗАПУСК PIPELINE ЗАГРУЗКИ ВАКАНСИЙ В QDRANT")
    print("=" * 70)
    
    # 1. Проверка окружения
    print("🔧 Проверка окружения...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Не установлена переменная окружения OPENAI_API_KEY")
        print("   Установите её через: export OPENAI_API_KEY='your-key-here'")
        print("   Или создайте файл .env с содержимым: OPENAI_API_KEY=your-key-here")
        return
    else:
        print("✅ OpenAI API ключ найден")
    
    if not Path(PICKLE_FILE).exists():
        print(f"❌ Файл {PICKLE_FILE} не найден в текущей директории")
        print(f"   Скопируйте его в: {Path.cwd() / PICKLE_FILE}")
        return
    else:
        print(f"✅ Файл данных найден: {PICKLE_FILE}")
    
    # 2. Подключение к Qdrant
    print(f"\n🔌 Подключение к Qdrant: {QDRANT_URL}")
    try:
        qdrant_client = QdrantClient(url=QDRANT_URL)
        collections = qdrant_client.get_collections()
        print(f"✅ Qdrant подключен. Существующих коллекций: {len(collections.collections)}")
        
        # Показываем существующие коллекции
        if collections.collections:
            print("   Существующие коллекции:")
            for coll in collections.collections:
                print(f"     • {coll.name}")
    except Exception as e:
        print(f"❌ Ошибка подключения к Qdrant: {e}")
        print("   Убедитесь что Qdrant запущен: docker-compose up -d qdrant")
        return
    
    # 3. Парсинг данных
    print(f"\n📊 Парсинг данных из {PICKLE_FILE}...")
    try:
        df = parse_pickle_to_tasks(PICKLE_FILE)
        if df.empty:
            print("❌ Нет валидных данных для загрузки")
            return
    except Exception as e:
        print(f"❌ Ошибка при парсинге данных: {e}")
        return
    
    print(f"\n📈 Статистика данных:")
    print(f"   Всего вакансий: {len(df):,}")
    print(f"   Уникальных категорий: {df['raw_category'].nunique()}")
    
    # Топ категории
    top_categories = df['raw_category'].value_counts().head(5)
    print(f"   Топ-5 категорий:")
    for cat, count in top_categories.items():
        print(f"     • {cat}: {count:,}")
    
    # Топ компании
    top_companies = df['company'].value_counts().head(5)
    print(f"   Топ-5 компаний:")
    for company, count in top_companies.items():
        if pd.notna(company):
            print(f"     • {company}: {count:,}")
    
    # 4. Создание эмбеддингов
    print(f"\n🤖 Создание эмбеддингов...")
    print(f"   Модель: {MODEL}")
    print(f"   Размерность: {DIM}")
    print(f"   Конкурентность: {CONCURRENCY}")
    print(f"   Размер батча: {BATCH_SIZE}")
    
    texts = df["tasks_text"].astype(str).tolist()
    
    # Подсчет токенов и стоимости
    print(f"\n💰 Анализ стоимости...")
    sample_texts = texts[:100] if len(texts) > 100 else texts
    sample_tokens = [count_tokens(text) for text in sample_texts]
    avg_tokens = sum(sample_tokens) / len(sample_tokens)
    total_tokens = int(avg_tokens * len(texts))
    estimated_cost = (total_tokens / 1_000_000) * 0.02  # $0.02 per 1M tokens для text-embedding-3-small
    
    print(f"   Среднее токенов на вакансию: {avg_tokens:.0f}")
    print(f"   Общее количество токенов: {total_tokens:,}")
    print(f"   Примерная стоимость: ${estimated_cost:.2f}")
    
    # Подтверждение от пользователя (в реальном запуске можно добавить input)
    print(f"\n⚠️  Внимание! Это создаст {len(texts):,} эмбеддингов за ~${estimated_cost:.2f}")
    
    try:
        embeddings = await embed_long_docs(texts)
        print(f"✅ Эмбеддинги созданы успешно: {embeddings.shape}")
    except Exception as e:
        print(f"❌ Ошибка создания эмбеддингов: {e}")
        return
    
    # 5. Настройка коллекции Qdrant
    print(f"\n🗄️ Настройка коллекции Qdrant...")
    try:
        await setup_qdrant_collection(qdrant_client, COLLECTION_NAME, DIM)
    except Exception as e:
        print(f"❌ Ошибка настройки коллекции: {e}")
        return
    
    # 6. Загрузка в Qdrant
    print(f"\n📤 Загрузка данных в Qdrant...")
    try:
        await upload_to_qdrant(qdrant_client, COLLECTION_NAME, df, embeddings)
    except Exception as e:
        print(f"❌ Ошибка загрузки в Qdrant: {e}")
        return
    
    # 7. Получение статистики коллекции
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        points_count = qdrant_client.count(COLLECTION_NAME).count
        print(f"\n📊 Статистика коллекции:")
        print(f"   Название: {COLLECTION_NAME}")
        print(f"   Количество точек: {points_count:,}")
        print(f"   Размерность векторов: {DIM}")
        print(f"   Статус: {collection_info.status}")
    except Exception as e:
        print(f"⚠️ Не удалось получить статистику коллекции: {e}")
    
    # 8. Тест поиска
    try:
        await test_search(qdrant_client, COLLECTION_NAME)
    except Exception as e:
        print(f"⚠️ Ошибка при тестировании поиска: {e}")
    
    # 9. Финальная статистика
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n🎉 PIPELINE ЗАВЕРШЕН УСПЕШНО!")
    print("=" * 70)
    print(f"📈 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   ⏱️ Время выполнения: {duration:.1f} секунд ({duration/60:.1f} минут)")
    print(f"   📊 Обработано вакансий: {len(df):,}")
    print(f"   🤖 Создано эмбеддингов: {len(embeddings):,}")
    print(f"   🗄️ Коллекция Qdrant: {COLLECTION_NAME}")
    print(f"   🌐 URL Qdrant Dashboard: http://localhost:6333/dashboard")
    print(f"   🔍 URL Qdrant API: {QDRANT_URL}")
    
    print(f"\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
    print(f"   1. Откройте Qdrant Dashboard: http://localhost:6333/dashboard")
    print(f"   2. Проверьте коллекцию '{COLLECTION_NAME}'")
    print(f"   3. Интегрируйте поиск в ваше приложение")
    
    print(f"\n✅ Готово! Векторная база с вакансиями создана и готова к использованию.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n⚠️ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
