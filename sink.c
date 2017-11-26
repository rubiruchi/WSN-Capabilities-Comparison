#include "node.h"
#include "dev/serial-line.h"
#include "dev/uart1.h"
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
/*---------------------------------------------------------------------------*/
static void tcpip_handler(){
  if(uip_newdata()){
    msg_t received_msg = *(msg_t*) uip_appdata;

    fill_link_data(received_msg.node_id,
      received_msg.last_node,
      packetbuf_attr(PACKETBUF_ATTR_RSSI),
      packetbuf_attr(PACKETBUF_ATTR_LINK_QUALITY),
      received_msg.link_param);

      print_link_data(&received_msg);

      if(received_msg.node_id == last_node_id){
        rounds_failed = 0;
        current_round++;
        round_finished = 1;
        prep_next_round();
      }
  }
}
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(sink_process, ev, data){
  PROCESS_BEGIN();
  #if TARGET == z1
  uart1_set_input(serial_line_input_byte);
  #else
  uart1_set_input(serial_line_input_byte);
  #endif
  serial_line_init();

  set_ip_address();
  message.node_id = node_id;

  if(!join_mcast_group()){
    printf("couldn't join multicast group\n");
    PROCESS_EXIT();
  }

  create_receive_conn();
  create_broadcast_conn();

  rounds_failed = 0;

  leds_on(LEDS_GREEN);
  leds_on(LEDS_BLUE);

  printf("Enter parameters in the following way:\n <last node>,<channel>,<txpower>,<link param>,<number of rounds>\n");
  while(1){
    PROCESS_WAIT_EVENT_UNTIL(ev == serial_line_event_message);

    if(ev == serial_line_event_message){
      char* str_ptr = (char*) data;
      char* comma_ptr = &(*str_ptr);

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

    /* send rounds */
    while(current_round <= number_of_rounds){
      send();
      etimer_set(&round_timer,(CLOCK_SECOND/4)*last_node_id+1);
      round_finished = 0;

      /* receive round */
      while(1){
        PROCESS_WAIT_EVENT();
        if(ev == tcpip_event){
          tcpip_handler();
          if(round_finished){
            printf("NODE$round finished\n");
            break;  //number_of_rounds will have decremented
          }
        }else if(etimer_expired(&round_timer)){
          printf("NODE$round failed\n");
          rounds_failed++;
          break; //number_of_rounds will not have decremented
        }
      }

      /* wait for skript to check if all nodes answered in first round */
      if(current_round == 1 && round_finished){
        PROCESS_WAIT_EVENT_UNTIL(ev == serial_line_event_message);
        char* str_ptr = (char*) data;
        if(!strcmp(str_ptr,"resend")){
          current_round--;
        }
      }

      if(rounds_failed == 4){
        printf("emergency channel&txpower reset\n");
        cc2420_set_channel(DEFAULT_CHANNEL);
        cc2420_set_txpower(DEFAULT_TX_POWER);
        rounds_failed = 0;
      }

    }//while num of rounds
    printf("NODE$measurement finished\n");
    delete_link_data();
  } // while 1

  PROCESS_END();
}
