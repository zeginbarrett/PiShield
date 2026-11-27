"""Fixed privileged operations. Model text is never interpreted as a command."""
ACTIONS={
 'restart_live':('admin','Restart the live packet monitor',('/usr/bin/systemctl','restart','pishield-live.service')),
 'refresh_intelligence':('admin','Refresh the device intelligence snapshot',('/usr/bin/systemctl','start','pishield-intelligence.service')),
 'refresh_privacy':('admin','Refresh privacy counters',('/usr/bin/systemctl','start','pishield-privacy.service')),
 'refresh_lists':('admin','Download DNS lists and rebuild Gravity (may change DNS results)',('/usr/local/bin/pihole','-g')),
 'refresh_packages':('root','Refresh Debian package metadata',('/usr/bin/apt-get','update')),
 'install_jq':('root','Install jq from configured package repositories',('/usr/bin/apt-get','install','-y','--no-install-recommends','jq')),
 'install_tcpdump':('root','Install tcpdump from configured package repositories',('/usr/bin/apt-get','install','-y','--no-install-recommends','tcpdump')),
}
