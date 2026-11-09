#!../../bin/linux-x86_64/sfrs

# PLSCI-only startup. run.sh selects the substitutions for this server.
< envPaths
cd "${TOP}"

dbLoadDatabase("dbd/sfrs.dbd")
sfrs_registerRecordDeviceDriver(pdbbase)
dbLoadTemplate("${PLSCI_SUBSTITUTIONS}")

iocInit
cd "${TOP}/iocBoot/${IOC}"
