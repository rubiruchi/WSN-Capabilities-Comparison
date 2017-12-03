node.h - contains all basic functions for normal nodes and the sink node.
node.c - contains code for normal nodes
sink.c - contains code for sink node

Node IDs:
-SINK NODE should always have NODE ID 1 (or at least the lowest id in the network, but not 0)
-NORMAL NODES should always have unique NODE IDs in ASCENDING order.

Node placement:
- The assumption is that the is at least one connection between nodes in the order of their node ids (1-2, 2-3, ...)
- Each node sends a broadcast message once it has received a message from the node before it.
- The last node in the network should have a connection to the sink node

_________________________________________________________________________
For Cooja Simulation:

- open serial line input window of the sink node
- Enter parameters the following way: <last node>,<channel>,<txpower>,<linkparameter>,<number of rounds>

<last node>:        the node id of the last node in the network
<channel>:          the channel you want to send on (11-26)
<txpower>:          the transmisson power you want to send with (1-31)
<linkparameter>:    the parameter you want to measure (0 for RSSI, 1 for LQI, 2 for number of dropped packets)
<number of rounds>: the number of measurement rounds

For Script:
- Start with: python script <platform>
- Will scan through /dev/ and try to log into every device starting with ttyUSB
- The measurements are stored in a list individually for each node
- The resulting .json files can be found in the "Measurements" folder created in the parent directory
