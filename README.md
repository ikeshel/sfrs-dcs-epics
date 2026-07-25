#EPICS

## Download and Installation

```bash
mkdir ~/EPICS;
cd ~/EPICS
wget https://epics.anl.gov/download/base/base-7.0.10.tar.gz
```

## Environment settings
```bash
nano ~/.bashrc
```

```bash
export EPICS_BASE=$HOME/EPICS/base-7.0.10
export EPICS_HOST_ARCH=$($EPICS_BASE/startup/EpicsHostArch)
export PATH=$EPICS_BASE/bin/$EPICS_HOST_ARCH:$PATH
export LD_LIBRARY_PATH=$EPICS_BASE/lib/$EPICS_HOST_ARCH:$LD_LIBRARY_PATH
```

```bash
source ~/.bashrc 
```

### Verify EPICS tools are available:
```bash
softIoc -h
caget -h
caput -h
camonitor -h
```

## Compilation
```bash
cd ~/EPICS/base-xxx
make -j$(( $(nproc) - 1 ))
```
