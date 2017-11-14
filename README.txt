node.h - contains multicast initialization, message struct and send method for normal nodes and the sink node.
node.c - contains code for normal nodes
sink.c - contains code for sink nodes

Node IDs:
-SINK NODES should always have NODE ID 0 (or at least the LOWEST id in the network)
-NORMAL NODES should always have UNIQUE NODE IDs in ASCENDING order.

Node placement:
-The assumption is that the is always a connection between nodes in the order of their node ids (so 0-1, 1-2, 2-3, ...)
-Each node sends a broadcast message once it has received a message from the node before it.

Communication:
-The nodes are sending all the link information back to one sink in one packet.
-Define SMALLMSG in project_config to switch to each node broadcasting only own data at the end of the round. (assumes multiple sinks)

-MAX_NODES is currently set to 10 in the project-config  (cannot exceed 11 without SMALLMSG due to buffersize restrictions)
_________________________________________________________________________
For Cooja Simulation:
- possible adjust contiki path in Makefile is correct

- make sure COOJA is defined in project-conf.h
- adjust last_node_id in the sink.c process
- press button of sink node to start one round
