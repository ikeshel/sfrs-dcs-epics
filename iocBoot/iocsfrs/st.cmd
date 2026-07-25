#!../../bin/linux-x86_64/sfrs

< envPaths

cd "${TOP}"

dbLoadDatabase("dbd/sfrs.dbd")
sfrs_registerRecordDeviceDriver(pdbbase)

# SciFi temperature and bias substitutions
dbLoadTemplate("db/generated/scifi_temperature.substitutions")

dbLoadTemplate("db/generated/scifi_bias.substitutions","P=SFRS,OFF_THRESHOLD=0.2,BIAS_TOLERANCE=0.5,INITIAL_BIAS=0.0")

dbLoadTemplate("db/generated/scifi_threshold.substitutions","P=SFRS")

dbLoadTemplate("db/generated/scifi_mask.substitutions")

dbLoadTemplate("db/plsci.substitutions")

iocInit

cd "${TOP}/iocBoot/${IOC}"