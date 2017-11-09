#include "node.h"
#include "dev/button-sensor.h"
#include "dev/serial-line.h"

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
      for(i = 0; i < last_node_id-COOJA_IDS; i++){
        printf("%i: ",i+1+COOJA_IDS);
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
        for(j = 0; j < last_node_id-COOJA_IDS; j++){
          printf("%i: :",j+1+COOJA_IDS);
          if(received_msg.link_param == 0){
            printf("RSSI: %i\n",received_msg.link_data[i][j] );
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

  #ifdef COOJA
  SENSORS_ACTIVATE(button_sensor);
  #else
  serial_line_init();
  #endif

  set_ip_address();

  if(!join_mcast_group()){
    printf("couldn't join multicast group\n");
    PROCESS_EXIT();
  }

  create_receive_conn();
  create_broadcast_conn();

while(1){
  PROCESS_WAIT_EVENT();

#ifdef COOJA

  if(ev == sensors_event && data == &button_sensor) {
    printf("Button pressed\n");
    message.nodeId = node_id;
    last_node_id = 4;                                 //change to ID of last node
    message.last_node = last_node_id;
    message.round_finished = 0;
    next_channel = 0;
    message.link_param = 0;                           //change to 0 for RSSI, 1 for LQI
    memset(message.link_data,0,sizeof(message.link_data[0]) * last_node_id);
    send();
  }

#else

  if(ev == serial_line_event_message){
    printf("a serial line event, really?\n");
  }

#endif
    if(ev == tcpip_event){
      tcpip_handler();
    }
}
  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
