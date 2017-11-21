#include "node.h"
/*---------------------------------------------------------------------------*/
static struct etimer lost_link_timer;
static struct etimer emergency_timer;
static char timer_was_set;
static uint8_t num_of_nodes;
/*---------------------------------------------------------------------------*/
PROCESS(node_process, "node process");
AUTOSTART_PROCESSES(&node_process);
/*---------------------------------------------------------------------------*/
static void tcpip_handler(){
  if(uip_newdata()){
    msg_t received_msg = *(msg_t*) uip_appdata;

    if(node_id > received_msg.last_node){
      return;
    }

    /* indicates that a new round has started */
    if(message.last_node    != received_msg.last_node    ||
      message.next_channel != received_msg.next_channel ||
      message.next_txpower != received_msg.next_txpower ||
      message.link_param   != received_msg.link_param){
        delete_link_data();
      }

      num_of_nodes = received_msg.last_node - COOJA_IDS;
      next_channel = received_msg.next_channel;
      next_txpower = received_msg.next_txpower;
      message.next_channel = next_channel;
      message.next_txpower = next_txpower;
      message.link_param = received_msg.link_param;

      fill_link_data(received_msg.node_id,
      received_msg.last_node,
      packetbuf_attr(PACKETBUF_ATTR_RSSI),
      packetbuf_attr(PACKETBUF_ATTR_LINK_QUALITY),
      received_msg.link_param);

      print_link_data(&received_msg);

      /* upwards sending*/
      if(received_msg.node_id == node_id -1){
        send(num_of_nodes);
        prep_next_round();
      }

        /* lost link detection upwards sending*/
        if(received_msg.node_id < node_id-1){
          int wait_time = (node_id - received_msg.node_id);
          printf("started counter with %ims\n",200*wait_time);
          etimer_set(&lost_link_timer, (CLOCK_SECOND/5) * wait_time); //TODO test if sufficient time
          timer_was_set = 1;
        }

      } //uip_newdata
    }
    /*---------------------------------------------------------------------------*/

    PROCESS_THREAD(node_process, ev, data){
      PROCESS_BEGIN();

      timer_was_set = 0;

      message.node_id = node_id;
      message.last_node    = 0;
      message.next_channel = 0;
      message.next_txpower = 0;
      message.link_param   = 0;
      delete_link_data();

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
          etimer_set(&emergency_timer,CLOCK_SECOND*20);
          etimer_stop(&lost_link_timer);
          timer_was_set = 0;
          tcpip_handler();
        }

        if(etimer_expired(&lost_link_timer) && timer_was_set){
          timer_was_set = 0;
          printf("lost link detected. will continue sending\n");
          send(num_of_nodes);
          prep_next_round();
        }

        if(etimer_expired(&emergency_timer)){
          printf("emergency reset\n");
          cc2420_set_channel(DEFAULT_CHANNEL);
          cc2420_set_txpower(DEFAULT_TX_POWER);
          etimer_reset(&emergency_timer);
        }

      }
      PROCESS_END();
    }
    /*---------------------------------------------------------------------------*/
