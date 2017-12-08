#include "node.h"
#include "dev/serial-line.h"
#include "rf-core/rf-ble.h"
#ifdef z1
#include "dev/uart0.h"
#else
#include "dev/uart1.h"
#endif

#include <stdlib.h>

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

    fill_link_data(received_msg.node_id,
      received_msg.last_node,
      packetbuf_attr(PACKETBUF_ATTR_RSSI),
      packetbuf_attr(PACKETBUF_ATTR_LINK_QUALITY),
      received_msg.link_param);

      print_link_data(&received_msg);

      if(received_msg.node_id == last_node_id){
        rounds_failed = 0;
        if(!recently_reset){
          current_round++;
        }
        round_finished = 1;
        recently_reset = 0;
        prep_next_round();
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

  abc_open(&abc, 26, &abc_call);

  rounds_failed = 0;
  recently_reset = 0;
  number_of_rounds = -1;

  leds_on(LEDS_ALL);
  printf("Enter parameters in the following way:\n <last node>,<channel>,<txpower>,<link param>,<number of rounds>\n");
  while(1){
    PROCESS_WAIT_EVENT_UNTIL(ev == serial_line_event_message);

    printf("ble is active: %i\n",rf_ble_is_active());

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
      sendmsg();
      round_finished = 0;
      etimer_set(&round_timer,(CLOCK_SECOND/10)*last_node_id);

      /* receive round */
    PROCESS_WAIT_EVENT_UNTIL(round_finished == 1 || etimer_expired(&round_timer));
    if(round_finished){
        printf("NODE$round finished\n");
      }else if(etimer_expired(&round_timer)){
       printf("NODE$round failed\n");
       rounds_failed++;
      }


      /* wait for script to check if all nodes answered in first round */
      if(current_round == 1 && round_finished){
        delete_link_data();
        printf("continue or resend ?\n");
        PROCESS_WAIT_EVENT_UNTIL(ev == serial_line_event_message);
        char* str_ptr = (char*) data;
        if(!strcmp(str_ptr,"resend")){
          current_round--;
        }
      }

      if(rounds_failed == 4){
        printf("NODE$reset\n");
        set_channel(DEFAULT_CHANNEL);
        set_txpower(DEFAULT_TX_POWER);
        rounds_failed = 0;
        recently_reset = 1;
      }

    }//while num of rounds
    printf("NODE$measurement finished\n");
    delete_link_data();
  } // while 1

  PROCESS_END();
}
