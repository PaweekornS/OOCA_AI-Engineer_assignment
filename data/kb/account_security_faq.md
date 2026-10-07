# Knowledge Base: Account Security & Authentication FAQ

* **Document ID:** FAQ-SEC-101  
* **Owner:** Identity & Access Management Team  
* **Last Updated:** July 2024  

---

## 1. Password Reset Procedures
* Self-service password resets can be requested from the login screen via **"Forgot Password"**.
* Reset tokens remain valid for **15 minutes**.
* If a user does not receive the reset link within 5 minutes, verify their spam filters or check whether their account is locked due to multiple failed login attempts.

## 2. Multi-Factor Authentication (MFA / 2FA) Reset
* If an end user loses access to their authenticator app (Google Authenticator, Authy):
  * **Pro / Free Tiers:** Must use their 16-character backup emergency recovery codes generated during initial enrollment.
  * **Enterprise Accounts:** Organization IT Administrators can issue an MFA bypass token directly from the Enterprise Admin Console. Frontline agents cannot manually disable MFA on enterprise user accounts.
