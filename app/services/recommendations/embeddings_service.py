"""
Сервис для создания эмбеддингов с использованием OpenAI API.
Адаптирован из scripts/load_vacancies_to_qdrant.py
"""
import asyncio
import os
from typing import List, Optional
import numpy as np
import tiktoken
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from tenacity import retry, wait_exponential_jitter, stop_after_attempt, retry_if_exception_type
from app.core.settings import settings


class EmbeddingsService:
    """Сервис для создания эмбеддингов текста."""
    
    def __init__(self, model: str = "text-embedding-3-small", dimensions: int = 768):
        self.model = model
        self.dimensions = dimensions
        # Используем API ключ из настроек приложения или переменной окружения
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API ключ не найден в настройках или переменных окружения")
        self.client = AsyncOpenAI(api_key=api_key)
        self.enc = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Подсчитывает количество токенов в тексте."""
        return len(self.enc.encode(text or ""))
    
    def chunk_by_tokens(self, text: str, max_tokens: int = 400, overlap: int = 40) -> List[str]:
        """Резка длинных текстов по токенам с перекрытием."""
        ids = self.enc.encode(text or "")
        if not ids:
            return [""]
        chunks, step = [], max_tokens - overlap
        for i in range(0, len(ids), step):
            sub = ids[i:i+max_tokens]
            if not sub: 
                break
            chunks.append(self.enc.decode(sub))
        return chunks or [""]
    
    @retry(
        wait=wait_exponential_jitter(initial=2, max=30),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError))
    )
    async def _create_embedding_batch(self, texts: List[str]) -> np.ndarray:
        """Создает эмбеддинги для списка текстов с ретраями."""
        try:
            resp = await self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions
            )
            vecs = np.array([d.embedding for d in resp.data], dtype=np.float32)
            # L2-нормирование для косинусного расстояния
            norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
            return vecs / norms
        except Exception as e:
            print(f"❌ Ошибка создания эмбеддинга: {e}")
            raise
    
    async def create_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Создает эмбеддинг для одного текста.
        Возвращает нормализованный вектор или None при ошибке.
        """
        if not text or not text.strip():
            print("⚠️ Пустой текст для эмбеддинга")
            return None
        
        try:
            # Для коротких текстов используем напрямую
            if self.count_tokens(text) <= 400:
                embeddings = await self._create_embedding_batch([text])
                return embeddings[0]
            
            # Для длинных текстов - чанкинг и mean pooling
            chunks = self.chunk_by_tokens(text, max_tokens=400, overlap=40)
            if not chunks:
                return None
            
            chunk_embeddings = await self._create_embedding_batch(chunks)
            
            # Mean pooling по всем чанкам
            mean_embedding = chunk_embeddings.mean(axis=0)
            
            # Финальная нормализация
            norm = np.linalg.norm(mean_embedding) + 1e-12
            return mean_embedding / norm
        
        except Exception as e:
            print(f"❌ Не удалось создать эмбеддинг: {e}")
            return None
    
    async def create_embeddings_batch(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """Создает эмбеддинги для списка текстов."""
        results = []
        for text in texts:
            embedding = await self.create_embedding(text)
            results.append(embedding)
        return results
