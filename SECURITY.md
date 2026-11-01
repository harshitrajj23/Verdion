# Security Policy

VERDION handles legal and regulatory material, model inputs, cryptographic records and blockchain configuration. Security reports are welcome. Please report suspected vulnerabilities privately and allow maintainers time to investigate before public disclosure.

## Supported versions

| Version | Security support |
|---|---|
| Current default branch (`main`) | Best-effort security fixes |
| Older commits, forks and untagged snapshots | Not guaranteed; upgrade to the current maintained revision where practical |

This is an actively developed prototype. No service-level security commitment is made for deployments operated by third parties.

## Reporting a vulnerability

**Do not open a public issue, pull request or discussion for an unpatched vulnerability.**

1. First check whether GitHub's private vulnerability reporting is enabled for this repository: open the repository's **Security** tab and select **Report a vulnerability** if available.
2. If private vulnerability reporting is unavailable, contact the repository maintainers using the private contact method listed on their GitHub profiles. Do not publish exploit details while arranging contact.
3. If the report concerns an exposed credential, immediately identify the credential owner and arrange revocation/rotation. Removing a value from the latest commit does not invalidate a credential or erase it from Git history, forks, caches or logs.

Please include, where possible:

- A concise description of the affected component and security impact.
- The affected commit, branch, release or deployment version.
- Reproduction steps and a minimal proof of concept that does not access or modify other people's data.
- Preconditions, permissions required and likely attack path.
- Relevant logs, request/response samples or transaction references with secrets and personal data redacted.
- A suggested mitigation, if you have one.

Do not include live private keys, seed phrases, access tokens, RPC credentials, personal data, privileged case material or confidential legal documents in the report. Redact them and identify the secret type instead.

## Response expectations

Maintainers will make a reasonable effort to acknowledge a valid report within five business days and to provide status updates as the investigation proceeds. These are response goals, not guaranteed deadlines. Severity, reproducibility, maintainer availability and upstream dependencies affect remediation time.

Please coordinate a disclosure date with maintainers. Do not publish exploit code or details before an agreed fix or mitigation is available, except where applicable law requires otherwise.

## In-scope areas

Security reports may concern:

- Authentication, authorization, session handling, API access control and unsafe defaults.
- Exposure of secrets, wallet material, database credentials, RPC provider credentials or private case data.
- Prompt injection, untrusted retrieved content, model/tool boundary failures and unsafe agent execution.
- Evidence provenance, canonicalization, hashing, Merkle verification and audit-record integrity.
- Smart-contract access control, commitment/reveal handling, replay protection, settlement, pause controls and unsafe state transitions.
- Injection, deserialization, path traversal, dependency/supply-chain and CI workflow risks.
- Cross-tenant or cross-case data exposure, insecure file handling and unintended public disclosure.

## Out of scope and testing boundaries

- Vulnerabilities in third-party platforms or providers that are not caused by VERDION code.
- Findings that require access to infrastructure or accounts you do not own or have explicit permission to test.
- Denial-of-service testing against public deployments, RPC providers or legal-source websites.
- Social engineering, phishing, physical attacks or spam.
- Reports based only on missing hardening headers or scanner output without a realistic security impact.

Do not attack public deployments, other contributors' accounts, external legal-source systems or blockchain infrastructure. Use a local environment or an explicitly authorised test environment. Do not submit real personal, privileged or confidential legal data as test input.

## Security design notes and limitations

- The project threat model is documented in [`shared/threat_model.md`](shared/threat_model.md). It describes intended controls; it is not an independent security certification.
- The current MVP threat model documents an authorized evaluator/admin trust assumption for some resolution paths. Do not assume all governance or dispute resolution is decentralized.
- Local and sample configuration files contain development defaults and placeholder values. In particular, the root `docker-compose.yml` is development scaffolding and must not be exposed as-is: replace its example database credentials, set production-safe debug/CORS values and use managed secrets.
- Never use example Anvil keys, placeholder addresses, local RPC endpoints or testnet credentials as production credentials.
- Ethereum Sepolia is a public test network. Do not send confidential facts or privileged evidence in transactions or events. A hash does not automatically anonymize the underlying information or remove metadata leakage.
- Cryptographic integrity checks can detect a mismatch against an expected digest. They do not prove source truth, legal correctness, completeness, confidentiality or availability.
- Foundry unit tests, benchmark results and project-generated audit reports are not substitutes for independent smart-contract audits, penetration testing, privacy review or legal review.

## Security configuration checklist

Before a deployment is reachable by untrusted users:

- Set `DEBUG=false` and restrict CORS to explicit trusted origins.
- Replace all sample passwords, placeholder addresses and local-only endpoints.
- Store private keys and provider credentials in a managed secret store or protected deployment environment; never in frontend variables or source code.
- Use a dedicated, least-privilege wallet for the intended network and verify chain ID and contract addresses before signing transactions.
- Apply authentication, authorization, rate limits, request-size limits, secure transport, logging redaction, backups and monitoring at the deployment layer.
- Review database access, retention, encryption, backups and isolation of sensitive case records.
- Pin and review dependencies and CI actions; run tests and contract analysis against the exact release commit.
- Reassess the threat model whenever agent tools, source ingestion, model providers, contract permissions or data flows change.
