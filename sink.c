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
/*---------------------------------------------------------------------------*/
static void switch_channel(){
  if(starting_channel != end_channel){     // if channels should be switched at all
    if(next_channel <= end_channel){
      cc2420_set_channel(next_channel);
      next_channel++;
    }
    if(next_channel == end_channel+1){ // if this switch is the last for this round
      if(number_of_rounds-1 != 1){           // if this is not the last round
        next_channel = starting_channel;
      }else{                                 // if this is the last round
        printf("setting chan to default\n");
        next_channel = DEFAULT_CHANNEL;
      }
    }
  }
}

static void tcpip_handler(){
  if(uip_newdata()){
    msg_t received_msg = *(msg_t*) uip_appdata;
    int i;

    #ifdef SMALLMSG

    if(received_msg.round_finished){
      etimer_stop(&round_timer);
      switch_channel();
      number_of_rounds--;

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
      etimer_stop(&round_timer);
      switch_channel();
      number_of_rounds--;

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

  while(1){
    cc2420_set_channel(DEFAULT_CHANNEL);
    PROCESS_WAIT_EVENT();


    if(ev == sensors_event && data == &button_sensor) {
      printf("Button pressed\n");
      last_node_id = 5;                                 //change to ID of last node
      message.last_node = last_node_id;
      message.next_channel = 0;
      message.round_finished = 0;
      message.link_param = 0;                           //change to 0 for RSSI, 1 for LQI
      number_of_rounds = 2;
    }

    //will be covered by script
    // printf("Last node: Node id of the last node in the network\n
    //         Starting channel/End channel: range of channels. enter 0 to only use default channel 26\n
    //         Link param:  0 for RSSI, 1 for LQI\n
    //         Number of rounds: how many rounds should be done\n
    printf("Enter parameters in the following way:\n <last node>,<starting channel>,<end channel>,<link param>,<number of rounds>\n");
    if(ev == serial_line_event_message){
      printf("received line: %s\n",(char*) data);
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
          case 1: starting_channel = atoi(str_ptr);
                  break;
          case 2: end_channel = atoi(str_ptr);
                  break;
          case 3: message.link_param = atoi(str_ptr);
                  break;
          case 4: number_of_rounds = atoi(str_ptr);
                  break;
          default: printf("something went wrong while parsing input\n");
                  break;
        }

        comma_ptr++;
        str_ptr = comma_ptr;
      }

      message.last_node = last_node_id;
      message.round_finished = 0;
      next_channel = starting_channel;

      /* if using default channel */
      if(starting_channel == 0 && end_channel == 0){
        starting_channel = DEFAULT_CHANNEL;
        end_channel = DEFAULT_CHANNEL;
        next_channel = 0;
      }
      /* if channel switching*/
      if(end_channel != starting_channel){
        int diff = end_channel+1 - starting_channel;     //+1 because e.g. 24 to 26 are 3 channels not 2
        number_of_rounds = number_of_rounds * diff +1;
      }


      printf("last_node_id : %d\n",message.last_node);
      printf("starting_channel: %d\n",starting_channel);
      printf("end_channel: %d\n",end_channel);
      printf("link param: %d\n",message.link_param);
      printf("num of rounds: %d\n",number_of_rounds);
    }

    while(number_of_rounds){
      printf("round: %i\n",number_of_rounds);
      message.next_channel = next_channel;
      send(last_node_id -COOJA_IDS);
      etimer_set(&round_timer,CLOCK_SECOND*5);

      while(1){
      PROCESS_WAIT_EVENT();
      if(ev == tcpip_event){
        tcpip_handler();
      }
      if(etimer_expired(&round_timer)){ //will expire after 5s or by stop() when round completes
        break;
      }
    }

    }


  }
  PROCESS_END();
}
