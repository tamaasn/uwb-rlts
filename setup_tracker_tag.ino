/* Cerdas UWB Tracker V3.0 (will not work for previous version)

 * Please set :
 * USB CDC On Boot : "Enabled" 
 * USB DFU On Boot : "Disabled"
 * USB Firmware MSC On Boot : "Disabled"
 * Upload Mode : "UART0/Hardware CDC"
 * USB Mode : "USB-OTG (TinyUSB)"
 */

 // currently tag is module #5
// The purpose of this code is to set the tag address and antenna delay to default.
// this tag will be used for calibrating the anchors.

#include <SPI.h>
#include "DW1000Ranging.h"
#include "DW1000.h"
#include "WiFi.h"
#include <bits/stdc++.h>

#define EN_UWB 5

#define SPI_SCK 14
#define SPI_MISO 16
#define SPI_MOSI 18
#define DW_CS 33

#define SSID "akmal"
#define PASSWORD "akmalsani"

// connection pins
const uint8_t PIN_RST = 7; // reset pin
const uint8_t PIN_IRQ = 13; // irq pin
const uint8_t PIN_SS = 33;   // spi select pin

std::map<int,int> address;
// TAG antenna delay defaults to 16384
// leftmost two bytes below will become the "short address"
char tag_addr[] = "7D:00:22:EA:82:60:3B:9C";
WiFiClient client;

void setup() {
  // turn on UWB Module
  pinMode(EN_UWB, OUTPUT);
  digitalWrite(EN_UWB, HIGH);

  Serial.begin(115200);
  delay(1000);
  
  WiFi.begin(SSID,PASSWORD);
  while(WiFi.status() != WL_CONNECTED){
    Serial.print(".");
    delay(500);
  }
  address[0x1783] = 0;
  address[0x1782] = 1;
  address[0x1784] = 2;

  //init the configuration
  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
  DW1000Ranging.initCommunication(PIN_RST, PIN_SS, PIN_IRQ); //Reset, CS, IRQ pin

  DW1000Ranging.attachNewRange(newRange);
  DW1000Ranging.attachNewDevice(newDevice);
  DW1000Ranging.attachInactiveDevice(inactiveDevice);
  
  //DM1000 indicator LED
  DW1000.enableDebounceClock();
  DW1000.enableLedBlinking();
  DW1000.setGPIOMode(MSGP0, LED_MODE);  

  // start as tag, do not assign random short address
  DW1000Ranging.startAsTag(tag_addr, DW1000.MODE_LONGDATA_RANGE_LOWPOWER, false);
  bool connected = client.connect(IPAddress("192.168.1.11"),1150);
  while (!connected){
    Serial.println("Connection failed");
    delay(1000);
    connected = client.connect(IPAddress("192.168.43.11"),1150);
  }
}

void loop() {
  DW1000Ranging.loop();
}

void newRange() {
  int address = DW1000Ranging.getDistantDevice()->getShortAddress();
  float range = 0;
  for(int i=0;i<1;i++){
    range += DW1000Ranging.getDistantDevice()->getRange();
  }
  range/=1;
  Serial.print(address);
  Serial.print(",");
  Serial.println(range);
  char payload[256];
  snprintf(payload,sizeof(payload),"%d|%.4f;",address,range);
  if (client.connected()) client.write(payload);
  client.flush();

}

void newDevice(DW1000Device *device) {
  Serial.print("Device added: ");
  Serial.println(device->getShortAddress());
}


void inactiveDevice(DW1000Device *device) {
  Serial.print("delete inactive device: ");
  Serial.println(device->getShortAddress(), HEX);
}