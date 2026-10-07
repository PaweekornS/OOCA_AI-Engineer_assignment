# Internal Policy: Payment Failures, Authorization Holds & Disputes

* **Document ID:** POL-FIN-2024-03  
* **Owner:** Finance & Billing Operations  
* **Last Updated:** October 2024  
* **Audience:** Customer Support, Billing Operations, Account Managers  

---

## 1. Overview & Scope
This policy governs how customer support representatives handle payment errors, duplicate pending charges, subscription upgrade stalls, and bank dispute threats.

## 2. Card Payment Failures & Pre-Authorization Holds
When a user attempts to upgrade a plan (e.g., from Free to Pro at $29.99/mo) and encounters a transaction failure, our payment gateway may submit an authorization request to the issuing bank before the decline occurs.

### Critical Bank Behavior:
* **Pending Holds:** Issuing banks frequently hold the transaction amount ($29.99) as a "Pending" or "Authorization" hold on the user's mobile banking app for each retry attempt.
* **Not Captured Funds:** If the customer tried 3 times, their bank app may display 3 separate $29.99 charges. **These funds have NOT been captured by our merchant account.**
* **Automatic Expiration:** In 99% of cases, card networks release unauthorized holds within **3 to 5 business days**.

> [!WARNING]
> **Strict Guardrail: Zero Financial Promises**  
> Frontline Support agents are **strictly prohibited** from promising immediate bank refunds, cash reversals, or financial credits. Promising *"We have refunded $89.97 to your card"* creates legal and accounting liability for transactions that were never captured.

### Required Support Actions:
1. Explain the distinction between **Pending Bank Authorization Holds** and settled charges clearly and reassuringly.
2. If the user reports multiple pending charges and threatens bank chargebacks or disputation:
   * **Do NOT attempt to resolve autonomously.**
   * Flag ticket urgency as **High** or **Critical** (churn and merchant fee risk).
   * Immediately route ticket to **Billing Operations**.
   * SLA for disputed billing review: Under 1 hour during business operations.

## 3. Subscription License Provisioning Stalls
If a customer completes payment or has pending transactions but their account remains on the **Free tier**:
* This indicates a webhook synchronization delay between the gateway and our licensing service.
* Frontline support **cannot manually provision temporary Pro export access** without Billing Operations supervisor sign-off.
* Ask the customer for the last 4 digits of the card or transaction timestamp to expedite Billing Operations investigation.
