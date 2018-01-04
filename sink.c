#include "node.h"
#include "dev/serial-line.h"
#include <stdlib.h>

#ifdef z1
#include "dev/uart0.h"
#else
#include "dev/uart1.h"
#endif

#if defined(z1) || defined(sky)
#define sht11
#define TEMPSENSOR sht11_sensor
#include "dev/sht11/sht11-sensor.h"
#endif

#ifdef openmote
#define sht21_s
#include "dev/button-sensor.h"
#include "dev/sht21.h"

#define TEMPSENSOR sht21
#endif

#ifdef sensortag
#define hdc
#include "hdc-1000-sensor.h"
#define TEMPSENSOR hdc_1000_sensor
#endif

/*---------------------------------------------------------------------------*/
PROCESS(sink_process, "sink process");
AUTOSTART_PROCESSES(&sink_process);
/*---------------------------------------------------------------------------*/
static uint8_t last_node_id;
static struct etimer round_timer;
static struct etimer emergency_timer;
static int number_of_rounds, current_round;
static uint8_t rounds_failed;
static uint8_t round_finished;
static uint8_t recently_reset;
static uint8_t reset_counter;
/*---------------------------------------------------------------------------*/
static void abc_recv(){
    msg_t received_msg = *(msg_t*) packetbuf_dataptr();

    print_link_data(&received_msg);

    fill_link_data(received_msg.node_id,
      received_msg.last_node,
      packetbuf_attr(PACKETBUF_ATTR_RSSI),
      packetbuf_attr(PACKETBUF_ATTR_LINK_QUALITY),
      received_msg.link_param);

      if(received_msg.node_id == last_node_id){
        rounds_failed = 0;
        round_finished = 1;
      }

}

/* in °C */
static void read_temperature(){
  #ifdef sht11
  sht11_init();
  unsigned rh = sht11_humidity();
  printf("NODE$Temp@%u | Hum@%u\n",
  ((unsigned)(-39.60 + 0.01 * sht11_temp())),
  ((unsigned) (-4 + 0.0405 * rh -2.8e-6 * (rh * rh))) );
  #endif

  #ifdef sht21_s
  printf("NODE$Temp@%u\n", sht21.value(SHT21_READ_TEMP) / 100);
  #endif

  #ifdef hdc
  printf("NODE$Temp@%d | Hum@%d\n", hdc_1000_sensor.value(HDC_1000_SENSOR_TYPE_TEMP) / 100,
  hdc_1000_sensor.value(HDC_1000_SENSOR_TYPE_HUMIDITY) / 100);
  #endif
}
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(sink_process, ev, data){
  PROCESS_BEGIN();
  PROCESS_EXITHANDLER(abc_close(&abc));

  #ifdef z1
  uart0_set_input(serial_line_input_byte);
  #else
  uart1_set_input(serial_line_input_byte);
  #endif

  serial_line_init();

  NETSTACK_RADIO.set_value(RADIO_PARAM_TX_MODE, 0);

  message.node_id = node_id;
  current_channel = DEFAULT_CHANNEL;
  current_txpower = DEFAULT_TX_POWER;

  abc_open(&abc, DEFAULT_CHANNEL, &abc_call);

  rounds_failed = 0;
  recently_reset = 1;     // has to be 1 initially to ensure that all nodes report back in initail round
  number_of_rounds = -1;  // -1 to make sure variable is set via serial input
  current_round = 0;
  reset_counter = 0;

  leds_on(LEDS_GREEN);
  SENSORS_ACTIVATE(TEMPSENSOR);
  leds_on(LEDS_ALL);

  printf("NODE$Booted\n");
  printf("Enter parameters in the following way:\n <last node>,<channel>,<txpower>,<link param>,<number of rounds>\n");

/* main loop */
  while(1){
    etimer_set(&emergency_timer,CLOCK_SECOND*360);

    /* handle serial line input */
    PROCESS_WAIT_EVENT_UNTIL(ev == serial_line_event_message || etimer_expired(&emergency_timer));
    if(ev == serial_line_event_message){
      char* str_ptr = (char*) data;
      char* comma_ptr = &(*str_ptr);

      //go to next ',' and replace it with '\0'. read resulting string. set pointer to char after repeat until end of string
      if(strlen(str_ptr) > 9 && strlen(str_ptr) < 15){
        int i;
        for(i = 0; i < 5; i++){
          while(*comma_ptr != ',' && *comma_ptr != '\0'){
            comma_ptr++;
          }
          *comma_ptr = '\0';

          switch(i){
            case 0: last_node_id = atoi(str_ptr);
                    break;
            case 1: next_channel = atoi(str_ptr);
                    break;
            case 2: next_txpower = atoi(str_ptr);
                    break;
            case 3: message.link_param = atoi(str_ptr);
                    break;
            case 4: number_of_rounds = atoi(str_ptr);
                    current_round = 0;
                    break;
            default: printf("ERROR while parsing input\n");
                     break;
          }
          comma_ptr++;
          str_ptr = comma_ptr;
        }

        message.last_node = last_node_id;
        message.next_channel = next_channel;
        message.next_txpower = next_txpower;
      }

    }else if(etimer_expired(&emergency_timer)){
      leds_off(LEDS_ALL);
      printf("rebooting");
      watchdog_reboot();
    }

    read_temperature();

      /* send rounds */
      while(current_round <= number_of_rounds){
        printf("NODE$Round=%i\n",current_round);
        sendmsg();
        round_finished = 0;
        etimer_set(&round_timer, (CLOCK_SECOND/30)*last_node_id);

        /* receive round */
      PROCESS_WAIT_EVENT_UNTIL(round_finished == 1 || etimer_expired(&round_timer) || etimer_expired(&emergency_timer));
      if(round_finished){
        printf("NODE$round finished\n");
        reset_counter = 0;
        if(!recently_reset){
          prep_next_round();
          current_round++;
          }
        }else if(etimer_expired(&round_timer)){
         printf("NODE$round failed\n");
         rounds_failed++;
       }else if(etimer_expired(&emergency_timer)){
         leds_off(LEDS_ALL);
         printf("rebooting");
         watchdog_reboot();
       }

        /* wait for script to check if all nodes answered in critical round */
        if(recently_reset == 1 && round_finished){
          delete_link_data();
          printf("continue or resend ?\n");
          PROCESS_WAIT_EVENT_UNTIL(ev == serial_line_event_message || etimer_expired(&emergency_timer));
          if(ev == serial_line_event_message){
            char* str_ptr = (char*) data;
            if(!strcmp(str_ptr,"resend")){
              recently_reset = 1;
            }else{
              prep_next_round();
              if(current_round == 0){
                current_round++;
              }
              recently_reset = 0;
            }
          }else if(etimer_expired(&emergency_timer)){
            leds_off(LEDS_ALL);
            printf("rebooting");
            watchdog_reboot();
          }
        }

        /* channel and tx reset if rounds do not complete */
        if(rounds_failed >= 4){
          reset_counter++;
          if(current_channel != DEFAULT_CHANNEL || current_txpower != DEFAULT_TX_POWER){
            printf("NODE$reset\n");
            set_channel(DEFAULT_CHANNEL);
            set_txpower(DEFAULT_TX_POWER);
            rounds_failed = 0;
            recently_reset = 1;
          }
        }

        if(reset_counter > 20){
          leds_off(LEDS_ALL);
          printf("rebooting");
          watchdog_reboot();
        }

      }//while num of rounds
      printf("NODE$measurement complete\n");
      recently_reset = 1;
      delete_link_data();

  } // while 1 main loop

  PROCESS_END();
}
