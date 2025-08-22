"""
LMS TCP 서버

TCP 명세서에 따른 LMS (Logistic Management System) 서버 구현
GUI 클라이언트의 요청을 받아 재고 관리 작업을 수행합니다.
"""

import socket
import threading
import time
import struct
from typing import Optional

from ..handlers.command_handler import create_command_handler


class LMSServer:
    """
    LMS TCP 서버 클래스
    
    TCP 명세서에 따라 GUI 클라이언트와 통신하며
    재고 관리 명령을 처리합니다.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 9999):
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self.command_handler = create_command_handler()
        self.client_threads = []
        
    def start(self) -> None:
        """서버를 시작합니다."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.is_running = True
            print(f" LMS 서버가 {self.host}:{self.port}에서 시작되었습니다.")
            print(f" TCP 명세서에 따른 명령어 처리 준비 완료")
            print(f" GUI 클라이언트 연결을 대기 중...")
            
            while self.is_running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    print(f" 클라이언트 연결: {addr}")
                    
                    # 클라이언트 처리를 위한 새 스레드 시작
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr),
                        daemon=False
                    )
                    client_thread.start()
                    self.client_threads.append(client_thread)
                    
                except socket.error as e:
                    if self.is_running:
                        print(f"❌ 클라이언트 연결 수락 중 오류: {e}")
                        
        except Exception as e:
            print(f"❌ 서버 시작 실패: {e}")
        finally:
            self._cleanup()
    
    def _handle_client(self, client_socket: socket.socket, addr: tuple) -> None:
        """개별 클라이언트 요청을 처리합니다."""
        try:
            while self.is_running:
                # TCP 명세서에 따른 요청 수신
                # Command (2) + Data (4) + End (1) = 7 bytes
                request_data = client_socket.recv(7)
                
                if not request_data:
                    break
                
                if len(request_data) != 7 or request_data[-1:] != b'\n':
                    print(f"⚠️ 잘못된 요청 형식: {addr}")
                    continue
                
                # 요청 파싱
                command = request_data[:2].decode('ascii')
                data = request_data[2:6]
                
                print(f"요청 수신 [{addr}]: {command}")
                
                # 명령어 처리
                response = self.command_handler.process_command(command, data)
                
                # 응답 전송
                client_socket.sendall(response)
                
                # 응답 해석하여 출력
                self._print_readable_response(response, addr)
                
        except ConnectionResetError:
            print(f"클라이언트 연결 끊김: {addr}")
        except Exception as e:
            print(f" 클라이언트 처리 중 오류 [{addr}]: {e}")
        finally:
            try:
                client_socket.close()
                print(f" 클라이언트 연결 종료: {addr}")
            except:
                pass
    
    def stop(self) -> None:
        """서버를 중지합니다."""
        print("\n💤 LMS 서버 중지 중...")
        self.is_running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # 모든 클라이언트 스레드 종료 대기
        print("🔄 클라이언트 연결 정리 중...")
        for thread in self.client_threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        print("✅ LMS 서버가 안전하게 종료되었습니다.")
    
    def _cleanup(self) -> None:
        """리소스 정리"""
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
    
    def _print_readable_response(self, response: bytes, addr: tuple) -> None:
        """응답을 읽기 쉬운 형태로 출력합니다."""
        try:
            if len(response) < 4:
                print(f" 응답 전송 [{addr}]: {response.hex()}")
                return
            
            command = response[:2].decode('ascii')
            status_code = response[2]
            
            print(f" 응답 전송 [{addr}]:")
            
            if command == 'AI' and status_code == 0x00 and len(response) >= 24:  # AI 성공 응답
                # AI 응답: Command(2) + Status(1) + StockData(20) + End(1) = 24 bytes
                stock_data = response[3:23]  # 20바이트 재고 데이터
                stocks = struct.unpack('>IIIII', stock_data)
                
                print(f"  RECEIVING 재고 : {stocks[0]}")
                print(f"  RED_STORAGE 재고 : {stocks[1]}")
                print(f"  GREEN_STORAGE 재고 : {stocks[2]}")
                print(f"  YELLOW_STORAGE 재고 : {stocks[3]}")
                print(f"  SHIPPING 재고 : {stocks[4]}")
            elif command == 'CU' and status_code == 0x00 and len(response) >= 12:  # CU 성공 응답
                # CU 응답: Command(2) + Status(1) + CumulativeData(8) + End(1) = 12 bytes
                cumulative_data = response[3:11]  # 8바이트 누적 데이터
                cumulative_stocks = struct.unpack('>II', cumulative_data)
                
                print(f"  RECEIVING 누적 입고 : {cumulative_stocks[0]}")
                print(f"  SHIPPING 누적 출고 : {cumulative_stocks[1]}")
            else:
                # 다른 명령어나 오류 응답
                print(f"  {response.hex()}")
                
        except Exception as e:
            print(f" 응답 전송 [{addr}]: {response.hex()} (파싱 오류: {e})")
    
    def get_server_info(self) -> dict:
        """서버 상태 정보 반환"""
        return {
            'host': self.host,
            'port': self.port,
            'is_running': self.is_running,
            'active_clients': len([t for t in self.client_threads if t.is_alive()])
        }


def main():
    """LMS 서버 메인 실행 함수"""
    print("=" * 60)
    print(" LMS (Logistic Management System) 서버")
    print("=" * 60)
    
    server = LMSServer()
    
    try:
        # 서버 직접 시작
        server.start()
    except KeyboardInterrupt:
        print("\n⌨ 키보드 인터럽트 감지")
    except Exception as e:
        print(f" 서버 실행 중 오류: {e}")
    finally:
        server.stop()


if __name__ == "__main__":
    main()