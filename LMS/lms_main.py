#!/usr/bin/env python3
"""
LMS 시스템의 실행 진입점입니다.
- LMS 서버: 비즈니스 로직 처리
"""

import sys
import threading
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from LMS.core.lms_server import LMSServer

def run_lms_server():
    """LMS 서버를 별도 스레드에서 실행"""
    print("🚀 LMS 서버 시작 중...")
    server = LMSServer(host='localhost', port=9999)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n⌨️ LMS 서버 중단 요청")
        server.stop()
    except Exception as e:
        print(f"❌ LMS 서버 오류: {e}")
        server.stop()

def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("🏢 물류 센터 관리 시스템")
    print("=" * 70)
    print()
    print("시스템 구성:")
    print("  🖥️  GUI: 데이터 표시 전용 (TCP 클라이언트)")
    print("  🏗️  LMS: 비즈니스 로직 처리 (TCP 서버)")
    print("  📡 통신: TCP 명세서 기반")
    print()
    
    # LMS 서버를 직접 실행 (데몬 스레드가 아닌 메인에서)
    try:
        run_lms_server()
    except KeyboardInterrupt:
        print("\n📶 프로그램 종료 중...")
        return 0
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())