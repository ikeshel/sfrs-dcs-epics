#!/bin/bash
#
# i.keshelashvili@gsi.de
#
# Run script for sfrs IOC

set -euo pipefail # Exit on error, undefined variable, or failed pipe

ioc_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ioc_boot="$ioc_root/iocBoot/iocsfrs"


# Source environment
if [ -f "$ioc_root/../../configure/RELEASE.local" ]; then
    source "$ioc_root/../../configure/RELEASE.local"
fi

ioc_arch=${EPICS_HOST_ARCH:-linux-x86_64}
ioc_binary="$ioc_root/bin/$ioc_arch/sfrs"

if [[ $# -gt 1 || ( $# -eq 1 && $1 != --dry-run ) ]]; then
    echo "Usage: $0 [--dry-run]" >&2
    exit 2
fi

# ss -lntup | grep ':5064'
export EPICS_CAS_SERVER_PORT="${EPICS_CAS_SERVER_PORT:-5064}"

# ---------------------------------------------------------------------------
# Select the PV location from the computer hostname
# ---------------------------------------------------------------------------

ioc_hostname=$(hostname -s)
ioc_hostname_lower=${ioc_hostname,,}
startup_file="st.cmd"
ioc_kind="MAIN"
unset PLSCI_SUBSTITUTIONS

case "$ioc_hostname_lower" in

    dtlpc019)
        pv_location="FHF1"
        ;;

    x86l-208|x86l-209|x86l-132)
        startup_file="st-plsci.cmd"
        ioc_kind="PLSCI"
        export PLSCI_SUBSTITUTIONS="db/plsci-${ioc_hostname_lower}.substitutions"
        case "$ioc_hostname_lower" in
            x86l-208) pv_location="FPF2" ;;
            x86l-209) pv_location="FPF4 FMF1" ;;
            x86l-132) pv_location="FMF2 FMF3 FHF1" ;;
        esac
        ;;

    *)
        echo "Unknown IOC computer: $ioc_hostname" >&2
        echo "Add this hostname to the mapping in $0" >&2
        exit 1
        ;;
esac

export IOC_HOSTNAME="$ioc_hostname"
export PV_LOCATION="$pv_location"


# ---------------------------------------------------------------------------
# Print the selected configuration
# ---------------------------------------------------------------------------

echo "Starting $ioc_kind IOC"
echo "  Hostname:     $IOC_HOSTNAME"
echo "  PV location:  $PV_LOCATION"
for chamber in $PV_LOCATION; do
    echo "  PV prefix:    SFRS:${chamber}:"
done
echo "  Startup:      $startup_file"
if [[ -n ${PLSCI_SUBSTITUTIONS:-} ]]; then
    echo "  Substitutions: $PLSCI_SUBSTITUTIONS"
fi
echo "  CA server:    $EPICS_CAS_SERVER_PORT"

if [[ ${1:-} == --dry-run ]]; then
    exit 0
fi

cd "$ioc_boot"
exec "$ioc_binary" "$startup_file"
