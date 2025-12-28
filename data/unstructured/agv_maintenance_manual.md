# AGV Fleet Maintenance Manual
## VoltStream EV Gigafactory - KUKA KMR-iiwa Fleet

**Document Version:** 3.2.1  
**Last Updated:** 2024-09-15  
**Equipment Model:** KUKA KMR-iiwa  
**Applicable Fleet:** AGV_001 through AGV_020

---

## Table of Contents

1. [Overview](#overview)
2. [Error Code Reference](#error-code-reference)
3. [Troubleshooting Procedures](#troubleshooting-procedures)
4. [Preventive Maintenance](#preventive-maintenance)
5. [Environmental Guidelines](#environmental-guidelines)

---

## Overview

The VoltStream Gigafactory utilizes a fleet of 20 KUKA KMR-iiwa Automated Guided Vehicles (AGVs) for material transport between production lines. These AGVs employ LiDAR-based navigation with optical sensors for precise positioning and obstacle avoidance.

### Critical Operating Parameters

| Parameter | Normal Range | Warning Threshold | Critical Threshold |
|-----------|--------------|-------------------|-------------------|
| Battery Level | 40-100% | 30% | 20% |
| Ambient Humidity | 35-55% | <35% or >60% | <30% or >65% |
| Dust (PM2.5) | <15 µg/m³ | 15-25 µg/m³ | >25 µg/m³ |
| Operating Temperature | 18-26°C | 15-30°C | <10°C or >35°C |

---

## Error Code Reference

### AGV-ERR-99: Optical Sensor Obscured

**Severity:** ERROR  
**Category:** SENSOR  
**Root Cause:** LiDAR or optical sensor blocked, typically by dust accumulation on the sensor lens.

**Symptoms:**
- AGV stops unexpectedly during operation
- Navigation accuracy degraded
- False obstacle detection warnings
- Intermittent path deviation

**Common Triggers:**
- Low humidity environment (<35%) causing increased airborne particulates
- Dust levels exceeding 25 µg/m³
- Extended operation without sensor cleaning
- HVAC system malfunction or filter saturation

**Resolution Time:** 10-15 minutes

---

### AGV-ERR-01: Low Battery

**Severity:** WARNING  
**Category:** ELECTRICAL

**Description:** Battery level has dropped below the minimum safe operating threshold. The AGV will automatically route to the nearest charging station.

**Action Required:**
1. Allow AGV to complete charging cycle (approximately 30 minutes)
2. If frequent low battery events occur, schedule battery health check
3. Review route optimization to ensure charging opportunities

---

### AGV-ERR-42: Path Obstruction

**Severity:** WARNING  
**Category:** SENSOR

**Description:** Physical obstacle detected in the planned navigation path.

**Action Required:**
1. Identify and remove the obstruction
2. Clear the path within the 2-meter safety zone
3. Use manual override to reroute if obstruction is permanent fixture

---

### AGV-ERR-55: Communication Lost

**Severity:** CRITICAL  
**Category:** SOFTWARE

**Description:** AGV has lost connection to the central fleet management system.

**Action Required:**
1. Check network connectivity in the affected zone
2. Verify fleet management server status
3. Restart AGV controller if connectivity issue persists
4. Contact IT support if network infrastructure issue suspected

---

## Troubleshooting Procedures

### Procedure T-99: Dust Mitigation Cycle for AGV-ERR-99

**Purpose:** Clear optical sensor obstruction caused by dust accumulation  
**Applicability:** All AGV units experiencing AGV-ERR-99 errors  
**Frequency:** As needed, or preventively when dust levels exceed 20 µg/m³

#### Step-by-Step Instructions

**Step 1: Safe Stop**
1. Using the fleet management console, issue a SAFE_STOP command to the affected AGV
2. Verify AGV has stopped in a designated safe zone (zones marked with yellow floor markings)
3. Engage parking brake via console command: `AGV_PARK <unit_id>`

**Step 2: Sensor Access**
1. Approach the AGV from the rear (opposite the LiDAR sensor)
2. Locate the primary LiDAR sensor housing (top-mounted rotating unit)
3. Identify secondary optical sensors (four corner-mounted units)

**Step 3: Cleaning Procedure**
1. Use approved microfiber lens wipes (Part #: LW-MF-001)
2. Gently wipe the LiDAR lens in circular motion, working from center outward
3. Clean each corner optical sensor lens
4. Do NOT use compressed air (may damage sensor calibration)
5. Do NOT use liquid cleaners (may leave residue)

**Step 4: Sensor Calibration**
1. From the local AGV control panel, access Diagnostics menu
2. Select "Sensor Calibration" → "Quick Cal"
3. Wait for calibration sequence to complete (approximately 45 seconds)
4. Verify all sensors report "NOMINAL" status

**Step 5: Resume Operation**
1. Disengage parking brake: `AGV_RELEASE <unit_id>`
2. Issue route resume command: `AGV_RESUME <unit_id>`
3. Monitor first two route segments for any recurrence

#### Post-Procedure Verification
- Verify AGV completes at least 3 successful deliveries without error
- Log the maintenance event in the fleet management system
- If error recurs within 1 hour, escalate to Level 2 maintenance

---

### Procedure T-ENV: Environmental Condition Response

**Purpose:** Proactive measures when environmental conditions approach critical thresholds

#### Humidity Below 35%

**Risk:** Low humidity increases static electricity and airborne dust, leading to increased AGV-ERR-99 occurrences.

**Mitigation Steps:**
1. Notify facilities team to increase HVAC humidification
2. Reduce AGV fleet speed to 75% of normal
3. Increase preventive sensor cleaning frequency to every 4 hours
4. Consider temporary production rate reduction if conditions persist

#### Dust Levels Above 25 µg/m³

**Risk:** High dust concentration will rapidly contaminate optical sensors.

**Mitigation Steps:**
1. Immediately initiate Dust Mitigation Cycle on all active AGVs
2. Request emergency HVAC filter check/replacement
3. Identify and address dust source (grinding operations, material handling, etc.)
4. Suspend AGV operations if dust exceeds 40 µg/m³

---

## Preventive Maintenance

### Daily Checks (Performed by Operators)

| Check Item | Acceptance Criteria | Action if Failed |
|------------|---------------------|------------------|
| Visual sensor inspection | No visible dust/debris | Clean sensors |
| Battery charge level | >50% at shift start | Charge before use |
| Navigation light status | All lights operational | Replace failed lights |
| Emergency stop function | Responds within 0.5 sec | Remove from service |

### Weekly Maintenance

| Maintenance Item | Procedure | Duration |
|------------------|-----------|----------|
| Full sensor cleaning | Procedure T-99 | 15 min |
| Wheel inspection | Visual check for wear | 10 min |
| Battery health check | Diagnostic scan | 5 min |
| Software update check | Fleet management console | 5 min |

### Monthly Maintenance

- Full LiDAR calibration (factory procedure)
- Battery deep cycle and capacity test
- Motor and drive system inspection
- Communication module testing
- Emergency brake system verification

---

## Environmental Guidelines

### Optimal Operating Conditions

The AGV fleet operates most reliably under the following conditions:

| Parameter | Optimal Range | Notes |
|-----------|---------------|-------|
| Humidity | 40-50% | Minimizes dust and static |
| PM2.5 | <10 µg/m³ | Reduces sensor cleaning frequency |
| Temperature | 20-24°C | Optimal battery performance |

### Environmental Monitoring Integration

The AGV fleet management system integrates with factory environmental sensors to provide:

1. **Predictive Alerts:** When humidity trends toward critical thresholds
2. **Automated Speed Reduction:** When dust levels exceed warning threshold
3. **Maintenance Scheduling:** Increased cleaning frequency during adverse conditions

### Correlation: Environmental Conditions and AGV Reliability

Historical analysis has demonstrated strong correlation between environmental factors and AGV performance:

| Condition | Reliability Impact |
|-----------|-------------------|
| Humidity <30% | 15-20% increase in AGV-ERR-99 |
| Humidity <25% | 25-35% increase in AGV-ERR-99 |
| PM2.5 >30 µg/m³ | Sensor cleaning required every 2 hours |
| PM2.5 >40 µg/m³ | Operations suspension recommended |

**Note:** Low humidity and high dust are typically correlated—dry air conditions lead to increased particulate suspension.

---

## Contact Information

**AGV Fleet Maintenance Team**  
- Shift Supervisor: Extension 4001  
- Emergency Response: Extension 4099  

**Facilities (HVAC/Environmental)**  
- Control Room: Extension 3001  
- Emergency: Extension 3099  

**IT Support (Network/Communication)**  
- Help Desk: Extension 2001

---

*This document is property of VoltStream EV Manufacturing. Unauthorized distribution prohibited.*

