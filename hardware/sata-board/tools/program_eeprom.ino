// Запись карты платы в AT24C02 на сата-плате.
// Это памятка для сборщика, а не часть прошивки контроллера.
//
// Программатор — ESP32 на 3,3 В. Arduino Uno на 5 В не подходит:
// 5 В на SDA/SCL портят и AT24C02, и PCA9554, они сидят на той же шине.
//
// Питать только с гребёнки J3, слот 12 В не включать:
//   контакт 1  3V3_AUX  -> 3,3 В ESP32
//   контакт 2  GND      -> GND
//   контакт 5  SDA
//   контакт 6  SCL
// WP уже сидит на земле на плате, отдельный провод не нужен.
// С завода микросхема читается как 0xFF. На фабрике её не прошивают.

#include <Wire.h>

static const uint8_t ADDR = 0x50;  // 7-битный адрес AT24C02
static const int PIN_SDA = 21;    // свой GPIO, куда пришёл контакт 5
static const int PIN_SCL = 22;    // свой GPIO, куда пришёл контакт 6

static uint8_t image[256];

void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(100000);

  memset(image, 0, sizeof(image));
  image[0] = 'S';
  image[1] = 'L';
  image[2] = 'I';
  image[3] = 'B';
  image[4] = 1;  // версия карты
  image[5] = 4;  // число дисков
  image[6] = 1;  // ревизия платы
  // байты 7..255 остаются нулями

  // страница AT24C02 — 8 байт, после страницы пауза на запись
  for (int off = 0; off < 256; off += 8) {
    Wire.beginTransmission(ADDR);
    Wire.write((uint8_t)off);
    Wire.write(&image[off], 8);
    uint8_t err = Wire.endTransmission();
    if (err != 0) {
      Serial.printf("запись с %d не прошла, код %u\n", off, err);
      return;
    }
    delay(10);
  }

  uint8_t back[256];
  for (int off = 0; off < 256; off += 16) {
    Wire.beginTransmission(ADDR);
    Wire.write((uint8_t)off);
    Wire.endTransmission(false);
    Wire.requestFrom(ADDR, (uint8_t)16);
    for (int i = 0; i < 16; i++) {
      back[off + i] = Wire.read();
    }
  }

  if (memcmp(image, back, 256) == 0) {
    Serial.println("EEPROM записана: SLIB, версия 1, дисков 4, ревизия 1");
  } else {
    Serial.println("чтение не совпало с картой, повторить запись");
  }
}

void loop() {}
