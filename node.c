#include "node.h"


/*---------------------------------------------------------------------------*/
static struct etimer lost_link_timer;
static char timer_was_set;
static char is_first_msg;
/*---------------------------------------------------------------------------*/
PROCESS(node_process, "node process");
AUTOSTART_PROCESSES(&node_process);
/*---------------------------------------------------------------------------*/

static void fill_link_data(uint8_t received_node_id, uint8_t last_node, char received_rssi, char received_lqi, uint8_t link_param){

  /* do not take link data from sink node(node_id: 0) */
  if((received_node_id -1 -COOJA_IDS) >= 0){
    /* RSSI */
    if(link_param == 0){
      #ifdef SMALLMSG
      printf("IN SMALL MSG!\n");
      message.link_data[received_node_id-1-COOJA_IDS] = received_rssi;
      #else
      message.link_data[node_id-1-COOJA_IDS][received_node_id-1-COOJA_IDS] = received_rssi;
      #endif
    }else{
      /* LQI */
      if(link_param == 1){
        #ifdef SMALLMSG
        printf("IN SMALL MSG!\n");
        message.link_data[received_node_id-1-COOJA_IDS] = received_lqi;
        #else
        message.link_data[node_id-1-COOJA_IDS][received_node_id-1-COOJA_IDS] = received_lqi;
        #endif
      }
    }
  }
  message.last_node = last_node;

  // if(1){
  //   printf("my msg is: ");
  //   int i;
  //   int j;
  //     for(i = 0; i < last_node-COOJA_IDS; i++){
  //       printf("%i \n",i+1+COOJA_IDS);
  //       for(j = 0; j < last_node-COOJA_IDS; j++){
  //         printf("%i: :",j+1+COOJA_IDS);
  //         if(message.link_param == 0){
  //           printf("RSSI: %i\n",message.link_data[i][j] );
  //         }else{
  //           printf("LQI: %i\n",message.link_data[i][j] );
  //         }
  //       }
  //     }
  //   }
}

static void tcpip_handler(){
  if(uip_newdata()){
    msg_t received_msg = *(msg_t*) uip_appdata;

     int i;
    // int j;
    #ifndef SMALLMSG //Sending and modifying one packet to get data to sink
    for(i = 0; i < received_msg.last_node -COOJA_IDS;i++){
      if((i+1+COOJA_IDS) != node_id){
        // printf("copying to msg[%i]: ",i);
        // for(j = 0; j < received_msg.last_node -COOJA_IDS;j++){
        //   printf("%i, ",message.link_data[i][j]);
        // }
        // printf(" from recvmsg[%i]: ",i);
        // for(j = 0; j < received_msg.last_node -COOJA_IDS;j++){
        //   printf("%i, ",received_msg.link_data[i][j]);
        // }
        // printf("\n");

        memcpy(&message.link_data[i][0],&received_msg.link_data[i][0], (received_msg.last_node -COOJA_IDS) );
      }
    }
    #endif

      if(!received_msg.round_finished){

        printf("Package from: %i , RSSI: %i , LQI: %i \n",received_msg.nodeId,
        PACKETBUF_ATTR_RSSI, PACKETBUF_ATTR_LINK_QUALITY);


      //   int j;
      //   if(1){
      //   printf("received msg is: ");
      //   for(i = 0; i < received_msg.last_node -COOJA_IDS; i++){
      //     printf("%i \n",i+1+COOJA_IDS);
      //     for(j = 0; j < received_msg.last_node -COOJA_IDS; j++){
      //       printf("%i: :",j+1+COOJA_IDS);
      //       if(received_msg.link_param == 0){
      //         printf("RSSI: %i\n",received_msg.link_data[i][j] );
      //       }else{
      //         printf("LQI: %i\n",received_msg.link_data[i][j] );
      //       }
      //     }
      //   }
      // }

        fill_link_data(received_msg.nodeId,
          received_msg.last_node,
          packetbuf_attr(PACKETBUF_ATTR_RSSI),
          packetbuf_attr(PACKETBUF_ATTR_LINK_QUALITY),
          received_msg.link_param);

        /* upwards sending*/
        if(received_msg.nodeId == node_id -1){
          message.round_finished =  0;
          send();

          /* case last node hast to initiate downwards sending */
          if(received_msg.last_node == node_id){
            message.round_finished = 1;
            send();
          }

          /* case last node isn't reachable and penultimate node hast to initiate downwards sending */
          if(received_msg.last_node -1 == node_id){
            message.round_finished = 1;
            printf("started counter for last\n");
            etimer_set(&lost_link_timer, CLOCK_SECOND*1);
            timer_was_set = 1;
          }

        }

        /* lost link detection upwards sending*/
        if(received_msg.nodeId == node_id -2){
          printf("started counter for upwards\n");
          etimer_set(&lost_link_timer, CLOCK_SECOND*1);
          timer_was_set = 1;
          //if penultimate node isn't reachable, last node still finishes round
          if(received_msg.last_node == node_id){
            message.round_finished = 1;
          }
        }

      }else{
        /* downwards */
        if(received_msg.nodeId == node_id +1){
          message.round_finished = 1;
          if(received_msg.next_channel != 0){
            cc2420.set_channel(next_channel);
          }
          send();
          #ifdef SMALLMSG
          memset(message.link_data,0,sizeof(message.link_data[0]) * MAX_NODES);
          #else
          memset(message.link_data,0,sizeof(message.link_data[0]) * MAX_NODES * MAX_NODES);
          #endif
        }

        /* lost link detection downwards sending*/
        if(received_msg.nodeId == node_id +2){
          message.round_finished = 1;
          printf("started counter for downwards\n");
          etimer_set(&lost_link_timer, CLOCK_SECOND*1);
          timer_was_set = 1;
        }

      }

    }
  }
  /*---------------------------------------------------------------------------*/

  PROCESS_THREAD(node_process, ev, data){
    PROCESS_BEGIN();

    timer_was_set = 0;
    is_first_msg = 1;
    message.nodeId = node_id;

    printf("uip appdata size: %i\n",UIP_APPDATA_SIZE);
    printf("packetbuf size: %i\n",PACKETBUF_SIZE);
    //printf("packetbuf hdr size: %i\n",PACKETBUF_HDR_SIZE);
    printf("message size: %i\n", sizeof(message));

    set_ip_address();

    if(!join_mcast_group()){
      printf("couldn't join multicast group\n");
      PROCESS_EXIT();
    }

    create_receive_conn();
    create_broadcast_conn();

    while(1){
      PROCESS_WAIT_EVENT();

      if(ev == tcpip_event){
        etimer_stop(&lost_link_timer);
        timer_was_set = 0;
        tcpip_handler();
      }

      if(etimer_expired(&lost_link_timer) && timer_was_set){
        printf("lost link detected. will continue sending\n");
        send();
      }

    }
    PROCESS_END();
  }
  /*---------------------------------------------------------------------------*/
