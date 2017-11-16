#include "node.h"
#include "dev/button-sensor.h"
#include "dev/serial-line.h"
#include "dev/uart1.h"
#include <stdlib.h>


/*---------------------------------------------------------------------------*/
PROCESS(sink_process, "sink process");
AUTOSTART_PROCESSES(&sink_process);
/*---------------------------------------------------------------------------*/
static uint8_t last_node_id;
static struct etimer round_timer;
static int number_of_rounds;
static uint8_t starting_channel,next_channel,end_channel;
static uint8_t rounds_failed;
static uint8_t round_finished;
/*---------------------------------------------------------------------------*/
static void tcpip_handler(){
  if(uip_newdata()){
    msg_t received_msg = *(msg_t*) uip_appdata;
    int i;

    #ifdef SMALLMSG

    if(received_msg.round_finished){
      if(received_msg.nodeId == node_id+1){
        round_finished = 1;
        number_of_rounds--;
        cc2420_set_channel(next_channel);
      }

      printf("Node %i \n",received_msg.nodeId);
      for(i = 0; i < last_node_id-COOJA_IDS-1; i++){
        if(received_msg.nodeId > i + 1 + COOJA_IDS){
          printf("%i: ",i+1+COOJA_IDS);
        }else{
          printf("%i: ",i+COOJA_IDS+2);
        }

        if(received_msg.link_param == 0){
          printf("RSSI: %i\n",received_msg.link_data[i] );
        }else{
          printf("LQI: %i\n",received_msg.link_data[i] );
        }
      }
    }

    #else
    int j;
    if(received_msg.round_finished && received_msg.nodeId == 1+COOJA_IDS){
      round_finished = 1;
      number_of_rounds--;
      cc2420_set_channel(next_channel);

      for(i = 0; i < last_node_id-COOJA_IDS; i++){
        printf("%i \n",i+1+COOJA_IDS);
        for(j = 0; j < last_node_id-COOJA_IDS-1; j++){
          if(i +1 +COOJA_IDS > j +1 +COOJA_IDS){
            printf("%i: ",j+1+COOJA_IDS);
          }else{
            printf("%i: ",j+COOJA_IDS+2);
          }


          if(received_msg.link_param == 0){
            printf("RSSI: %i\n",received_msg.link_data[i][j]);
          }else{
            printf("LQI: %i\n",received_msg.link_data[i][j] );
          }
        }
      }
    }
    #endif
  }
}
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(sink_process, ev, data){
  PROCESS_BEGIN();
  SENSORS_ACTIVATE(button_sensor);

  uart1_set_input(serial_line_input_byte);  //should be uart0 for z1?
  serial_line_init();

  set_ip_address();
  message.nodeId = node_id;

  if(!join_mcast_group()){
    printf("couldn't join multicast group\n");
    PROCESS_EXIT();
  }

  create_receive_conn();
  create_broadcast_conn();

  rounds_failed = 0;

  while(1){
    printf("Enter parameters in the following way:\n <last node>,<channel>,<link param>,<number of rounds>\n");
    cc2420_set_channel(DEFAULT_CHANNEL);
    PROCESS_WAIT_EVENT_UNTIL(ev == sensors_event || ev == serial_line_event_message);

    if(ev == sensors_event && data == &button_sensor) {
      printf("Button pressed\n");
      last_node_id = 5;                                 //change to ID of last node
      message.last_node = last_node_id;
      message.next_channel = 0;
      message.round_finished = 0;
      message.link_param = 0;                           //change to 0 for RSSI, 1 for LQI
      number_of_rounds = 2;
    }

    if(ev == serial_line_event_message){
      printf("received line: %s\n",(char*) data);
      char* str_ptr = (char*) data;
      char* comma_ptr = &(*str_ptr);

      int i;
      for(i = 0; i < 4; i++){
        while(*comma_ptr != ',' && *comma_ptr != '\0'){
          comma_ptr++;
        }
        *comma_ptr = '\0';

        switch(i){
          case 0: last_node_id = atoi(str_ptr);
          break;
          case 1: next_channel = atoi(str_ptr);
          break;
          case 2: message.link_param = atoi(str_ptr);
          break;
          case 3: number_of_rounds = atoi(str_ptr);
          break;
          default: printf("something went wrong while parsing input\n");
          break;
        }

        comma_ptr++;
        str_ptr = comma_ptr;
      }

      message.last_node = last_node_id;
      message.round_finished = 0;

      /* if using default channel */
      if(next_channel == 0){
        next_channel = DEFAULT_CHANNEL;
      }
      /* if channel switching*/
      if(next_channel != 0 && next_channel != 26){
        number_of_rounds = number_of_rounds +1;
      }

      printf("last_node_id : %d\n",message.last_node);
      printf("starting_channel: %d\n",starting_channel);
      printf("end_channel: %d\n",end_channel);
      printf("link param: %d\n",message.link_param);
      printf("num of rounds: %d\n",number_of_rounds);
    }

    /* send rounds */
    while(number_of_rounds){
      printf("round: %i\n",number_of_rounds);
      if(number_of_rounds == 1){
        message.next_channel = DEFAULT_CHANNEL;
      }else{
        message.next_channel = next_channel;
      }
      send(last_node_id -COOJA_IDS);
      etimer_set(&round_timer,CLOCK_SECOND*5);
      round_finished = 0;

      /* receive round */
      while(1){
        PROCESS_WAIT_EVENT();
        if(ev == tcpip_event){
          tcpip_handler();
          if(round_finished){
            break;  //to send next rounds init msg
          }

        }else if(etimer_expired(&round_timer)){ //will expire after 5s or by stop() when round completes
          rounds_failed++;
          break; //to resend current rounds init msg
        }
      }

      if(rounds_failed == 4){
        printf("emergency channel reset\n");
        cc2420_set_channel(DEFAULT_CHANNEL);
        rounds_failed = 0;
      }

    }//while num of rounds
    printf("finished\n");
  } // while 1

  PROCESS_END();
}
