#include "node.h"
#include "dev/serial-line.h"
#include "dev/watchdog.h"
#include <stdlib.h>

#ifdef z1
#include "dev/uart0.h"
#else
#include "dev/uart1.h"
#endif

/*---------------------------------------------------------------------------*/
PROCESS(sink_process, "sink process");
AUTOSTART_PROCESSES(&sink_process);
/*---------------------------------------------------------------------------*/
static uint8_t last_node_id;
static struct etimer round_timer;
static int number_of_rounds, current_round;
static uint8_t rounds_failed;
static uint8_t round_finished;
static uint8_t recently_reset;
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

  message.node_id = node_id;
  current_channel = DEFAULT_CHANNEL;
  current_txpower = DEFAULT_TX_POWER;

  abc_open(&abc, DEFAULT_CHANNEL, &abc_call);

  rounds_failed = 0;
  recently_reset = 1; //has to be 1 initially to ensure that all nodes report back in initail round
  number_of_rounds = -1;

  leds_on(LEDS_ALL);
  printf("NODE$Booted\n");
  printf("Enter parameters in the following way:\n <last node>,<channel>,<txpower>,<link param>,<number of rounds>\n");

/* main loop */
  while(1){

    /* handle serial line input */
    PROCESS_WAIT_EVENT_UNTIL(ev == serial_line_event_message);
    if(ev == serial_line_event_message){
      char* str_ptr = (char*) data;
      char* comma_ptr = &(*str_ptr);


      //go to next ',' and replace it with '\0'. read resulting string. set pointer to char after repeat until end of string
      if(strlen(str_ptr) >= 9){
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

    }

    /* send rounds */
    while(current_round <= number_of_rounds){
      printf("NODE$Round=%i\n",current_round);
      sendmsg();
      round_finished = 0;
      etimer_set(&round_timer,(CLOCK_SECOND/20)*last_node_id);

      /* receive round */
    PROCESS_WAIT_EVENT_UNTIL(round_finished == 1 || etimer_expired(&round_timer) || ev == serial_line_event_message);
    if(round_finished){
      printf("NODE$round finished\n");
      if(!recently_reset){
        prep_next_round();
        current_round++;
        }
      }else if(etimer_expired(&round_timer)){
       printf("NODE$round failed\n");
       rounds_failed++;
     }else if(ev == serial_line_event_message){
       char* str_ptr = (char*) data;
       if(!strcmp(str_ptr,"reboot")){
         watchdog_reboot();
       }
     }


      /* wait for script to check if all nodes answered in critical round */
      if(recently_reset == 1 && round_finished){
        delete_link_data();
        printf("continue or resend ?\n");
        PROCESS_WAIT_EVENT_UNTIL(ev == serial_line_event_message);
        char* str_ptr = (char*) data;
        if(!strcmp(str_ptr,"resend")){
          recently_reset = 1;
        }else if(!strcmp(str_ptr,"reboot")){
          watchdog_reboot();
        }else{
          prep_next_round();
          if(current_round == 0){
            current_round++;
          }
          recently_reset = 0;
        }
      }

      if(rounds_failed == 4){
        if(current_channel != DEFAULT_CHANNEL || current_txpower != DEFAULT_TX_POWER){
          printf("NODE$reset\n");
          set_channel(DEFAULT_CHANNEL);
          set_txpower(DEFAULT_TX_POWER);
          rounds_failed = 0;
          recently_reset = 1;
        }
      }

    }//while num of rounds
    printf("NODE$measurement complete\n");
    recently_reset = 1;
    delete_link_data();
  } // while 1 main loop

  PROCESS_END();
}
