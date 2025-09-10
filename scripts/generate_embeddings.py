#!/usr/bin/env python3
"""
Скрипт для генерации эмбеддингов из вакансий и сохранения в файл.
Использование: python scripts/generate_embeddings.py
"""
import asyncio
import os
import pickle
import json
import re
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import numpy as np
import pandas as pd
from tenacity import retry, wait_exponential_jitter, stop_after_attempt, retry_if_exception_type
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
import tiktoken

# ==================== НАСТРОЙКИ ====================
MODEL = "text-embedding-3-small"
DIM = 768  # 1536 максимум; 768 для экономии памяти
CONCURRENCY = 2  # УМЕНЬШЕНО для обхода рейт-лимитов
BATCH_SIZE = 25   # УМЕНЬШЕНО для обхода рейт-лимитов
DELAY_BETWEEN_BATCHES = 2  # задержка между батчами в секундах

PICKLE_FILE = "scored_vacs.pickle"
OUTPUT_FILE = "vacancies_with_embeddings.pickle"

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
    wait=wait_exponential_jitter(initial=2, max=60),
    stop=stop_after_attempt(10),
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

    print(f"📊 Всего спанов: {len(doc_spans)}")
    
    if not doc_spans:
        print("⚠️  Нет спанов для обработки!")
        return np.array([]).reshape(0, DIM)

    # 2) батчинг спанов
    async def run_batch(start: int, end: int, batch_num: int):
        async with sem:
            if batch_num > 0:
                await asyncio.sleep(DELAY_BETWEEN_BATCHES)
            batch_texts = doc_spans[start:end]
            print(f"   🔄 Батч {batch_num + 1}: обрабатываем спаны {start}-{end} ({len(batch_texts)} элементов)")
            return await embed_batch(client, batch_texts)

    # Создаем задачи для батчей
    tasks = []
    for batch_num, start in enumerate(range(0, len(doc_spans), BATCH_SIZE)):
        end = min(start + BATCH_SIZE, len(doc_spans))
        tasks.append(run_batch(start, end, batch_num))

    # Выполняем батчи с ограничением concurrency
    print(f"🚀 Запускаем {len(tasks)} батчей...")
    try:
        span_vecs_list = await asyncio.gather(*tasks)
        span_vecs = np.vstack(span_vecs_list)
        print(f"✅ Получили эмбеддинги для всех спанов: {span_vecs.shape}")
    except Exception as e:
        print(f"❌ Ошибка при обработке батчей: {e}")
        raise

    # 3) собираем спаны обратно в документы (mean-pooling)
    doc_vecs = []
    ptr = 0
    for num_spans in doc_ptrs:
        if num_spans == 0:
            print("⚠️  Документ без спанов, используем нулевой вектор")
            doc_vecs.append(np.zeros(DIM, dtype=np.float32))
        else:
            chunk_embeddings = span_vecs[ptr:ptr+num_spans]
            pooled = chunk_embeddings.mean(axis=0)
            doc_vecs.append(pooled)
        ptr += num_spans

    result = np.array(doc_vecs, dtype=np.float32)
    print(f"✅ Итоговые эмбеддинги документов: {result.shape}")
    return result

def parse_vacancy_from_answers(answers_list) -> Dict[str, Any]:
    """Парсит данные вакансии из answers_list."""
    try:
        if not answers_list or len(answers_list) == 0:
            return {}
        
        # Берем первый ответ (обычно там вакансия)
        answer = answers_list[0]
        if not isinstance(answer, str):
            return {}
        
        # Убираем markdown разметку и парсим JSON
        clean_answer = answer.strip()
        if clean_answer.startswith('```'):
            lines = clean_answer.split('\n')
            # Ищем JSON между ```
            json_start = None
            json_end = None
            for i, line in enumerate(lines):
                if line.strip() == '{':
                    json_start = i
                elif line.strip() == '```' and json_start is not None:
                    json_end = i
                    break
            
            if json_start is not None and json_end is not None:
                json_str = '\n'.join(lines[json_start:json_end])
                return json.loads(json_str)
        
        return {}
    
    except Exception as e:
        return {}

def prepare_task_text(row) -> str:
    """Подготавливает текст задач для эмбеддинга."""
    try:
        # Парсим вакансию из answers_list
        vacancy_data = parse_vacancy_from_answers(row.get('answers_list', []))
        
        if not vacancy_data:
            return ""
        
        tasks = vacancy_data.get('tasks', [])
        if not tasks:
            return ""
            
        # Если tasks это список, объединяем в текст
        if isinstance(tasks, list):
            return " ".join(str(task).strip() for task in tasks if str(task).strip())
        else:
            return str(tasks).strip()
    
    except Exception as e:
        print(f"⚠️  Ошибка обработки задач: {e}")
        return ""

def expand_vacancy_data(df: pd.DataFrame) -> pd.DataFrame:
    """Расширяет DataFrame, парся данные из answers_list."""
    print(f"🔄 Парсим данные вакансий из answers_list...")
    
    expanded_rows = []
    for _, row in df.iterrows():
        vacancy_data = parse_vacancy_from_answers(row.get('answers_list', []))
        
        if vacancy_data:
            # Объединяем исходные данные с распарсенными
            expanded_row = {
                'id': row.get('id'),
                'hh_id': str(vacancy_data.get('url', '').split('/')[-1]) if vacancy_data.get('url') else str(row.get('id', '')),
                'answers_list': row.get('answers_list'),
                'dialog': row.get('dialog'),
                **vacancy_data  # Добавляем все поля из vacancy_data
            }
            expanded_rows.append(expanded_row)
        else:
            print(f"⚠️  Не удалось распарсить vacancy для ID {row.get('id')}")
    
    expanded_df = pd.DataFrame(expanded_rows)
    print(f"✅ Распарсено {len(expanded_df)} вакансий")
    return expanded_df

