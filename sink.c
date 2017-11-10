#include "node.h"
#include "dev/button-sensor.h"
#include "dev/serial-line.h"
#include "dev/uart1.h"

/*---------------------------------------------------------------------------*/
PROCESS(sink_process, "sink process");
AUTOSTART_PROCESSES(&sink_process);
/*---------------------------------------------------------------------------*/
static uint8_t last_node_id;
/*---------------------------------------------------------------------------*/
static void tcpip_handler(){
  if(uip_newdata()){
    msg_t received_msg = *(msg_t*) uip_appdata;
    int i;

    #ifdef SMALLMSG

    if(received_msg.round_finished){
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
    PROCESS_WAIT_EVENT();


    if(ev == sensors_event && data == &button_sensor) {
      printf("Button pressed\n");
      last_node_id = 5;                                 //change to ID of last node
      message.last_node = last_node_id;
      message.next_channel = 0;
      message.round_finished = 0;
      message.link_param = 0;                           //change to 0 for RSSI, 1 for LQI
      send(last_node_id -COOJA_IDS);
    }

    //will be covered by script
    // printf("Last node: Node id of the last node in the network\n
    //         Starting channel/End channel: range of channels. enter 0 to only use default channel 26\n
    //         Link param:  Enter parameters in the following way:\n <last node>,<starting channel>,<end channel>,<link param>\n");
    if(ev == serial_line_event_message){
      printf("received line: %s\n",(char*) data);

      //TODO FINISH INPUT FOR MSG


    }
    

    if(ev == tcpip_event){
      tcpip_handler();
    }
  }
  PROCESS_END();
}
