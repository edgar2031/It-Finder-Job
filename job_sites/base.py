from abc import ABC, abstractmethod
from logger import Logger

logger = Logger.get_logger(__name__, file_prefix='jobsite')

class JobSite(ABC):
    @abstractmethod
    def search_jobs(self, keyword, location=None, extra_params=None):
        pass