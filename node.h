#ifndef NODE_HEADER
#define NODE_HEADER

#include "contiki.h"
#include "dev/watchdog.h"
#include "net/netstack.h"
#include "net/packetbuf.h"
#include "dev/radio.h"
#include "net/rime/rime.h"
#include "net/rime/rimestats.h"
#include <stdio.h>
#include <stdlib.h>
#include "dev/leds.h"

#if defined(sky) || defined(z1) || defined(sensortag)
#include "sys/node-id.h"
#endif

#if defined(sensortag) && defined(NID)
#undef IEEE_ADDR_CONF_ADDRESS
#define IEEE_ADDR_CONF_ADDRESS                {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, NID}
#endif

#if defined(sky) || defined(z1)
#include "dev/cc2420/cc2420.h"
#endif

#ifdef openmote
#ifdef IEEE_ADDR_NODE_ID
static unsigned short node_id = IEEE_ADDR_NODE_ID;
#else
static unsigned short node_id = 0;
#endif
#endif
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
  signed char link_data[MAX_NODES-1];
} msg_t;

static msg_t message;
static struct abc_conn abc;
static radio_value_t  next_channel, next_txpower, current_channel, current_txpower;
/*---------------------------------------------------------------------------*/
static void abc_recv();
static const struct abc_callbacks abc_call = {abc_recv};

static void delete_link_data(){
  memset(message.link_data, 0, MAX_NODES-1);
}

static int get_channel(){
  NETSTACK_RADIO.get_value(RADIO_PARAM_CHANNEL,&current_channel);
  return current_channel;
}

/* sets radio channel and opens new abc connection to specified channel */
static void set_channel(int channel){
  abc_close(&abc);
  abc_open(&abc,channel,&abc_call);
  NETSTACK_RADIO.set_value(RADIO_PARAM_CHANNEL, channel);
}

static int get_txpower(){
  /* get/set txpower somehow not working for cc2420 without directly using radio driver */
  #if defined(sky) || defined(z1)
  return cc2420_get_txpower();
  #endif

  NETSTACK_RADIO.get_value(RADIO_PARAM_TXPOWER,&current_txpower);
  return current_txpower;
}

static void set_txpower(int power){
  /* get/set txpower somehow not working for cc2420 without directly using radio driver */
  #if defined(sky) || defined(z1)
  current_txpower = power;
  cc2420_set_txpower(power);
  #endif

  NETSTACK_RADIO.set_value(RADIO_PARAM_TXPOWER, power);
}

/* print link data of a message */
static void print_link_data_only_sink(msg_t* msg){
  printf("NODE$%i:%i:%i:",msg->node_id,get_channel(), get_txpower());
  printf("1:");
  if(msg->link_param == 0){
    printf("%i:RSSI\n",msg->link_data[0] );
  }else if(msg->link_param == 1){
    printf("%i:LQI\n",msg->link_data[0] );
  } else if(msg->link_param == 2){
    printf("%i:Dropped\n",msg->link_data[0] );
  }
}

/* print link data of a message */
static void print_link_data(msg_t* msg){
  int i;
  for(i = 0; i < msg->last_node -1; i++){
    printf("NODE$%i:%i:%i:",msg->node_id,get_channel(), get_txpower());
    if(msg->node_id > i + 1){
      printf("%i:",i+1);
    }else{
      printf("%i:",i+2);
    }

    if(msg->link_param == 0){
      printf("%i:RSSI\n",msg->link_data[i] );
    }else if(msg->link_param == 1){
      printf("%i:LQI\n",msg->link_data[i] );
    } else if(msg->link_param == 2){
      printf("%i:Dropped\n",msg->link_data[i] );
    }
  }
}

/* broadcast message, print message, delete message*/
static void sendmsg(){
  leds_toggle(LEDS_RED);
  packetbuf_copyfrom(&message,sizeof(message));
  abc_send(&abc);
  print_link_data(&message);
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
  if(next_channel != 0 && (get_channel() != next_channel)){
    set_channel(next_channel);
  }

  if(next_txpower != 0 && (get_txpower() != next_txpower)){
    set_txpower(next_txpower);
  }
}

/*---------------------------------------------------------------------------*/

#endif
