---
layout: single
title: "Cyber + Papers — 2026-05-02"
date: 2026-05-02
categories: [cyber-papers]
---

# Cyber + Papers Brief — 2026-05-02

_Generated 2026-05-02T19:45:00+02:00 Europe/Zurich. Coverage: ~06:30 to now._

---

## 🛡️ Cybersecurity — full day

### CVE-2026-31431 "Copy Fail" — Linux kernel LPE, CVSS 7.8, PoC public, CISA KEV

- **CVE-2026-31431 ("Copy Fail")** — CVSS 7.8 High | Exploitation status: **public PoC, CISA KEV** | Patch: available. A logic flaw in the Linux kernel's `algif_aead` module (AF_ALG crypto userspace API) allows an unprivileged local user to trigger a deterministic, controlled 4-byte write into the page cache of any readable file. A 732-byte Python PoC edits a setuid binary and achieves root without race conditions on effectively every Linux distribution shipped since 2017. **CISA has added this to KEV.** Affected distributions: Ubuntu 24.04 LTS, RHEL 10.1, SUSE 16, Amazon Linux 2023, Debian, Fedora, Arch Linux. Cloud and Kubernetes multi-tenant environments carry the highest risk (container breakout, lateral movement). Microsoft Defender reports "preliminary testing activity" and expects wider threat-actor uptake. Patches are available from all major distro vendors; interim mitigation is disabling `AF_ALG` socket creation. Publicly disclosed April 29, 2026. ([Microsoft Security Blog, 1 May 2026](https://www.microsoft.com/en-us/security/blog/2026/05/01/cve-2026-31431-copy-fail-vulnerability-enables-linux-root-privilege-escalation/)) ([CERT-EU Advisory 2026-005, 1 May 2026](https://cert.europa.eu/publications/security-advisories/2026-005/) [via snippet]) ([Ubuntu Blog, 1 May 2026](https://ubuntu.com/blog/copy-fail-vulnerability-fixes-available) [via snippet])

---

### CISA KEV additions (April 28): Two nation-state-exploited flaws, federal deadline May 12

