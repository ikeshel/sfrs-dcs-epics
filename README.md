#EPICS

## Download and Installation
```wget https://epics.anl.gov/download/base/base-7.0.10.tar.gz```

## Environment settings
```nano ~/.bashrc```

```
export EPICS_BASE=/home/irakli/EPICS/base-7.0.10
export EPICS_HOST_ARCH=$($EPICS_BASE/startup/EpicsHostArch)
export PATH=$EPICS_BASE/bin/$EPICS_HOST_ARCH:$PATH
export LD_LIBRARY_PATH=$EPICS_BASE/lib/$EPICS_HOST_ARCH:$LD_LIBRARY_PATH
```
### Verify EPICS tools are available:
```
softIoc -h
caget -h
caput -h
camonitor -h
```
