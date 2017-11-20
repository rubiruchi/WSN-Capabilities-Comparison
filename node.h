#ifndef NODE_HEADER
#define NODE_HEADER
#include "contiki.h"
#include "contiki-lib.h"
#include "contiki-net.h"
#include "sys/node-id.h"
#include "dev/cc2420/cc2420.h"

#include "net/packetbuf.h"

#include "net/ipv6/multicast/uip-mcast6.h"
#include "net/ipv6/multicast/uip-mcast6-engines.h"
#include "net/ip/uip.h"
#include "net/ipv6/uip-ds6.h"
#include "net/ip/uip-udp-packet.h"
#include "net/ip/uip-debug.h"

#include <stdio.h>

#include "dev/leds.h"

#include "net/rime/rimestats.h"

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
static struct uip_udp_conn* broadcast_conn;
static struct uip_udp_conn* receive_conn;
static uip_ip6addr_t mcast_addr;
static uip_ip6addr_t addr;
static int  next_channel, next_txpower;
/*---------------------------------------------------------------------------*/
static void send(uint8_t num_of_nodes){
  printf("sending: %i, lastnode: %i, nxtchan: %i, nxttx: %i, linkpar: %i\n",
  message.node_id,
  message.last_node,
  message.next_channel,
  message.next_txpower,
  message.link_param);
  uip_udp_packet_send(broadcast_conn, &message, sizeof(message));
  // printf("sendingdropI:%lu\n",RIMESTATS_GET(sendingdrop));
  // printf("contentiondropI:%lu\n",RIMESTATS_GET(contentiondrop));
}

static void tcpip_handler();

static void create_broadcast_conn(){
  broadcast_conn = udp_new(&mcast_addr,UIP_HTONS(UDP_BROADCAST_PORT),NULL);
}

static void create_receive_conn(){
  receive_conn = udp_new(NULL, UIP_HTONS(0), 0);
  udp_bind(receive_conn, UIP_HTONS(UDP_BROADCAST_PORT));
}

static void set_ip_address(){
  /* set global ip adress */
  uip_ip6addr(&addr, UIP_DS6_DEFAULT_PREFIX, 0, 0, 0, 0, 0, 0, 0);
  uip_ds6_set_addr_iid(&addr, &uip_lladdr);
  uip_ds6_addr_add(&addr, 0, ADDR_AUTOCONF);
}

static uip_ds6_maddr_t* join_mcast_group(void){
  /*
  * IPHC will use stateless multicast compression for this destination
  * (M=1, DAC=0), with 32 inline bits (1E 89 AB CD)
  */
  uip_ip6addr(&mcast_addr, 0xFF01,0,0,0,0,0,0x89,0xABCD);

  return uip_ds6_maddr_add(&mcast_addr);
}

/* print link data of a message */
static void print_link_data(msg_t* msg){
  int i;
  printf("Node %i \n",msg->node_id);
  for(i = 0; i < msg->last_node -COOJA_IDS; i++){
    if(msg->node_id > i + COOJA_IDS){
      printf("%i: ",i+COOJA_IDS);
    }else{
      printf("%i: ",i+COOJA_IDS+1);
    }

    if(msg->link_param == 0){
      printf("RSSI: %i\n",msg->link_data[i] );
    }else if(msg->link_param == 1){
      printf("LQI: %i\n",msg->link_data[i] );
    } else if(msg->link_param == 2){
      printf("Dropped: %i\n",msg->link_data[i] );
    }
  }
}

/* fill measured RSSI, LQI, or dropped counter into link data array*/
static void fill_link_data(uint8_t received_node_id, uint8_t last_node, char received_rssi, char received_lqi, uint8_t link_param){

  /* RSSI */
  if(link_param == 0){
    if(node_id > received_node_id){
      message.link_data[received_node_id -COOJA_IDS] = received_rssi;   // -COOJA_IDS: cooja IDs start at 1 instead of 0;
    }else{
      message.link_data[received_node_id -COOJA_IDS -1] = received_rssi;  //additional -1: Ignore "own" space in array
    }

    /* LQI */
  }else if(link_param == 1){
    if(node_id > received_node_id){
      message.link_data[received_node_id -COOJA_IDS] = received_lqi;
    }else{
      message.link_data[received_node_id -COOJA_IDS -1] = received_lqi;
    }

    /* Dropped */
  } else if(link_param == 2){
    int count = RIMESTATS_GET(badsynch) + RIMESTATS_GET(badcrc) + RIMESTATS_GET(toolong) + RIMESTATS_GET(tooshort);
    if(node_id > received_node_id){
      message.link_data[received_node_id -COOJA_IDS] = count;
    }else{
      message.link_data[received_node_id -COOJA_IDS -1] = count;
    }
  }

  message.last_node = last_node;
}

/*---------------------------------------------------------------------------*/

#endif
