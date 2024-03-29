#include "node.h"
#include "dev/button-sensor.h"
/*---------------------------------------------------------------------------*/
static struct etimer lost_link_timer;
static struct etimer emergency_timer;
static struct etimer reboot_timer;
static char ro_timer_set, em_timer_set, re_timer_set;
static int last_node_id;
/*---------------------------------------------------------------------------*/
PROCESS(node_process, "node process");
AUTOSTART_PROCESSES(&node_process);
/*---------------------------------------------------------------------------*/
static void abc_recv(){
  msg_t received_msg = *(msg_t*) packetbuf_dataptr();

  etimer_stop(&reboot_timer);
  re_timer_set = 0;
  etimer_stop(&emergency_timer);
  em_timer_set = 0;

  /* don't handle message if node isn't needed for measuerement */
  if(node_id > received_msg.last_node){
    return;
  }

  /* indicates that a new measurement has started */
  if(message.last_node   != received_msg.last_node    ||
    message.next_channel != received_msg.next_channel ||
    message.next_txpower != received_msg.next_txpower ||
    message.link_param   != received_msg.link_param){
      printf("new measurement: deleting data\n");
      delete_link_data();
  }

  last_node_id = received_msg.last_node;
  next_channel = received_msg.next_channel;
  next_txpower = received_msg.next_txpower;
  message.next_channel = next_channel;
  message.next_txpower = next_txpower;
  message.link_param = received_msg.link_param;

  /* put content of recieved msg and link readings into own msg */
  fill_link_data(received_msg.node_id,
    received_msg.last_node,
    packetbuf_attr(PACKETBUF_ATTR_RSSI),
    packetbuf_attr(PACKETBUF_ATTR_LINK_QUALITY),
    received_msg.link_param);

  /* in case node works as additional sink */
  print_link_data(&received_msg);

  /* upwards sending*/
  if(received_msg.node_id == node_id -1){
    etimer_stop(&lost_link_timer);
    ro_timer_set = 0;
    sendmsg();
    prep_next_round();
  }

  /* lost link detection upwards sending*/
  if(received_msg.node_id < node_id-1){
    int wait_time = (node_id - received_msg.node_id);
    etimer_set(&lost_link_timer, (CLOCK_SECOND/30) * wait_time);
    lost_link_timer.p = &node_process;
    ro_timer_set = 1;
  }

  etimer_set(&emergency_timer, (CLOCK_SECOND/30)*last_node_id*4); //times 4 because sink will resend a round 4 times before resetting channel
  em_timer_set = 1;
  emergency_timer.p = &node_process;

}
    /*---------------------------------------------------------------------------*/

    PROCESS_THREAD(node_process, ev, data){
      PROCESS_BEGIN();

      PROCESS_EXITHANDLER(abc_close(&abc));

      ro_timer_set = 0;
      re_timer_set = 0;
      em_timer_set = 0;

      current_channel = DEFAULT_CHANNEL;
      current_txpower = DEFAULT_TX_POWER;

      message.node_id = node_id;
      message.last_node    = 0;
      message.next_channel = 0;
      message.next_txpower = 0;
      message.link_param   = 0;
      delete_link_data();

      NETSTACK_RADIO.set_value(RADIO_PARAM_TX_MODE, 0);

      abc_open(&abc,DEFAULT_CHANNEL,&abc_call);

      leds_on(LEDS_GREEN);

      while(1){
        SENSORS_ACTIVATE(button_sensor);

        PROCESS_WAIT_EVENT();

        if(etimer_expired(&lost_link_timer) && ro_timer_set){
          ro_timer_set = 0;
          printf("lost link detected. will continue sending\n");
          sendmsg();
          prep_next_round();
        }

        if(etimer_expired(&reboot_timer) && re_timer_set){
          watchdog_reboot();
        }

        if(etimer_expired(&emergency_timer) && em_timer_set){
          leds_blink();
          etimer_set(&reboot_timer,CLOCK_SECOND*10);
          re_timer_set = 1;
          printf("emergency timer expired\n");
          if(get_channel() != DEFAULT_CHANNEL || get_txpower() != DEFAULT_TX_POWER){
            printf("emergency reset\n");
            set_channel(DEFAULT_CHANNEL);
            set_txpower(DEFAULT_TX_POWER);
          }
        }

        if(ev == sensors_event && data == &button_sensor){
          printf("Channel: %d\n",get_channel());
          printf("TXpow: %d\n",get_txpower());
        }

      }
      PROCESS_END();
    }
    /*---------------------------------------------------------------------------*/