- **CVE-2024-1708** (ConnectWise ScreenConnect — path traversal) — CVSS 8.4 | Exploitation: **active, Kimsuky (DPRK)** | Patch: available. An unauthenticated path traversal that leads to remote code execution. North Korean state group **Kimsuky** is actively exploiting this flaw and uses it to deploy **ToddlerShark**, a polymorphic malware variant capable of persistent access and data exfiltration. CISA added to KEV on April 28, 2026; FCEB agencies must remediate by **May 12, 2026**. ([CISA KEV Alert, 28 Apr 2026](https://www.cisa.gov/news-events/alerts/2026/04/28/cisa-adds-two-known-exploited-vulnerabilities-catalog) [via snippet]) ([The Hacker News, 28 Apr 2026](https://thehackernews.com/2026/04/cisa-adds-actively-exploited.html) [via snippet])

- **CVE-2026-32202** (Microsoft Windows Shell — NTLM spoofing) — CVSS 4.3 | Exploitation: **active, APT28 (Russia)** | Patch: KB5083769 (April 2026). A zero-click flaw that captures the victim's Net-NTLMv2 hash when they browse a folder, enabling relay attacks and lateral movement across the network. Stems from an **incomplete patch** for CVE-2026-21510, which APT28 had exploited against Ukraine and EU targets since December 2025. CVE-2026-32202 is now itself under active exploitation in the wild. Fix: April 2026 cumulative update KB5083769 for Windows 11 24H2/25H2. FCEB deadline: **May 12, 2026**. ([BleepingComputer, 28 Apr 2026](https://www.bleepingcomputer.com/news/security/cisa-orders-feds-to-patch-windows-flaw-exploited-in-zero-day-attacks/) [via snippet]) ([SecurityOnline.info, 28 Apr 2026](https://securityonline.info/cisa-kev-catalog-kimsuky-apt28-exploitation-cve-2024-1708-cve-2026-32202/) [via snippet])

---

### PyPI supply chain: PyTorch Lightning 2.6.2/2.6.3 poisoned for 42 minutes (April 30)

- **PyTorch Lightning supply chain attack** — Threat actors compromised the `lightning` package maintainer's PyPI credentials and pushed two malicious versions (2.6.2 and 2.6.3) on April 30, 2026. On import, the payload silently downloads the Bun JavaScript runtime and executes an 11 MB obfuscated JS script that steals tokens, credentials, environment variables, and cloud secrets — then exfiltrates everything to attacker-controlled GitHub repos using the **victim's own credentials**. Socket's AI scanner flagged both versions **18 minutes after publication**; PyPI quarantined them after **42 minutes**. A companion attack hit the `intercom-client` npm package in the same window [single-source]. Safe version: `lightning==2.6.1`. ([Socket.dev, 30 Apr 2026](https://socket.dev/blog/lightning-pypi-package-compromised) [via snippet]) ([The Hacker News, 30 Apr 2026](https://thehackernews.com/2026/04/pytorch-lightning-compromised-in-pypi.html) [via snippet]) ([Semgrep Research, 30 Apr 2026](https://semgrep.dev/blog/2026/malicious-dependency-in-pytorch-lightning-used-for-ai-training/) [via snippet])

---

### Threat intelligence: Two new China-aligned APT disclosures

- **GopherWhisper** (China-aligned, active since Nov 2023) — ESET Research published full analysis on April 23/29, 2026 of this previously undocumented APT targeting Mongolian governmental institutions. ~12 systems confirmed infected. The group deploys two Go-based backdoors: **LaxGopher** (C2 via private Slack channels, executes `cmd.exe` commands, posts results back to Slack) and **RatGopher** (C2 via private Discord servers). Microsoft 365 Outlook and file.io also used for C2 and exfiltration. C2 message timestamps consistently align to **China Standard Time** (08:00–17:00 CST). Initial access vector not yet confirmed in public reporting. No CVEs attributed. ([ESET WeLiveSecurity, 23 Apr 2026](https://www.welivesecurity.com/en/eset-research/gopherwhisper-burrow-full-malware/) [via snippet]) ([GlobeNewswire / ESET press release, 23 Apr 2026](https://www.globenewswire.com/news-release/2026/04/23/3279634/0/en/eset-research-discovers-new-china-aligned-group-gopherwhisper-it-abuses-messaging-services-discord-slack-and-outlook-to-spy.html) [via snippet]) ([BleepingComputer, Apr 2026](https://www.bleepingcomputer.com/news/security/new-gopherwhisper-apt-group-abuses-outlook-slack-discord-for-comms/) [via snippet])

- **SHADOW-EARTH-053** (China-aligned, active since Dec 2024) — Trend Micro published a research report (April 2026) on a multi-country espionage campaign targeting government, defense, and critical infrastructure across at least eight countries: Pakistan, Thailand, Malaysia, India, Myanmar, Sri Lanka, Taiwan, and **Poland** (NATO member). Initial access via **ProxyLogon** vulnerability chains against unpatched Microsoft Exchange and IIS servers. Post-compromise toolkit: **ShadowPad** modular backdoor (a long-running China-nexus shared tool), **GODZILLA** web shell for persistent remote execution, plus open-source tunneling tools (IOX, GOST, Wstunnel) for evasion. Transportation and defense-adjacent IT consultancies also targeted. Geographic spread across eight countries makes this a significant, sustained campaign. ([Trend Micro Research, Apr 2026](https://www.trendmicro.com/en_us/research/26/d/inside-shadow-earth-053.html) [via snippet]) ([CyberSecurityNews, Apr 2026](https://cybersecuritynews.com/china-aligned-attackers-use-multi-stage-espionage-campaign/) [via snippet])

---

## 📄 ML research — second arXiv batch

_arXiv batch inaccessible — attempted: arxiv.org/list/cs.LG, /cs.AI, /cs.CL, /cs.CV, /stat.ML, huggingface.co/papers. ~10 papers reviewed via web-search snippets but none confirmed as today's batch. Skipped per no-fabrication rule._

---

## Coverage footer

- **Sources used:** T1 = 6 | T2 = 5 | T3 = 0
  - T1: Microsoft Security Blog (direct fetch ✓), CISA KEV alert, ESET WeLiveSecurity, Socket.dev, Trend Micro, CERT-EU
  - T2: BleepingComputer, The Hacker News, SecurityOnline.info, CyberSecurityNews, Semgrep
- **Cyber items:** 5 (CVEs flagged: 3 — CVE-2026-31431, CVE-2024-1708, CVE-2026-32202 | CISA KEV additions: 2 | APT disclosures: 2 | supply chain: 1)
- **Papers:** 0 (section skipped — arXiv + HF inaccessible)
- **Direct fetches:** 1 (Microsoft Security Blog, 1 May 2026) | **Via-snippet citations:** 10
- **Gaps:**
  - cisa.gov returned HTTP 403 on direct fetch — KEV additions confirmed via T2 coverage and URL in search results only [via snippet]
  - arxiv.org and huggingface.co/papers both returned HTTP 403; HF Hub MCP query returned empty results — ML papers section skipped
  - ncsc.admin.ch (NCSC Switzerland) not checked; no Swiss-specific advisory surfaced in search
  - NVD direct fetch not attempted (gov-site sandbox restriction inferred)
  - No confirmed Apple, Google, or Cisco bulletins from today specifically; most recent vendor patches confirmed are Microsoft April 2026 Patch Tuesday (Apr 8) and Cisco IOS advisories (Apr 28 per SANS)
  - Covenant Health/Qilin (478K patients) and Interlock/Cisco FMC CVE-2026-20131 story found in research but both predate the current coverage window (December 2025 / March 2026 respectively) — omitted
