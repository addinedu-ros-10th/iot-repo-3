"""
LMS (Logistic Management System) Package

물류 관리 시스템의 핵심 로직을 담당하는 패키지입니다.
TCP 명세서에 따라 재고 관리 및 물품 이동을 처리합니다.
"""

__version__ = "1.0.0"
__author__ = "LMS Development Team"

from .core.lms_server import LMSServer
from .data.inventory_manager import InventoryManager

__all__ = ['LMSServer', 'InventoryManager']