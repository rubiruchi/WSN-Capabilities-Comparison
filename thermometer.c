#include "contiki.h"
#include "dev/serial-line.h"
#include <stdio.h>
#include "dev/uart1.h"
#include "dev/sht11/sht11-sensor.h"
#include "dev/leds.h"

/*---------------------------------------------------------------------------*/
PROCESS(thermometer_process, "thermometer process");
AUTOSTART_PROCESSES(&thermometer_process);
/*---------------------------------------------------------------------------*/
/*---------------------------------------------------------------------------*/
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(thermometer_process, ev, data){
  PROCESS_BEGIN();

  uart1_set_input(serial_line_input_byte);

  leds_on(LEDS_GREEN);
  SENSORS_ACTIVATE(sht11_sensor);
  leds_on(LEDS_BLUE);

  sht11_init();
  serial_line_init();

/* main loop */
  while(1){
    /* handle serial line input */
    PROCESS_WAIT_EVENT_UNTIL(ev == serial_line_event_message);
    if(ev == serial_line_event_message){
      char* str_ptr = (char*) data;

      uint8_t comma_counter = 0;
      while(*str_ptr != '\0'){
        if(*str_ptr == ','){
          comma_counter++;
        }
        str_ptr++;
      }

      if(comma_counter == 4){
        leds_toggle(LEDS_GREEN);
        unsigned rh = sht11_humidity();
        printf("NODE$Temp@%u | Hum@%u\n",
        ((unsigned)(-39.60 + 0.01 * sht11_temp())),
        ((unsigned) (-4 + 0.0405 * rh -2.8e-6 * (rh * rh))) );
      }
    }
  }
  PROCESS_END();
}
