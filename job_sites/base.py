from abc import ABC, abstractmethod
from helpers.logger import LoggerHelper

logger = LoggerHelper.get_logger(__name__, prefix='jobsite')

class BaseJobSite(ABC):
    @abstractmethod
    def search_jobs(self, keyword, location=None, extra_params=None):
        pass