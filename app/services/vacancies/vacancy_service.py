"""
Сервис для работы с данными вакансий из CSV файла
"""
import csv
import os
from typing import Dict, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class VacancyData:
    """Данные вакансии из CSV"""
    id: str
    title: str
    company: str
    job_description: str
    meta_summary: str
    url: str
    date_posted: str
    valid_through: str
    employment_type: str
    job_location_type: str
    address_locality: str
    country: str

class VacancyService:
    """Сервис для загрузки и работы с вакансиями из CSV файла"""
    
    def __init__(self, csv_file_path: str = "vacancies_sample.csv"):
        self.csv_file_path = csv_file_path
        self._vacancies: Dict[str, VacancyData] = {}
        self._loaded = False
    
    def load_vacancies(self) -> None:
        """Загружает данные вакансий из CSV файла в память"""
        if self._loaded:
            logger.info("Вакансии уже загружены в память")
            return
            
        if not os.path.exists(self.csv_file_path):
            logger.error(f"CSV файл не найден: {self.csv_file_path}")
            return
            
        logger.info(f"Загрузка вакансий из {self.csv_file_path}")
        loaded_count = 0
        
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    # Пропускаем строки без ID (возможно пустые)
                    vacancy_id = row.get('id', '').strip()
                    if not vacancy_id:
                        continue
                        
                    vacancy = VacancyData(
                        id=vacancy_id,
                        title=row.get('title', '').strip(),
                        company=row.get('company', '').strip(),
                        job_description=row.get('job_description', '').strip(),
                        meta_summary=row.get('meta_summary', '').strip(),
                        url=row.get('url', '').strip(),
                        date_posted=row.get('datePosted', '').strip(),
                        valid_through=row.get('validThrough', '').strip(),
                        employment_type=row.get('employmentType', '').strip(),
                        job_location_type=row.get('jobLocationType', '').strip(),
                        address_locality=row.get('addressLocality', '').strip(),
                        country=row.get('country', '').strip()
                    )
                    
                    self._vacancies[vacancy_id] = vacancy
                    loaded_count += 1
                    
                    # Логируем прогресс каждые 1000 записей
                    if loaded_count % 1000 == 0:
                        logger.info(f"Загружено {loaded_count} вакансий...")
                        
            self._loaded = True
            logger.info(f"✅ Загружено {loaded_count} вакансий из CSV файла")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки CSV файла: {e}")
            raise
    
    def get_vacancy_by_id(self, vacancy_id: str) -> Optional[VacancyData]:
        """Получает данные вакансии по ID"""
        if not self._loaded:
            self.load_vacancies()
        
        return self._vacancies.get(vacancy_id)
    
    def get_vacancies_by_ids(self, vacancy_ids: List[str]) -> List[VacancyData]:
        """Получает список вакансий по списку ID"""
        if not self._loaded:
            self.load_vacancies()
            
        vacancies = []
        for vacancy_id in vacancy_ids:
            vacancy = self._vacancies.get(vacancy_id)
            if vacancy:
                vacancies.append(vacancy)
            else:
                logger.warning(f"Вакансия с ID {vacancy_id} не найдена в CSV")
                
        return vacancies
    
    def get_vacancy_descriptions(self, vacancy_ids: List[str]) -> Dict[str, str]:
        """Получает словарь {vacancy_id: job_description} для списка ID"""
        vacancies = self.get_vacancies_by_ids(vacancy_ids)
        return {
            v.id: v.job_description 
            for v in vacancies 
            if v.job_description.strip()
        }
    
    def get_total_count(self) -> int:
        """Возвращает общее количество загруженных вакансий"""
        if not self._loaded:
            self.load_vacancies()
        return len(self._vacancies)
    
    def is_loaded(self) -> bool:
        """Проверяет, загружены ли данные"""
        return self._loaded

# Создаем глобальный экземпляр сервиса (singleton)
vacancy_service = VacancyService()

