#include  "../header/api.h"    		// private library - API layer
#include  "../header/halGPIO.h"     // private library - HAL layer

int current_angle = 0;
const unsigned int halfsec = 0x5555;
const unsigned int quatersec = 0x2AAA;
const unsigned int eightsec = 0x1FFF;
const unsigned int sec = 0xAAAA;
const unsigned int thirdquatersec = 0x7FFF;




void change_degree(){

    setDegrees(current_angle);
    TimerWait(sec); //  need to check if can do less!
    stopPWM();
}


void setDegrees(int deg){
    set_SemiCircle_timer(deg);
    TimerWait(0xAAAA);
    stopPWM();
    enable_interrupts();

}


// ------------------------------------------------------------------
//                          STATE 1
// ------------------------------------------------------------------

void object_prox(){
    //  engine start
    //start_object_timers();
    //enable_interrupts();
    stopPWM();
    unsigned int k;
    enable_interrupts();
    for(k=350; k<=2150; k = k + 90){ // IF CHANGING ANGLES, CHANGE THE 60!
        stopPWM();
        if (k == 440){
            set_SemiCircle_timer(490);
        }
        else{
            set_SemiCircle_timer(k);
        }
        TimerWait(halfsec);
        //TimerWait(eightsec);
        //TimerWait(thirdhalfsec);
        stopPWM();
        UDSconfig();
        start_object_timers();
        enterLPM(lpm_mode);
        distance_append();
        if (state != state1){
            stopPWM();
            break;
        }
    }
    stopPWM();
    send_distance_list();
    //enterLPM(lpm_mode);
}

// ------------------------------------------------------------------
//                  STATE 2 - Telemeter
// ------------------------------------------------------------------

void Telemeter(int angle){
    int new_angle;
    //TimerWait(halfsec); //  need to check if can do less!
    stopPWM();
    UDSconfig();
    current_angle = angle;
    while(1){
        new_angle = get_angle();
        if (new_angle != current_angle){
            current_angle = new_angle;
            //stopPWM();
            //TimerWait(halfsec);
            //change_degree();
            setDegrees(current_angle);
            UDSconfig();
            start_object_timers();
        }
        if (state != state2){
            stop_USDscan();
            break;
        }
        enable_interrupts();
        start_object_timers();
        enterLPM(lpm_mode);
        if (state != state2){
            break;
        }
        send_distance();
        TimerWait(quatersec);
        //start_object_timers();

    }

}

// ------------------------------------------------------------------
//                          STATE 3
// ------------------------------------------------------------------


void calibration(){
    int line, avarage_ldr, last_scan = 0;
    for (line = 10; line >= 0; line--){
        if (state != state3 || state != state4 || calibrated() == '4'){
            set_calibration_flag();
            return;
        }
        enable_interrupts();
        startADC_ldr1();
        enterLPM(lpm_mode);
        stopADC();
        startADC_ldr2();
        enterLPM(lpm_mode);
        stopADC();
        avarage_ldr = return_ldr_avarage();

        while ((line > 3 && avarage_ldr > 1019) ||  avarage_ldr < last_scan - 100){
            if (line <=3 && avarage_ldr > 1019){
                break;
            }
            if (state != state3 || state != state4){
                return;
            }
            send_scan_error();
            enterLPM(lpm_mode);
            startADC_ldr1();
            enterLPM(lpm_mode);
            stopADC();
            startADC_ldr2();
            enterLPM(lpm_mode);
            stopADC();
            avarage_ldr = return_ldr_avarage();

        }
        last_scan = avarage_ldr;
        sendADC_value(avarage_ldr);
        if (!line){
            break;
        }
        sendNewlineREQ();
        enterLPM(lpm_mode);  // wait until ready signal from PC
    }
    send_done();
}


void light(){
    //stopPWM();
    ADC_idx_reset();
    unsigned int k;
    enable_interrupts();
    for(k=350; k<=2150; k = k + 90){ // IF CHANGING ANGLES, CHANGE THE 60!
            if (k == 440){
                set_SemiCircle_timer(490);
            }
            else{
                set_SemiCircle_timer(k);
            }
        TimerWait(thirdquatersec);
        //TimerWait(thirdhalfsec);
        //stopPWM();
        startADC_ldr1();
        enterLPM(lpm_mode);
        stopADC();
        startADC_ldr2();
        enterLPM(lpm_mode);
        stopADC();
        ADC_append();
        if (state != state3){
            stopPWM();
            break;
        }
    }
    stopPWM();
    send_ADC_list();

}

// ------------------------------------------------------------------
//                          STATE 4
// ------------------------------------------------------------------

