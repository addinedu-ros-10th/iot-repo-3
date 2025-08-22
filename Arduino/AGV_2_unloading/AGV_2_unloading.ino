#include <ESP32Servo.h>

Servo myservo;

void steppingRun(bool run, short speed);
int colorSearch(bool led, unsigned long now_Time);

struct RunTime {
  unsigned long led_Time;
};

RunTime run_T;

const short step_s1 = 27, step_s2 = 14, step_s3 = 12, step_s4 = 13;
const short servo_pin = 15;
const short col_s0 = 32, col_s1 = 33, col_s2 = 25, col_s3 = 26, col_out = 34, col_led = 2;

int steps_cw[8] = { 0x01, 0x03, 0x02, 0x06, 0x04, 0x0C, 0x08, 0x09 };
int steps_ccw[8] = { 0x09, 0x08, 0x0C, 0x04, 0x06, 0x02, 0x03, 0x01 };
int step_index = 0;
short angle = 180;
bool col_led_status = false;

void setup() {
  Serial.begin(115200);

    // 스텝모터 스탭별 핀모드 적용
  pinMode(step_s1, OUTPUT);
  pinMode(step_s2, OUTPUT);
  pinMode(step_s3, OUTPUT);
  pinMode(step_s4, OUTPUT);

    //서보모터 초기 셋팅 위치
  myservo.attach(servo_pin);
  myservo.write(angle);

    // 컬러센서 셋팅 및 led 선언
  pinMode(col_s0, OUTPUT);
  pinMode(col_s1, OUTPUT);
  pinMode(col_s2, OUTPUT);
  pinMode(col_s3, OUTPUT);
  pinMode(col_led, OUTPUT);

  digitalWrite(col_led, HIGH);
  col_led_status = false;

    // RGB 주파수 스케일 설정
  digitalWrite(col_s0, HIGH);
  digitalWrite(col_s1, LOW);

    //컬러센서 LED 시간 초기화
  run_T.led_Time = 0;
}

void loop() {
  // put your main code here, to run repeatedly:
  unsigned long now = millis();
  bool block = false;

  steppingRun(true, 60);
  //colorSearch(true, now);

}

//_________________________________________________________
void steppingRun(bool run, short speed)
{
  speed = map(speed, 0, 100, 2000, 100);
  if (run)
  {
    if(! col_led_status) 
    {
      digitalWrite(col_led, HIGH);
      col_led_status = true;
    }

    digitalWrite(step_s1, bitRead(steps_cw[step_index], 0));
    digitalWrite(step_s2, bitRead(steps_cw[step_index], 1));
    digitalWrite(step_s3, bitRead(steps_cw[step_index], 2));
    digitalWrite(step_s4, bitRead(steps_cw[step_index], 3));

    step_index = (step_index + 1) % 8;
    delayMicroseconds(speed);
  }
  else
  {
    step_index = 0;
  }
}

int colorSearch(bool led, unsigned long now_Time)
{
  if (led)
  {
    if(now_Time - run_T.led_Time >= 200)
    {
      run_T.led_Time = now_Time;
        //Red
      digitalWrite(col_s2, LOW);
      digitalWrite(col_s3, LOW);
      int redFrequency = pulseIn(col_out, LOW);
        // Green
      digitalWrite(col_s2, HIGH);
      digitalWrite(col_s3, HIGH);
      int greenFrequency = pulseIn(col_out, LOW);
        // Blue
      digitalWrite(col_s2, LOW);
      digitalWrite(col_s3, HIGH);

      int blueFrequency = pulseIn(col_out, LOW);

      // Serial.print("R= "); Serial.print(redFrequency);
      // Serial.print(" G= "); Serial.print(greenFrequency);
      // Serial.print(" B= "); Serial.println(blueFrequency);

      delay(200);

      short result;
      if (redFrequency < 250 && greenFrequency > 300 && blueFrequency > 200) {
        result = 1;
      }
      else if (redFrequency > 200 && greenFrequency < 400 && blueFrequency > 200) {
        result = 2;
      }
      else if (redFrequency < 200 && greenFrequency < 300 && blueFrequency > 150) {
        result = 3;
      }
      else {
        result = 0;
      }
      // Serial.print(" -> Result: ");
      // Serial.println(result);
    }

  }
  

}