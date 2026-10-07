# Troubleshooting Guide: macOS Desktop Client Known Issues

* **Document ID:** TS-APP-MACOS-08  
* **Owner:** Desktop Client Engineering Team  
* **Last Updated:** August 2024  
* **Product:** Desktop Client (macOS Edition v2.4.x)  

---

## 1. Issue KB-2048: Dark Mode "System Default" Theme Sync Failure

### Symptoms:
* User sets Appearance setting to **"System Default"**.
* macOS system appearance is set to **Dark Mode**.
* The application continues displaying the **Light theme** instead of matching the operating system.

### Root Cause:
In Desktop Client v2.4.x running on macOS Monterey through Sonoma, the underlying Electron renderer fails to capture Darwin OS theme switch IPC broadcast events when the application is launched prior to system theme toggling.

### Verified Workaround Steps:
Frontline agents should auto-respond with the following troubleshooting steps:
1. Navigate to **Settings > Appearance**.
2. Explicitly select **"Light"**, wait 2 seconds, and then select **"System Default"** again.
3. If the theme still fails to switch to dark, perform a complete application restart (**Cmd + Q** followed by relaunching the app).

### Permanent Resolution:
* A permanent IPC event listener patch is scheduled for release in **v2.5.0** (expected end of quarter).

---

## 2. Appearance Customization & Feature Scope
* Current appearance options are strictly limited to:
  * `Light`
  * `System Default`
* *Note on Unreleased Features:* Any customer inquiries regarding custom color schemes, time-based theme scheduling, or automated ambient lighting adjustments are not currently supported by the client. These should be logged as feature requests for the Product Design team.
