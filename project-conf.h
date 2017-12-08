#ifndef PROJECT_CONF_H_
#define PROJECT_CONF_H_


/* Change this to switch engines. Engine codes in uip-mcast6-engines.h */
//#define UIP_MCAST6_CONF_ENGINE UIP_MCAST6_ENGINE_ROLL_TM

#define DEFAULT_CHANNEL 25
#define DEFAULT_TX_POWER 31
#define MAX_NODES 30

#ifdef sensortag
#define ROM_BOOTLOADER_ENABLE                 1
#define BOARD_CONF_DEBUGGER_DEVPACK           1
#define IEEE_ADDR_CONF_HARDCODED              1
//#define IEEE_ADDR_CONF_ADDRESS                {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 2}
#define RF_BLE_CONF_ENABLED                   0
#define CC26XX_RF_CONF_BLE_SUPPORT            0
#define NETSTACK_CONF_RADIO        ieee_mode_driver
#endif

#define RIMESTATS_CONF_ENABLED 1
#define UART1_CONF_TX_WITH_INTERRUPT 1


#undef UIP_CONF_IPV6_RPL
#undef UIP_CONF_ND6_SEND_RA
#undef UIP_CONF_ROUTER
#define UIP_CONF_ND6_SEND_RA                0
#define UIP_CONF_ROUTER                     0
#define UIP_MCAST6_ROUTE_CONF_ROUTES        0

#undef UIP_CONF_TCP
#define UIP_CONF_TCP                        0

/* Code/RAM footprint savings so that things will fit on our device */
#undef NBR_TABLE_CONF_MAX_NEIGHBORS
#undef UIP_CONF_MAX_ROUTES
//#define NBR_TABLE_CONF_MAX_NEIGHBORS        10
//#define UIP_CONF_MAX_ROUTES                 10


//#undef UIP_MCAST6_ROUTE_CONF_ROUTES
//#define UIP_MCAST6_ROUTE_CONF_ROUTES        1

#undef NETSTACK_CONF_RDC
#define NETSTACK_CONF_RDC                   nullrdc_driver
#undef NETSTACK_CONF_MAC
#define NETSTACK_CONF_MAC                   nullmac_driver

#undef NETSTACK_RDC_CHANNEL_CHECKRATE
#define NETSTACK_RDC_CHANNEL_CHECKRATE      32
#undef RF_CHANNEL
#define RF_CHANNEL                          DEFAULT_CHANNEL

// #undef CC2420_CONF_CHANNEL
// #define CC2420_CONF_CHANNEL                 DEFAULT_CHANNEL

// #if RADIO==openmote
// #undef CC2538_RF_CONF_CHANNEL
// #define CC2538_RF_CONF_CHANNEL                 DEFAULT_CHANNEL
// #endif


#endif /* PROJECT_CONF_H_ */
