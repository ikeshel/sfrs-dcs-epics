#!/bin/bash
#
# i.keshelashvili@gsi.de
#
# Run script for sfrs IOC

set -euo pipefail # Exit on error, undefined variable, or failed pipe

ioc_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ioc_arch=${EPICS_HOST_ARCH:-linux-x86_64}
ioc_binary="$ioc_root/bin/$ioc_arch/sfrs"
ioc_boot="$ioc_root/iocBoot/iocsfrs"


# Source environment
if [ -f "$ioc_root/../../configure/RELEASE.local" ]; then
    source "$ioc_root/../../configure/RELEASE.local"
fi

# ss -lntup | grep ':5064'
export EPICS_CAS_SERVER_PORT="${EPICS_CAS_SERVER_PORT:-5064}"

# ---------------------------------------------------------------------------
# Select the PV location from the computer hostname
# ---------------------------------------------------------------------------

ioc_hostname=$(hostname -s)
ioc_hostname_lower=${ioc_hostname,,}

case "$ioc_hostname_lower" in

    dtlpc019)
        pv_location="FHF1"
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

echo "Starting MAIN IOC"
echo "  Hostname:     $IOC_HOSTNAME"
echo "  PV location:  $PV_LOCATION"
echo "  PV prefix:    SFRS:${PV_LOCATION}:"
echo "  CA server:    $EPICS_CAS_SERVER_PORT"

cd "$ioc_boot"
# exec "$ioc_binary" st.cmd