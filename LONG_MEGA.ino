
// Use software serial if you have only one Rx-Tx pair
//#include <SoftwareSerial.h>
//SoftwareSerial Serial2(9, 8); // rx, tx
///////////////////////////////////////////////////
/*
Current config:
LED (Hall light) - Pin 13
Potentiometer (Kitchen temoerature) - Analog Pin A1
Check switch status (check status hall) - Pin 7
Servo motor - Pin 9
*/
///////////////////////////////////////////////////

#include <Servo.h>
#define SpecialId "12345"
#define SSID "Tenda"
#define PASS "hellobro"
#define DST_IP "192.168.0.104" 
#define DEST_PORT 5555

// This is rest function, to reset Arduino board
void(* resetFunc) (void) = 0;

// This function runs only once, during the execcution
void setup(){
  delay(5000);
//serial 2 is to esp8266
  Serial2.begin(115200);
  Serial2.setTimeout(500);
  Serial.begin(115200);

// check wether serial is available or not..
  while (!Serial);
  while (!Serial2);

  Serial.println("ESP8266 Demo on Mega2560");

  while (Serial2.available() > 0){
    Serial2.read();
  }

//test if the module is ready
  Serial2.println("AT+RST");
  Serial2.flush();
  delay(1000);
  if (Serial2.find((char*)"OK")){
    Serial.println("Module is ready");
  }
  else{
    Serial.println("Module have no response.");
  }
  delay(1000);

//quit existing connection
  Serial2.println("AT+CWQAP");
  Serial2.flush();
  delay(1000);
  if (Serial2.find((char*)"WIFI DISCONNECT")){
    Serial.println("Module is QUIT");
  }
  else{
    Serial.println("Module have no QUIT.");
  }
  delay(1000);
  
  while (Serial2.available() > 0){
    Serial2.read();
  }
// try to connect wifi
  boolean connected = false;
  for (int i = 0; i < 10; i++){
    if (connectWiFi()){
      connected = true;
      break;
    }
  }
  if (!connected) {
    resetFunc();
    while (1);
  }
  delay(1000);
  
//set the single connection mode
  Serial2.println("AT+CIPMUX=0");
  delay(5000);
  
////  close existing connections (No need this code right now.)
//  Serial2.println("AT+CIPCLOSE");
//  Serial2.flush();
//  delay(1000);
//  if (Serial2.find((char*)"OK")){
//    Serial.println("IP QUIT");
//  }
//  else{
//    Serial.println("IP no QUIT.");
//  }
//  delay(1000);

  String cmd = SpecialId;
// wait till it connect to tcp
  while(1){  
    Serial2.print("AT+CIPSEND=");
    Serial2.println(cmd.length());
    if (Serial2.find((char*)">")){
      Serial.print(">");
      Serial2.println(cmd);
      Serial2.flush();
      String recvd = Serial2.readString();
      Serial.println("Recvd str="+recvd);
      Serial.println("Recvd end");
      Serial.println("====");
      break;
    } else{
      Serial2.println("AT+CIPCLOSE");
      Serial.println("connect timeout");
      delay(2000);
      connect_tcp();
    }
  }
}

// This loop function runs indefinately. like while(1){}.
void loop(){

    while(Serial2.available()){ // If serial buffer has somethig in it.
//      Serial.println("This is forever");
// fetch input command sent by server from seral2 to 'input' var.
      String recv=Serial2.readString();
      Serial.println("REC: "+recv);
// Now fetch command from serial buffer
      int ind=0;
      for(ind=0;ind<recv.length()-3;ind++){
        if(recv.charAt(ind)=='I')
          if(recv.charAt(ind+1)=='P')
            if(recv.charAt(ind+2)=='D')
              break;
      }
      int ind2;
      for(ind2=ind+4;ind2<recv.length();ind2++){
        if(recv.charAt(ind2)==':')
          break;
      }
      String input=recv.substring(ind2+1);

      // Input is our command string. Interprate it and send responce back to server.
      Serial.println(input);
      //Responce is "actual cmmand + its reply"
      String responce = input+","+interpretate(input);
      Serial2.print("AT+CIPSEND=");
      Serial2.println(responce.length());
      if (Serial2.find((char*)">"))
      {
        Serial.print(">");
      } else
      {
        Serial2.println("AT+CIPCLOSE");
        Serial.println("error accur");
        delay(1000);
        // try the line below. it shall restart Arduino
        resetFunc();
        while(1);
      }
      Serial2.println(responce);
      Serial2.flush();
      Serial.println("RED:"+Serial2.readString());
      delay(200);
    }  
    
}

