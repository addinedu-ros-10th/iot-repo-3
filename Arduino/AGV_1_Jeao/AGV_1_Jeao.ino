#include <WiFi.h>
#include <esp_now.h>


uint8_t peerMac[6] = {0x08,0xA6,0xF7,0x21,0xAC,0xF4}; // Jeao_ESP32 MAC 00:4B:12:30:24:C0

const char* ssid = "AIE_509_2.4G";          //공유기 이름
const char* password = "addinedu_class1";    //공유기 비밀번호

void sendData(const char* msg);
void moveArea(char* color, bool move);

struct RunTime {
unsigned long led_Time;
};
RunTime run_T;

const short col_s0 = 32, col_s1 = 33, col_s2 = 25, col_s3 = 26, col_out = 34, col_led = 2;
bool col_status = false;
const short dc_vcc = 13, dc_gnd = 12;

char u_c[10] = "";
bool msg_status = false;
bool move_status = false;

typedef struct {
char value[10];
} DataPacket;

volatile DataPacket latestData;
volatile bool newDataReceived = false;

  //받은 데이터를 자동 호출 함수(info: 송신자 Mac, incomingData: 전송된 데이터, len: 데이터 길이)
void onRecv(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len){
  if(len == sizeof(DataPacket)){
    memcpy((void*)&latestData, (const void*)incomingData, sizeof(DataPacket));
    newDataReceived = true;
  }
}

DataPacket p;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);   //공유기 접속 시도
  Serial.print("Wi-Fi 연결중");
  while(WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi 연결 성공!");
  Serial.print("IP 주소: ");
  Serial.println(WiFi.localIP());   // ESP32의 IP 확인
  Serial.print("Unloading ESP32 MAC : ");
  Serial.println(WiFi.macAddress());

  // 컬러센서 셋팅 및 led 선언
  pinMode(col_s0, OUTPUT);
  pinMode(col_s1, OUTPUT);
  pinMode(col_s2, OUTPUT);
  pinMode(col_s3, OUTPUT);
  pinMode(col_led, OUTPUT);
  pinMode(col_out, INPUT);
  digitalWrite(col_led, LOW);
  col_status = true;

  // RGB 주파수 스케일 설정
  digitalWrite(col_s0, HIGH);
  digitalWrite(col_s1, LOW);
  
  //컬러센서 LED 시간 초기화
  run_T.led_Time = 0;

    //DC 모터 셋틴
  pinMode(dc_vcc, OUTPUT);
  pinMode(dc_gnd, OUTPUT);

  WiFi.mode(WIFI_STA);
  if(esp_now_init() != ESP_OK)
  {
    Serial.println("ESP-NOW init fail");
  }
  // 피어 등록
  esp_now_peer_info_t peer{};
  memcpy(peer.peer_addr, peerMac, 6);
  peer.channel = 0;
  peer.encrypt = false;
  esp_now_add_peer(&peer);
    // 수신 콜백 등록
  esp_now_register_recv_cb(onRecv);
}

void loop() {
  //수신 부분
  if(newDataReceived && !move_status)
  {
    Serial.print("수신 성공: ");
    char buffer[10];
    strcpy(buffer, (const char*)latestData.value);
    strcpy(p.value, buffer);
    Serial.println(p.value);  // 바로 출력 가능
    newDataReceived = false;
  }

  if(!move_status)
  {
    int color_num = 0;
    if(p.value[strlen(p.value)-1] == 'R')
    {
      Serial.println("block is RED!");
      color_num = 1;
      move_status = true;
    }
    else if(p.value[-1] == 'G')
    {
      Serial.println("block is GREEN!");
      color_num = 2;
      move_status = true;
    }
    else if(p.value[-1] == 'Y')
    {
      Serial.println("block is YELLOW!");
      color_num = 3;
      move_status = true;
    }
  }

  moveArea(p.value, move_status);
  
}

void sendData(const char* msg) {
  if (strlen(msg) != 0)
  {
      // 문자열을 구조체에 복사
    strncpy(p.value, msg, sizeof(p.value));
    p.value[sizeof(p.value) - 1] = '\0'; // NULL 종료 보장

    // ESP-NOW 송신
    esp_err_t result = esp_now_send(peerMac, (uint8_t*)&p, sizeof(p));
    if(result == ESP_OK) {
      Serial.println("송신 성공: " + String(p.value));
      msg_status = true;
    } else {
      Serial.println("송신 실패");
    }
  }
}

void moveArea(char* color, bool move)
{
  if(move)
  {
    analogWrite(dc_vcc, 150);
    analogWrite(dc_gnd, 0);
  }
}