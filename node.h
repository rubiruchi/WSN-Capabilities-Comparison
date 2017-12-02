#ifndef NODE_HEADER
#define NODE_HEADER

#include "contiki.h"

#ifdef OPENMOTE
#include "dev/cc2538-rf.h"
#include "net/netstack.h"
static short node_id = IEEE_ADDR_NODE_ID;
#endif
#ifdef CC2420
#include "dev/cc2420/cc2420.h"
#include "sys/node-id.h"
#endif

#include "net/packetbuf.h"

#include "net/rime/rime.h"
#include "net/rime/rimestats.h"

#include <stdio.h>
#include <stdlib.h>

#include "dev/leds.h"


/*---------------------------------------------------------------------------*/
#define UDP_BROADCAST_PORT 5678      // UDP port of broadcast connection
#define UDP_IP_BUF    ((struct uip_udpip_hdr* ) &uip_buf[UIP_LLH_LEN])
/*---------------------------------------------------------------------------*/
typedef struct msg{
  uint8_t node_id:4;                     //bitfields to keep size as small as possible
  uint8_t last_node:4;
  uint8_t next_channel:5;
  uint8_t next_txpower:5;
  uint8_t link_param:2;                 // 0 for rssi, 1 for lqi, 2 for dropped
  char link_data[MAX_NODES-1];
} msg_t;

static msg_t message;
static struct abc_conn abc;
static int  next_channel, next_txpower, current_channel, current_txpower;
/*---------------------------------------------------------------------------*/
static void abc_recv();
static const struct abc_callbacks abc_call = {abc_recv};

/* delete old link data*/
static void delete_link_data(){
  memset(message.link_data, 0, MAX_NODES-1);
}

/* print link data of a message */
static void print_link_data(msg_t* msg){
  int i;
  #ifdef CC2420
  printf("NODE$%i,%i,%i\n",msg->node_id,cc2420_get_channel(), cc2420_get_txpower());
  #endif
  #ifdef OPENMOTE
  NETSTACK_RADIO.get_value(RADIO_PARAM_CHANNEL,&current_channel);
  NETSTACK_RADIO.get_value(RADIO_PARAM_TXPOWER,&current_txpower);
  printf("NODE$%i,%i,%i\n",msg->node_id,current_channel, current_txpower);
  #endif



  for(i = 0; i < msg->last_node -1; i++){
    if(msg->node_id > i + 1){
      printf("NODE$%i:",i+1);
    }else{
      printf("NODE$%i:",i+2);
    }

    if(msg->link_param == 0){
      printf("RSSI:%i\n",msg->link_data[i] );
    }else if(msg->link_param == 1){
      printf("LQI:%i\n",msg->link_data[i] );
    } else if(msg->link_param == 2){
      printf("Dropped:%i\n",msg->link_data[i] );
    }
  }
}

/* print message, broadcast message, delete message*/
static void sendmsg(){
  leds_toggle(LEDS_RED);
  print_link_data(&message);
  packetbuf_copyfrom(&message,sizeof(message));
  abc_send(&abc);
  delete_link_data();
}

/* fill measured RSSI, LQI, or dropped counter into link data array*/
static void fill_link_data(uint8_t received_node_id, uint8_t last_node, char received_rssi, char received_lqi, uint8_t link_param){

  /* RSSI */
  if(link_param == 0){
    if(node_id > received_node_id){
      message.link_data[received_node_id -1] = received_rssi;   // node IDs start at 1 instead of 0;
    }else{
      message.link_data[received_node_id -2] = received_rssi;  //additional -1: Ignore "own" space in array
    }

    /* LQI */
  }else if(link_param == 1){
    if(node_id > received_node_id){
      message.link_data[received_node_id -1] = received_lqi;
    }else{
      message.link_data[received_node_id -2] = received_lqi;
    }

    /* Dropped */
  } else if(link_param == 2){
    int count = RIMESTATS_GET(badsynch) + RIMESTATS_GET(badcrc) + RIMESTATS_GET(toolong) + RIMESTATS_GET(tooshort) +
    RIMESTATS_GET(sendingdrop) + RIMESTATS_GET(contentiondrop);
    if(node_id > received_node_id){
      message.link_data[received_node_id -1] = count;
    }else{
      message.link_data[received_node_id -2] = count;
    }
  }

  message.last_node = last_node;
}

/*change channel and/or txpower for next round if necessary */
static void prep_next_round(){
  #ifdef CC2420

  if(next_channel != 0 && (cc2420_get_channel() != next_channel)){
    cc2420_set_channel(next_channel);
  }

  if(next_txpower != 0 && (cc2420_get_txpower() != next_channel)){
    cc2420_set_txpower(next_txpower);
  }

#endif
#ifdef OPENMOTE

NETSTACK_RADIO.get_value(RADIO_PARAM_CHANNEL,&current_channel);
NETSTACK_RADIO.get_value(RADIO_PARAM_TXPOWER,&current_txpower);
if(next_channel != 0 && (current_channel != next_channel)){
  NETSTACK_RADIO.set_value(RADIO_PARAM_CHANNEL, next_channel);
}

if(next_txpower != 0 && (current_txpower != next_channel)){
  NETSTACK_RADIO.set_value(RADIO_PARAM_TXPOWER, next_txpower);
}
#endif

}

/*---------------------------------------------------------------------------*/

#endif
