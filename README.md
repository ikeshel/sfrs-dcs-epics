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

## PLSCI servers

Run `./run.sh` on each server. The hostname selects a PLSCI-only IOC:

| Server | Chambers | PMTs |
| --- | --- | --- |
| `x86l-208` | FPF2 | 6 |
| `x86l-209` | FPF4, FMF1 | 12 |
| `x86l-132` | FMF2, FMF3, FHF1 | 22 |

Use `./run.sh --dry-run` to print the selected configuration without starting
an IOC. These hosts use `iocBoot/iocsfrs/st-plsci.cmd` and their respective
`db/plsci-<hostname>.substitutions` files; they do not load SCIFI or MUSIC records.
The existing PMT numbering is preserved. The records currently use Soft Channel
device support, as defined in `db/plsci.template`.

The `dtlpc019` mapping continues to select the combined `st.cmd` startup.
Unknown hostnames are rejected. The launcher now executes the selected IOC;
use `--dry-run` when only checking configuration.
