# VPN Troubleshooting Guide

## Purpose

This guide helps engineers diagnose and resolve common VPN connectivity issues when accessing internal resources. If you cannot resolve the issue using this guide, escalate to the Network Engineering team.

## Common Issues and Solutions

### Issue 1: VPN Client Won't Connect

**Symptoms**: VPN client shows "connecting" indefinitely or fails with a timeout error.

**Troubleshooting steps**:

1. **Check your internet connection**: Verify you can reach external sites (google.com). VPN requires a working internet connection.
2. **Restart the VPN client**: Close the application completely and relaunch.
3. **Check VPN server status**: Visit https://status.internal.example.com to see if VPN servers are operational.
4. **Try an alternate VPN endpoint**:
   - Primary: vpn-east.internal.example.com
   - Secondary: vpn-west.internal.example.com
   - Emergency: vpn-backup.internal.example.com
5. **Check for software updates**: Ensure your VPN client is on the latest version (currently v4.2.1).
6. **Firewall interference**: Disable local firewall temporarily to test. Corporate firewalls on hotel/coffee shop networks may block UDP 1194 (OpenVPN) or UDP 500/4500 (IKEv2).

### Issue 2: Connected but Cannot Reach Internal Resources

**Symptoms**: VPN shows "connected" but internal URLs and SSH to bastion hosts fail.

**Troubleshooting steps**:

1. **Check DNS resolution**:
   ```
   nslookup bastion.internal.example.com
   ```
   Expected: should resolve to 10.x.x.x address. If it resolves to a public IP or fails, your DNS is not routing through the VPN.

2. **Check routing table**:
   ```
   # Windows
   route print | findstr 10.0

   # Mac/Linux
   netstat -rn | grep 10.0
   ```
   You should see routes for 10.0.0.0/8 through the VPN tunnel interface.

3. **Force DNS through VPN**: On Windows, flush DNS cache:
   ```
   ipconfig /flushdns
   ```

4. **Check split tunneling**: If split tunneling is enabled, only traffic destined for internal networks (10.0.0.0/8, 172.16.0.0/12) goes through the VPN. Public internet traffic goes directly. If you need to access a resource that's not on a standard internal subnet, contact Network Engineering.

### Issue 3: VPN Disconnects Frequently

**Symptoms**: VPN connection drops every 15-30 minutes.

**Troubleshooting steps**:

1. **Check idle timeout**: VPN sessions have a 30-minute idle timeout. If you're not actively sending traffic, the session will disconnect. Enable keep-alive in VPN client settings.
2. **Check network stability**: Run a continuous ping to the VPN gateway. If you see packet loss, the issue is your local network, not the VPN.
   ```
   ping -t vpn-east.internal.example.com
   ```
3. **Power management**: On laptops, check that the network adapter is not being put to sleep by power management settings.
4. **Concurrent sessions**: Only 1 VPN session per user is allowed. If you connected from another device, the first session will be terminated.

### Issue 4: Slow Performance Over VPN

**Symptoms**: SSH sessions lag, file transfers are slow, web apps timeout.

**Troubleshooting steps**:

1. **Check MTU**: VPN encapsulation reduces the effective MTU. Try reducing MTU on your local interface:
   ```
   # Linux
   sudo ip link set dev tun0 mtu 1400

   # Windows (admin PowerShell)
   netsh interface ipv4 set subinterface "VPN Tunnel" mtu=1400 store=persistent
   ```

2. **Use the closest VPN endpoint**: If you're on the West Coast, use vpn-west. Latency adds up over VPN.

3. **Bandwidth test**: Run an iperf test to the bastion host to measure actual throughput:
   ```
   iperf3 -c bastion.internal.example.com -p 5201
   ```
   Expected: >50 Mbps for most operations.

4. **Compression**: Enable compression in VPN client settings if available. This helps with text-heavy protocols (SSH, HTTP) but may hurt with already-compressed data.

## VPN Access Levels

| VPN Profile | Access | Who Gets It |
|------------|--------|-------------|
| Engineering | Full access to dev, staging, production networks | All engineers |
| Operations | Production + monitoring networks only | Ops team, on-call |
| Contractor | Dev network only, no production access | External contractors |
| Emergency | Full access, bypasses IP restrictions | On-call lead only |

## Requesting VPN Access

1. Submit a request through the IT Service Desk (ServiceNow).
2. Manager approval required.
3. Access is provisioned within 1 business day.
4. Quarterly access reviews — unused accounts are deactivated after 90 days of inactivity.

## Emergency VPN Reset

If you're locked out and need immediate access (e.g., during an incident):

1. Contact the on-call Network Engineer via PagerDuty.
2. They can reset your VPN credentials and issue a temporary certificate.
3. Temporary credentials expire after 24 hours.

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-10-01 | N. Engineering Team | Initial version |
| 2026-02-28 | E. Nguyen | Added MTU troubleshooting |
| 2026-05-01 | L. Chen | Updated VPN endpoints |
