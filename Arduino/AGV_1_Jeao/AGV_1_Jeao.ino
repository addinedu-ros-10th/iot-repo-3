#include <WiFi.h>
#include <esp_now.h>


uint8_t peerMac[6] = {0x00,0x4B,0x12,0x30,0x24,0xC0}; // Jeao_ESP32 MAC 00:4B:12:30:24:C0

const char* ssid = "AIE_509_2.4G";          //공유기 이름
const char* password = "addinedu_class1";    //공유기 비밀번호

void sendData(const char* msg);
void moveArea(int color, bool* move, bool* col_status);
int colorSearch(bool led);
void sendData(const char* msg);

struct RunTime {
unsigned long led_Time;
};
RunTime run_T;

const short col_s3 = 32, col_s2 = 33, col_s1 = 25, col_s0 = 26, col_out = 34, col_led = 2;
bool col_status = false;
const short dc_vcc = 13, dc_gnd = 12;

char u_c[10] = "";
char col_msg[][4] = {"UCR", "UCG", "UCY"};
bool msg_status = false;
bool move_status = false;
int color_num = 0;
int move_color = 0;

typedef struct {
char value[10];
} DataPacket;

volatile DataPacket latestData;
volatile bool newDataReceived = false;

  //받은 데이터를 자동 호출 함수(info: 송신자 Mac, incomingData: 전송된 데이터, len: 데이터 길이)
void onRecv(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len){
  if(len <= sizeof(DataPacket)){
    memcpy((void*)&latestData, (const void*)incomingData, sizeof(DataPacket));
    newDataReceived = true;
  }
}

DataPacket p;

void setup() {
  Serial.begin(115200);
  Serial.println("Jeao!");
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
  col_status = false;

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
  Serial.println("Ready");
}

void loop() {
  //수신 부분
  if(newDataReceived)
  {
    Serial.print("수신 성공: ");
    char buffer[10];
    strcpy(buffer, (const char*)latestData.value);
    strcpy(p.value, buffer);
    Serial.println(p.value);  // 바로 출력 가능
    newDataReceived = false;
    //msg_status = false;

    if(strncmp(p.value, "UC",2) == 0)
    {
      Serial.println("UC OK!");
      if(strcmp(p.value, "UCH") == 0)
      {
        move_status = true;
        col_status = true;
        msg_status = false;
        Serial.println("Come Back Home!");
      }
      else
      {
        for(int i = 0; i < 3; i++)
        {
          if(strcmp(p.value, col_msg[i]) == 0 && !move_status)
          {
            if(p.value[strlen(p.value)-1] == 'R')
            {
              Serial.println("block is RED!");
              color_num = 1;
              move_status = true;
              col_status = true;
            }
            else if(p.value[strlen(p.value)-1] == 'G')
            {
              Serial.println("block is GREEN!");
              color_num = 2;
              move_status = true;
              col_status = true;
            }
            else if(p.value[strlen(p.value)-1] == 'Y')
            {
              Serial.println("block is YELLOW!");
              color_num = 3;
              move_status = true;
              col_status = true;
            }
          }
        }
      }
      
    }
    else if (strncmp(p.value, "RM",2) == 0)
    {
      Serial.println("Robot Manual Mode");
    }
    
  }
  
  if(move_status && (strncmp(p.value, "UC",2) == 0))
  {
    if (strcmp(p.value, "UCH") == 0)
    {
      moveArea(4, &move_status, &col_status);
    }
    else
    {
      moveArea(color_num, &move_status, &col_status);
    }
  }

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

void moveArea(int color, bool* move, bool* col_status)
{
  if(move && color)
  {
    analogWrite(dc_vcc, 200);
    analogWrite(dc_gnd, 0);
  }
  else 
  {
    analogWrite(dc_vcc, 0);
    analogWrite(dc_gnd, 200);
  }

  if(color == colorSearch(col_status))
  {
    Serial.print(color);
    Serial.println(" 일치함 / 모터 정지");
    if (color != 4)
    {
      sendData("CI");
    }
    else
    {
      Serial.println("Success! Come Back Home!");
    }
    analogWrite(dc_vcc, 0);
    analogWrite(dc_gnd, 0);
    *move = false;
    *col_status = false;
    
  }
}

int colorSearch(bool col)
  {
  if (col)
  {
    //Red
    digitalWrite(col_s2, LOW);
    digitalWrite(col_s3, LOW);
    long redFrequency = pulseIn(col_out, LOW, 100000);
    // Green
    digitalWrite(col_s2, HIGH);
    digitalWrite(col_s3, HIGH);
    long greenFrequency = pulseIn(col_out, LOW, 100000);
    // Blue
    digitalWrite(col_s2, LOW);
    digitalWrite(col_s3, HIGH);
    long blueFrequency = pulseIn(col_out, LOW, 100000); 
    
    Serial.print("R= "); Serial.print(redFrequency); 
    Serial.print(" G= "); Serial.print(greenFrequency); 
    Serial.print(" B= "); Serial.println(blueFrequency); 
    short result; 

    if (blueFrequency < 120 && greenFrequency > 110) { 
      result = 1; 
    } 
    else if (redFrequency > 120 && blueFrequency > 110) { 
      result = 2; 
    } 
    else if (blueFrequency > 88 &&redFrequency < 100 && greenFrequency < 100) { 
      result = 3;
    }
    else if(redFrequency > 120 && greenFrequency > 110 && blueFrequency > 110)
    {
      Serial.println("???????");
      result = 4;
      delay(1000);
    }
    else { 
      result = 0; 
    } 
    return result;
  }
}
