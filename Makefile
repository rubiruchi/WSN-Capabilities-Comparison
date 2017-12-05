CONTIKI_PROJECT = node sink

all: $(CONTIKI_PROJECT)

CONTIKI = /home/${USER}/contiki

CFLAGS += -DPROJECT_CONF_H=\"project-conf.h\"
#CFLAGS += -DUIP_CONF_ND6_SEND_NS=1

ifeq ($(TARGET),openmote-cc2538)
CFLAGS += -D openmote=1
endif

ifeq ($(TARGET),srf06-cc26xx)
CFLAGS += -D sensortag=1
endif

ifeq ($(TARGET),sky)
CFLAGS += -D $(TARGET)=1
endif

ifeq ($(TARGET),z1)
CFLAGS += -D $(TARGET)=1
endif

# ifdef NODEID
# CFLAGS += -D NID=$(NODEID)
# endif

#CONTIKI_SOURCEFILES +=
PROJECT_SOURCEFILES += rimestats.c
#MODULES += core/net/ipv6/multicast

SMALL = 1
CONTIKI_WITH_RIME = 1

include $(CONTIKI)/Makefile.include
