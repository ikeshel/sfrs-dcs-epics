
TOP = .

include $(TOP)/configure/CONFIG

DIRS += sfrsApp
DIRS += db
DIRS += iocBoot

include $(TOP)/configure/RULES_TOP
