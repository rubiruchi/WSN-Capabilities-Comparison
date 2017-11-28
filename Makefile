CONTIKI_PROJECT = node sink

all: $(CONTIKI_PROJECT)

CONTIKI = /home/${USER}/contiki

CFLAGS += -DPROJECT_CONF_H=\"project-conf.h\"
#CFLAGS += -DUIP_CONF_ND6_SEND_NS=1

ifeq ($(TARGET),z1)
        CFLAGS += -D UART=0
else
        CFLAGS += -D UART=1
endif

#CONTIKI_SOURCEFILES +=
PROJECT_SOURCEFILES += rimestats.c
#MODULES += core/net/ipv6/multicast

SMALL = 1
CONTIKI_WITH_RIME = 1

include $(CONTIKI)/Makefile.include