// Connect to wifi with given SSID and PWD defiened in Macro.
boolean connectWiFi()
{
  Serial2.println("AT+CWMODE=1");
  Serial2.flush();
  delay(1000);
  while (Serial2.available() > 0){
    Serial2.read();
  }
  String cmd = "AT+CWJAP=\"";
  cmd += SSID;
  cmd += "\",\"";
  cmd += PASS;
  cmd += "\"";
  Serial2.println(cmd);
  Serial.println(cmd);
  delay(5000);
  if (Serial2.find((char*)"WIFI CONNECTED")){
    Serial.println("OK, Connected to WiFi.");
    return true;
  } else{
    Serial.println("Can not connect to the WiFi.");
    return false;
  }
}

// Connect to TCP server. server id and port as defiened in Macro
boolean connect_tcp(){
  String cmd = "AT+CIPSTART=\"TCP\",\"";
  cmd += DST_IP;
  cmd += "\",";
  cmd += DEST_PORT;
  Serial2.println(cmd);
  Serial.println(cmd);
  if (Serial2.find((char*)"CONNECT"))
    return true;
  else
    return false;
}


// This function interepretate the command given by Server. Try to perform the task and return the reply in specific format.
/*
 >>Command/Reply format:
  Command : aabbxxxxyyyy
  aa=operation, bb=state, xxxx=param1, yyyy=param2

  Reply : abxxxx
  a=acceptance status
  b=operation performed status
  xxxx=operation return value
 
 >>Accepted commands:
 "gp" = GPIO related operation. Accepted state: "dr" (digital read), "dw" (digital write), "ar" (analog read), "aw" (analog write)
 "sm" = Servom motor related command
*/
String interpretate(String cmd){
  int cmd_len = cmd.length();
  int no_param = (cmd_len-4)/4;
  String operation="",state="",parameter[10];
  if(cmd_len!=2 && cmd_len%4!=0){
    return "00";
  }
  operation = cmd.substring(0,2);
  operation.toLowerCase();
  cmd_len-=2;
  if(cmd_len>2){
    state = cmd.substring(2,4);
    state.toLowerCase();
    int i=0;
    while(cmd_len>0){
      parameter[i]=cmd.substring(4*(i+1),4*(i+2));
      parameter[i].toLowerCase();
      i++;
      cmd_len-=4;
    }
  }
// done command striping
  if(operation=="gp"){ // gpio handler
    if(state=="dr"){
      if(no_param>=1){
        //pinMode(parameter[0].toInt(), INPUT);
        int reading=digitalRead(parameter[0].toInt());
        Serial.println(reading);
        return "11"+pad(String(reading));
      }
      else{
        return "10";
      }
    }
    else if(state=="dw"){
      if(no_param>=2){
        pinMode(parameter[0].toInt(), OUTPUT);
        digitalWrite(parameter[0].toInt(), parameter[1].toInt());
        Serial.println(parameter[0].toInt());
        Serial.println(parameter[1].toInt());
        return "11"+pad(String(parameter[1].toInt()));
      }
      else{
        return "10";
      }
    }
    else if(state=="ar"){
      if(no_param>=1){
        int reading = analogRead(parameter[0].toInt());
        Serial.println(reading);
        return "11"+pad(String(reading));
      }
      else{
        return "10";
      }
    }
    else if(state=="aw"){
      if(no_param>=2){
        pinMode(parameter[0].toInt(), OUTPUT);
        analogWrite(parameter[0].toInt(), parameter[1].toInt());
        Serial.println(parameter[0].toInt());
        Serial.println(parameter[1].toInt());
        return "11"+pad(String(parameter[1].toInt()));
      }
      else{
        return "10";
      }
    }
    else{
      return "10";
    }
  }
  else if(operation=="sm"){
    int mn=state.toInt();
    if(no_param>=1){
      Servo myservo;
      myservo.attach(9);
      myservo.write(parameter[0].toInt());
      return "11"+pad(parameter[0]);
    }
    else{
      return "10";
    }
    
  }
  else{
    return "00";
  }


}
// Pad reply string to make it 4 bytes
String pad(String rep){
  int len = rep.length();
  String ret;
  if(len==1){
    ret="000"+rep;
  }
  else if(len==2){
    ret="00"+rep;
  }
  else if(len==3){
    ret="0"+rep;
  }else if(len==4){
    ret=rep;
  }  
  else{
    ret = "0000";
  }
  return ret;
}

