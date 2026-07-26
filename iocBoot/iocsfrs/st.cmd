#!../../bin/linux-x86_64/sfrs

< envPaths

cd "${TOP}"

## Load the SFRS database definitions
dbLoadDatabase("dbd/sfrs.dbd")
sfrs_registerRecordDeviceDriver(pdbbase)

## SciFi substitutions
dbLoadTemplate("db/scifi_bias.substitutions","OFF_THRESHOLD=0.2,BIAS_TOLERANCE=0.5,INITIAL_BIAS=0.0")
dbLoadTemplate("db/scifi_mask.substitutions")
dbLoadTemplate("db/generated/scifi_temperature.substitutions")
dbLoadTemplate("db/scifi_threshold.substitutions")

## Plastic scintillator substitutions
dbLoadTemplate("db/plsci.substitutions")

## MUSIC substitutions
dbLoadTemplate("db/music_adc_ch.substitutions")
dbLoadTemplate("db/music_hv.substitutions")

## Load the IOC database
iocInit

cd "${TOP}/iocBoot/${IOC}"