#include "node.h"

/*---------------------------------------------------------------------------*/
static struct etimer lost_link_timer;
static char up_timer_was_set,down_timer_was_set;
static uint8_t num_of_nodes, next_channel;
/*---------------------------------------------------------------------------*/
PROCESS(node_process, "node process");
AUTOSTART_PROCESSES(&node_process);
/*---------------------------------------------------------------------------*/
  /* delete old link data*/
static void delete_link_data(){
  printf("deleting\n");
  #ifdef SMALLMSG
  memset(message.link_data,0, MAX_NODES-1);
  #else
  memset(message.link_data,0, MAX_NODES * MAX_NODES-1);
  #endif
}

/*change channel for next round if neccessary */
static void change_channel(){
  if(next_channel != 0){
    printf("setting channel to %i\n",next_channel);
    cc2420_set_channel(next_channel);
  }
}
/* fill measured RSSI or LQI into messages link data array*/
static void fill_link_data(uint8_t received_node_id, uint8_t last_node, char received_rssi, char received_lqi, uint8_t link_param){

  if((received_node_id -1 -COOJA_IDS) >= 0){   // do not take link data from sink node(node_id == 0)

    /* RSSI */
    if(link_param == 0){
      if(node_id > received_node_id){ //-1: Array Index(nodes start at 1); -COOJA_IDS: cooja IDs start at 2 instead of 1;
        #ifdef SMALLMSG
        message.link_data[received_node_id-1-COOJA_IDS] = received_rssi;
        #else
        message.link_data[node_id-1-COOJA_IDS][received_node_id -1 -COOJA_IDS] = received_rssi;
        #endif
      }else{                         //additional -1: Ignore "own" space in array to avoid diagonal of 0
      #ifdef SMALLMSG
      message.link_data[received_node_id -1 -COOJA_IDS -1] = received_rssi;
      #else
      message.link_data[node_id -1 -COOJA_IDS][received_node_id -1 -COOJA_IDS -1] = received_rssi;
      #endif
    }

  }else{

    /* LQI */
    if(node_id > received_node_id){ //-1: Array Index; -COOJA_IDS: cooja IDs start at 1 instead of 0;
      #ifdef SMALLMSG
      message.link_data[received_node_id -1 -COOJA_IDS] = received_lqi;
      #else
      message.link_data[node_id -1 -COOJA_IDS][received_node_id -1 -COOJA_IDS] = received_lqi;
      #endif
    }else{                          //additional -1: Ignore "own" space in array to avoid diagonal of 0
    #ifdef SMALLMSG
    message.link_data[received_node_id -1 -COOJA_IDS -1] = received_lqi;
    #else
    message.link_data[node_id -1 -COOJA_IDS][received_node_id -1 -COOJA_IDS -1] = received_lqi;
    #endif
  }
}
}
message.last_node = last_node;
}

static void tcpip_handler(){
  if(uip_newdata()){
    msg_t received_msg = *(msg_t*) uip_appdata;

    num_of_nodes = received_msg.last_node - COOJA_IDS;
    next_channel = received_msg.next_channel;

    #ifndef SMALLMSG
    /*copy received data */
    int i;
    for(i = 0; i < num_of_nodes;i++){
      if((i+1+COOJA_IDS) != node_id){
        memcpy(&message.link_data[i][0],&received_msg.link_data[i][0], num_of_nodes -1);
      }
    }
    #endif

    if(!received_msg.round_finished){
      //  printf("Package from: %i , RSSI: %d , LQI: %d , sizeof msg: %d \n",received_msg.nodeId,
      //  packetbuf_attr(PACKETBUF_ATTR_RSSI),
      //  packetbuf_attr(PACKETBUF_ATTR_LINK_QUALITY),
      //  uip_len);

      fill_link_data(received_msg.nodeId,
        received_msg.last_node,
        packetbuf_attr(PACKETBUF_ATTR_RSSI),
        packetbuf_attr(PACKETBUF_ATTR_LINK_QUALITY),
        received_msg.link_param);

        /* upwards sending*/
        if(received_msg.nodeId == node_id -1){
          message.round_finished =  0;
          send(num_of_nodes);

          /* case last node hast to initiate downwards sending */
          if(received_msg.last_node == node_id){
            message.round_finished = 1;
            send(num_of_nodes);
            delete_link_data();
            change_channel(next_channel);
          }

          /* case last node isn't reachable and penultimate node hast to initiate downwards sending */
          if(received_msg.last_node -1 == node_id){
            printf("started counter for last\n");
            etimer_set(&lost_link_timer, CLOCK_SECOND*1);
            down_timer_was_set = 1;
          }
        } // message from node_id-1

        /* lost link detection upwards sending*/
        if(received_msg.nodeId == node_id -2){
          printf("started counter for upwards\n");
          etimer_set(&lost_link_timer, CLOCK_SECOND*1);
          up_timer_was_set = 1;
          //if penultimate node isn't reachable, last node still finishes round
          if(received_msg.last_node == node_id){
            down_timer_was_set = 1;
          }
        }

      }else{                      //if round is finished
        /* downwards */
        if(received_msg.nodeId == node_id +1){
          message.round_finished = 1;
          send(num_of_nodes);
          delete_link_data();
          change_channel(next_channel);
        }

        /* lost link detection downwards sending*/
        if(received_msg.nodeId == node_id +2){
          printf("started counter for downwards\n");
          etimer_set(&lost_link_timer, CLOCK_SECOND*1);
          down_timer_was_set = 1;
        }
      }

    } //uip_newdata
  }
  /*---------------------------------------------------------------------------*/

  PROCESS_THREAD(node_process, ev, data){
    PROCESS_BEGIN();

    up_timer_was_set = 0;
    down_timer_was_set = 0;
    message.nodeId = node_id;

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
        up_timer_was_set = 0;
        down_timer_was_set = 0;
        tcpip_handler();
      }

      if(etimer_expired(&lost_link_timer) && (up_timer_was_set || down_timer_was_set)){
        if(up_timer_was_set){
          up_timer_was_set = 0;
          message.round_finished = 0;
          printf("lost link detected. will continue sending upwards\n");
          send(num_of_nodes);
        }
        if(down_timer_was_set){
          down_timer_was_set = 0;
          message.round_finished = 1;
          printf("lost link detected. will continue sending downwards\n");
          send(num_of_nodes);
          delete_link_data();
          change_channel(next_channel);
        }
      }

    }
    PROCESS_END();
  }
  /*---------------------------------------------------------------------------*/
