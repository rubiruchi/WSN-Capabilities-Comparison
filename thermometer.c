#include "contiki.h"
#include "dev/serial-line.h"
#include <stdlib.h>
#include "dev/uart1.h"
#include "dev/sht11/sht11-sensor.h"

/*---------------------------------------------------------------------------*/
PROCESS(thermometer_process, "thermometer process");
AUTOSTART_PROCESSES(&thermometer_process);
/*---------------------------------------------------------------------------*/
/*---------------------------------------------------------------------------*/
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(sink_process, ev, data){
  PROCESS_BEGIN();
  PROCESS_EXITHANDLER(abc_close(&abc));

  uart1_set_input(serial_line_input_byte);

  leds_on(LEDS_GREEN);
  SENSORS_ACTIVATE(sht11_sensor);
  leds_on(LEDS_ALL);

  sht11_init();
  serial_line_init();

/* main loop */
  while(1){
    /* handle serial line input */
    PROCESS_WAIT_EVENT_UNTIL(ev == serial_line_event_message);
    if(ev == serial_line_event_message){
        printf("NODE$Temp@%u\n",(unsigned)(-39.60 + 0.01 * sht11_temp()));
    }
  }
  PROCESS_END();
}
