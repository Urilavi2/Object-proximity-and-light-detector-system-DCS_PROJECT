#include  "../header/api.h"         // private library - API layer
#include  "../header/app.h"         // private library - APP layer

enum FSMstate state;
enum SYSmode lpm_mode;
char main_menu_return;
void main(void){
  

  state = state0;
  lpm_mode = mode0;     
  sysConfig();
  lcd_init();
  lcd_clear();
  while(1){
    switch(state){
      case state0:

          stopPWM();
          setDegrees(350);
          lcd_clear();
          lcd_home();
          char* a = (char*) 0x1080;
          lcd_data(*a++);
          lcd_data(*a++);
          //lcd_puts("state0");
          enterLPM(lpm_mode);
          break;
         
      case state1:
          lcd_clear();
          lcd_puts("state1");

          while(1){
              enterLPM(lpm_mode);
              if (state != state1){
                  break;
              }
              object_prox();
              if (state != state1){
                  break;
              }
          }
         break;

      case state2:
          lcd_clear();
          lcd_puts("state2");
          enterLPM(lpm_mode); // ANGLE RECIVED
          setDegrees(get_angle());
          Telemeter(get_angle());
          break;

      case state3:
        //setDegrees(1050);
        if (calibrated() == '1'){
            enterLPM(lpm_mode);
            if (state != state3){
                break;
            }
            lcd_clear();
            lcd_puts("state3");
            lcd_new_line;
            lcd_puts("calibration");
            calibration();
            main_menu_return = '0';
        }
        lcd_clear();
        lcd_puts("state3");
        lcd_new_line;
        lcd_puts("scanning..");
        if (state != state3){
            break;
        }
        while(1){
            if (main_menu_return == '0'){
                enterLPM(lpm_mode);  // if goes to main menu and return to state3, we are asleep here!
            }
            if (state != state3){
                main_menu_return = '1';
                break;
            }
            if (calibrated() == '1'){
                enterLPM(lpm_mode);
                if (state != state3){
                    break;
                }
                lcd_clear();
                lcd_puts("state3");
                lcd_new_line;
                lcd_puts("calibration");
                setDegrees(350);
                calibration();
                if (state != state3){
                    break;
                }
            }
            light();
            if (main_menu_return == '1'){
                enterLPM(lpm_mode);
            }
            if (state != state3){
                main_menu_return = '1';
                break;
                }
        }
        break;

      case state4:
          if (calibrated() == '1'){
              lcd_clear();
              lcd_puts("state4");
              lcd_new_line;
              lcd_puts("calibration");
              enterLPM(lpm_mode);
              if (state != state4){
                  break;
              }
              calibration();
              main_menu_return = '0';
          }
          lcd_clear();
          lcd_puts("state4");
          lcd_new_line;
          lcd_puts("scanning..");
          if (state != state4){
              break;
          }
          while(1){
              if (main_menu_return == '0'){
                  enterLPM(lpm_mode);  // if goes to main menu and return to state3, we are asleep here!
              }
              if (state != state4){
                  main_menu_return = '1';
                  break;
              }
              if (calibrated() == '1'){
                  enterLPM(lpm_mode);
                  if (state != state4){
                      break;
                  }
                  lcd_clear();
                  lcd_puts("state4");
                  lcd_new_line;
                  lcd_puts("calibration");
                  setDegrees(350);
                  calibration();
                  if (state != state4){
                      break;
                  }
              }
              light_and_objects();
              if (main_menu_return == '1'){
                  enterLPM(lpm_mode);
              }
              if (state != state4){
                  main_menu_return = '1';
                  break;
                  }
          }

           break;

      case state5:
          lcd_clear();
          lcd_puts("script mode");
          script();

          break;

      case state6:  // CALIBRATION STATE!
          lcd_clear();
          lcd_puts("push button 0");
          lcd_new_line;
          lcd_puts("calibration");
          enterLPM(lpm_mode);
          calibration();
          main_menu_return = '0';
          state = state0;

        break;



    }
  }
}
  

  
  
  