void light_and_objects(){
    ADC_idx_reset();
    unsigned int k;
    enable_interrupts();
    for(k=350; k<=2150; k = k + 90){ // IF CHANGING ANGLES, CHANGE THE 60!
        stopPWM();
            if (k == 440){
                set_SemiCircle_timer(490);
            }
            else{
                set_SemiCircle_timer(k);
            }
        TimerWait(sec);
        //TimerWait(thirdhalfsec);
        //stopPWM();
        startADC_ldr1();
        enterLPM(lpm_mode);
        stopADC();
        startADC_ldr2();
        enterLPM(lpm_mode);
        stopADC();
        // end of ldr scan

        // start object scan
        stopPWM();
        UDSconfig();
        start_object_timers();
        enterLPM(lpm_mode);
        // end of object scan

        // start of appending data
        distance_append();
        ADC_append();
        if (state != state4){
            stopPWM();
            break;
        }
    }
    stopPWM();
    send_ADC_list();
    enterLPM(lpm_mode);  // waiting for acknowledge bit from pc
    send_distance_list();
}




// ------------------------------------------------------------------
//                          STATE 5
// ------------------------------------------------------------------

void script(){
    while(1){
        flash_ptrB = (char *) 0x1080;             // Initialize Flash segment B pointer
        flash_ptrC = (char *) 0x1040;             // Initialize Flash segment C pointer
        flash_ptrD = (char *) 0x1000;             // Initialize Flash segment D pointer
        if (state != state5){
            got_script = 0;
            break;
        }
        enterLPM(lpm_mode);  // MCU wake up after getting the script num

        if (got_script == 1){
            enterLPM(lpm_mode);
            if (get_script_size(1) != 0){
                got_script = 0;
                lcd_clear();
                char* a = (char*) 0x1080;
                lcd_data(*a++);
                lcd_data(*a++);
            }
            else{
                write_to_flash();
                *flash_ptrB = 0;                           // Dummy write to erase flash segmentB
                enterLPM(lpm_mode);
                // should exit in the end of receiving script
                stop_write_flash();
                }
        }

        else if (got_script == 2){
            if (get_script_size(2) != 0){

                got_script = 0;
                lcd_clear();
                lcd_puts("script2");
            }
            else{
                write_to_flash();
                *flash_ptrC = 0;                           // Dummy write to erase flash segmentC
                enterLPM(lpm_mode);
                // should exit in the end of receiving script
                stop_write_flash();
            }
        }

        else if (got_script == 3){
            if (get_script_size(3) != 0){
                got_script = 0;
                lcd_clear();
                lcd_puts("script3");
            }
            else{
                write_to_flash();
                *flash_ptrD = 0;                           // Dummy write to erase flash segmentD
                enterLPM(lpm_mode);
                // should exit in the end of receiving script
                stop_write_flash();
                }
        }
    }
}


void read_script(int script){
    int temp_address = 0x1080;
    int idx, script_bytes;
    char* address;
    char opcode[2], operand1[2], operand2[2];
    for (idx = 0; idx < script-1; idx ++){  // 0x1080 - (script - 1) * 0x40
        temp_address = temp_address - 0x40;
    }
    address = (char*) temp_address;
    script_bytes = get_script_size(script);
    while (script_bytes > 0){
        opcode[0] = *address++;
        opcode[1] = *address++;
        if (opcode == "08"){  // sleep
            enterLPM(lpm_mode);
            script_bytes -= 2;
            continue;
        }
        else if (opcode == "05"){ // clear lcd
            lcd_clear();
            script_bytes -= 2;
            continue;
        }
        else if (opcode == "07"){
            operand1[0] = *address++;
            operand1[1] = *address++;
            operand2[0] = *address++;
            operand2[1] = *address++;
            send_s('s');
            servo_scan_script(hex_to_int(operand1),hex_to_int(operand2));  // THIS IS WRONG!! NEED TO CALCULATE THE RIGHT PWM HIGH LEVEL TIME FOR EACH ANGLE
            script_bytes -= 6;
        }
        else{
            operand1[0] = *address++;
            operand1[1] = *address++;
            if (opcode == "01"){       // count up on LCD from until the number provided with Xdelay
                count_up_LCD(hex_to_int(operand1)-48);  // -48 because we have ASCII value and we want to send int
                script_bytes -= 4;
                continue;
            }
            else if (opcode == "02"){  // count down on LCD from the number provided to zero with Xdelay
                count_down_LCD(hex_to_int(operand1)-48);  // -48 because we have ASCII value and we want to send int
                script_bytes -= 4;
                continue;
            }
            else if (opcode == "03"){  // Rotate right onto LCD from pixel index 0 to pixel index 31 the provided char with Xdelay
                pixel_char_moving((char)hex_to_int(operand1))
                script_bytes -= 4;
                continue;
            }
            else if (opcode == "04"){
                // set delay
            }
            else if (opcode == "06"){
                // servo degree --> need to calculate the right PWM high level time
            }

        }

    }

}


int hex_to_int(char* hex){
    int result = 0;
    if(hex[0] >= 48 && hex[0] <= 57){
        result = ((int)hex[0] - 48) << 4;
        if (hex[1] >= 48 && hex[1] <= 57){
            result += (int)hex[1] - 48;
        }
        else{
            result += ((int)hex[1] - 55);
        }
    }
    else{
        result = ((int)hex[0] - 55) << 4;
        if (hex[1] >= 48 && hex[1] <= 57){
            result += (int)hex[1] - 48;
        }
        else{
            result += ((int)hex[1] - 55);
        }
    }
    return result;
}









