#ifndef NODE_HEADER
#define NODE_HEADER
#include "contiki.h"
#include "contiki-lib.h"
#include "contiki-net.h"
#include "sys/node-id.h"

#include "net/packetbuf.h"

#include "net/ipv6/multicast/uip-mcast6.h"
#include "net/ipv6/multicast/uip-mcast6-engines.h"
#include "net/ip/uip.h"
#include "net/ipv6/uip-ds6.h"
#include "net/ip/uip-udp-packet.h"
#include "net/ip/uip-debug.h"

#include <stdio.h>

#include "dev/leds.h"

/*---------------------------------------------------------------------------*/
#define UDP_BROADCAST_PORT 5678      // UDP port of broadcast connection
#define UDP_IP_BUF    ((struct uip_udpip_hdr* ) &uip_buf[UIP_LLH_LEN])
/*---------------------------------------------------------------------------*/
#ifdef SMALLMSG
  typedef struct msg{
    uint8_t nodeId;
    uint8_t last_node;
    uint8_t next_channel;
    char round_finished:1;
    char link_param:1;                 // 0 for rssi, 1 for lqi
    char link_data[MAX_NODES];
  } msg_t;
#else
typedef struct msg{
  uint8_t nodeId;
  uint8_t last_node;
  uint8_t next_channel;
  char round_finished:1;
  char link_param:1;                 // 0 for rssi, 1 for lqi
  char link_data[MAX_NODES][MAX_NODES];
} msg_t;
#endif

static msg_t message;
static struct uip_udp_conn* broadcast_conn;
static struct uip_udp_conn* receive_conn;
static uip_ip6addr_t mcast_addr;
static uip_ip6addr_t addr;
/*---------------------------------------------------------------------------*/
static void send(){
  printf("sending\n");
  uip_udp_packet_send(broadcast_conn, &message, sizeof(message));
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
/*---------------------------------------------------------------------------*/

#endif