def clean_and_validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """Очищает и валидирует данные перед обработкой."""
    print(f"📊 Исходное количество записей: {len(df)}")
    print(f"📋 Колонки в данных: {list(df.columns)}")
    
    # Сначала расширяем данные, парся answers_list
    df = expand_vacancy_data(df)
    
    # Убираем дубликаты по hh_id или id
    initial_len = len(df)
    if 'hh_id' in df.columns:
        df = df.drop_duplicates(subset=['hh_id'], keep='first').reset_index(drop=True)
        if len(df) < initial_len:
            print(f"🔄 Удалено {initial_len - len(df)} дубликатов по hh_id")
    elif 'id' in df.columns:
        df = df.drop_duplicates(subset=['id'], keep='first').reset_index(drop=True)
        if len(df) < initial_len:
            print(f"🔄 Удалено {initial_len - len(df)} дубликатов по id")
    
    # Подготавливаем тексты задач
    print("🔄 Подготавливаем тексты задач...")
    df['tasks_text'] = df.apply(prepare_task_text, axis=1)
    
    # Фильтруем записи с пустыми задачами
    df_with_tasks = df[df['tasks_text'].str.len() > 0].reset_index(drop=True)
    
    removed_count = len(df) - len(df_with_tasks)
    if removed_count > 0:
        print(f"🔄 Удалено {removed_count} записей без задач")
    
    print(f"✅ Итоговое количество записей для эмбеддинга: {len(df_with_tasks)}")
    return df_with_tasks

async def main():
    """Основная функция для генерации эмбеддингов."""
    print("🚀 ГЕНЕРАЦИЯ ЭМБЕДДИНГОВ ДЛЯ ВАКАНСИЙ")
    print("=" * 50)
    
    # Проверяем наличие входного файла
    if not Path(PICKLE_FILE).exists():
        print(f"❌ Файл {PICKLE_FILE} не найден!")
        print("💡 Убедитесь, что файл scored_vacs.pickle находится в корне проекта")
        return
    
    # Проверяем OpenAI API ключ
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OpenAI API ключ не найден!")
        print("💡 Установите переменную окружения: export OPENAI_API_KEY='your-key'")
        return
    
    # Загружаем данные
    print(f"📂 Загружаем данные из {PICKLE_FILE}...")
    try:
        with open(PICKLE_FILE, "rb") as f:
            data = pickle.load(f)
        
        # Проверяем тип данных и конвертируем в DataFrame если нужно
        if isinstance(data, list):
            print(f"📋 Конвертируем список в DataFrame...")
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            print(f"❌ Неожиданный тип данных: {type(data)}")
            return
            
        print(f"✅ Загружено {len(df)} записей")
    except Exception as e:
        print(f"❌ Ошибка загрузки файла: {e}")
        return
    
    # Очищаем и валидируем данные
    df = clean_and_validate_data(df)
    
    if len(df) == 0:
        print("❌ Нет данных для обработки!")
        return
    
    # Подготавливаем тексты для эмбеддинга
    print("🔄 Подготавливаем тексты для эмбеддинга...")
    texts = df['tasks_text'].tolist()
    
    # Считаем токены и стоимость
    total_tokens = sum(count_tokens(text) for text in texts)
    estimated_cost = (total_tokens / 1_000_000) * 0.02  # $0.02 per 1M tokens
    
    print(f"📊 Статистика:")
    print(f"   📄 Документов: {len(texts):,}")
    print(f"   🔤 Токенов: {total_tokens:,}")
    print(f"   💰 Примерная стоимость: ${estimated_cost:.2f}")
    print(f"   🤖 Модель: {MODEL}")
    print(f"   📐 Размерность: {DIM}")
    
    # Спрашиваем подтверждение
    confirmation = input(f"\n❓ Продолжить генерацию эмбеддингов? (y/N): ").strip().lower()
    if confirmation not in ['y', 'yes']:
        print("⛔ Операция отменена")
        return
    
    # Генерируем эмбеддинги
    print("\n🔄 Генерируем эмбеддинги...")
    start_time = datetime.now()
    
    try:
        embeddings = await embed_long_docs(texts)
        print(f"✅ Эмбеддинги созданы успешно: {embeddings.shape}")
    except Exception as e:
        print(f"❌ Ошибка создания эмбеддингов: {e}")
        return
    
    # Добавляем эмбеддинги к данным
    print("💾 Сохраняем результат...")
    
    # Создаем результирующую структуру
    result_data = {
        'dataframe': df,
        'embeddings': embeddings,
        'metadata': {
            'model': MODEL,
            'dimensions': DIM,
            'created_at': datetime.now().isoformat(),
            'total_records': len(df),
            'total_tokens': total_tokens,
            'estimated_cost': estimated_cost
        }
    }
    
    # Сохраняем в файл
    try:
        with open(OUTPUT_FILE, "wb") as f:
            pickle.dump(result_data, f)
        print(f"✅ Результат сохранен в {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return
    
    # Статистика
    duration = datetime.now() - start_time
    print(f"\n🎉 ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
    print(f"   ⏱️ Время выполнения: {duration}")
    print(f"   📊 Обработано вакансий: {len(df):,}")
    print(f"   🤖 Создано эмбеддингов: {len(embeddings):,}")
    print(f"   💾 Выходной файл: {OUTPUT_FILE}")
    print(f"   📏 Размер файла: {Path(OUTPUT_FILE).stat().st_size / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    asyncio.run(main())
