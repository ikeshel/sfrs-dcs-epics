TOP = ../..

include $(TOP)/configure/CONFIG

PROD_IOC = sfrs

DBD += sfrs.dbd
sfrs_DBD += base.dbd

sfrs_SRCS += sfrs_registerRecordDeviceDriver.cpp
sfrs_SRCS_DEFAULT += sfrsMain.cpp
sfrs_SRCS_vxWorks += -nil-

sfrs_LIBS += $(EPICS_BASE_IOC_LIBS)

include $(TOP)/configure/RULES