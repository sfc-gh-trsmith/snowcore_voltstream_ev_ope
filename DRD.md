# **DRD- OPE Intelligent Jidoka System**

GITHUB REPO NAME: snowcore\_voltstream\_ev\_ope

## **1\. Strategic Overview**

* **Problem Statement:** In high-volume EV "Gigafactories," efficiency losses are often hidden in the white space between production steps. Disconnected silos—ERP systems showing "available" inventory while shop floor IoT sensors report starvation—create a "Ghost Inventory" paradox where high machine uptime (OEE) masks low Overall Process Efficiency (OPE). Current manual root-cause analysis takes hours, risking shipment targets.  
* **Target Business Goals (KPIs):**  
  * **Increase Overall Process Efficiency (OPE) by 15%:** Bridge the gap between theoretical capacity and actual throughput.  
  * **Reduce "Material Starvation" Downtime by 20%:** optimize internal logistics (AGV routing) to match production cadence.  
* **The "Wow" Moment:** A Cortex Agent autonomously correlates a structured forecast (high dust probability) with unstructured maintenance manuals (sensor failure protocols) to proactively recommend a "Dust Mitigation Cycle" before the line stops, demonstrating true *Jidoka* (automation with human intelligence).

## **2\. User Personas & Stories**

| Persona Level | Role Title | Key User Story (Demo Flow) |
| :---- | :---- | :---- |
| **Strategic** | **VP of Manufacturing** | "As a VP, I want to query 'Why did OPE drop on Line 4?' in plain English and get an instant, data-backed answer without waiting for analyst reports." |
| **Operational** | **Plant Manager** | "As a Plant Manager, I want to receive proactive recommendations from an AI Agent that integrates shift logs and error codes so I can approve fixes (e.g., cleaning cycles) immediately." |
| **Technical** | **Lead Data Scientist** | "As a Data Scientist, I want to transparently inspect the Python code behind the AI's forecast in a Snowpark Notebook to verify the correlation between humidity levels and AGV failure rates." |

## **3\. Data Architecture & Snowpark ML (Backend)**

* **Structured Data (Inferred Schema):**  
  * FACTORY\_IOT\_STREAM: \[Machine\_ID, Timestamp, Vibration\_Hz, Throughput\_Count, Status\_Code\] (Ingested via Snowpipe Streaming).  
  * ERP\_INVENTORY\_SNAPSHOT: \[SKU\_ID, Warehouse\_Location, Quality\_Status, Quantity\_On\_Hand\] (Loaded via Dynamic Tables).  
  * AGV\_TELEMETRY: \[Vehicle\_ID, Battery\_Level, Error\_Code, Route\_Segment, Velocity\].  
* **Unstructured Data (Tribal Knowledge):**  
  * **Source Material:** OEM Maintenance Manuals (PDF), Daily Shift Reports (Email/Text), AGV Error Code Dictionaries.  
  * **Purpose:** Indexed by Cortex Search to answer qualitative questions like "What does error code AGV-ERR-99 mean?" and "How do I clear a blockage on Line 4?"  
* **ML Notebook Specification:**  
  * **Objective:** Predictive Maintenance / Anomaly Detection for AGV Fleet.  
  * **Target Variable:** FAILURE\_PROBABILITY (Binary Classification or Probability Score).  
  * **Algorithm Choice:** Cortex Forecast (Time-series) for failure trends; XGBoost (Snowpark ML) for feature importance (Humidity vs. Dust).  
  * **Inference Output:** Predictions written to table PREDICTIVE\_MAINTENANCE\_ALERTS.

## **4\. Cortex Intelligence Specifications**

### **Cortex Analyst (Structured Data / SQL)**

* **Semantic Model Scope:**  
  * **Measures:** OPE\_Score, Total\_Throughput, Downtime\_Minutes, Yield\_Percentage.  
  * **Dimensions:** Production\_Line\_ID, Shift\_ID, Product\_SKU, Error\_Type.  
* **Golden Query (Verification):**  
  * *User Prompt:* "Show me the average OPE for Line 4 grouped by shift for the last week."  
  * *Expected SQL Operation:* SELECT Shift\_ID, AVG(OPE\_Score) FROM FACTORY\_METRICS WHERE Production\_Line\_ID \= 'Line 4' AND Date \>= DATEADD(day, \-7, CURRENT\_DATE()) GROUP BY Shift\_ID

### **Cortex Search (Unstructured Data / RAG)**

* **Service Name:** MFG\_KNOWLEDGE\_BASE\_SEARCH  
* **Indexing Strategy:**  
  * **Document Attribute:** Indexed by Equipment\_Model and Error\_Code\_Tag to ensure precise retrieval of relevant manuals.  
* **Sample RAG Prompt:** "What are the recommended troubleshooting steps for an AGV sensor obstruction error?"

### **Cortex Agents (Orchestration)**

* **Role:** The "Jidoka" Coordinator.  
* **Tools:**  
  1. cortex\_analyst\_tool: To query current OPE stats.  
  2. cortex\_search\_tool: To look up repair manuals.  
  3. forecast\_model\_tool: To run the failure prediction function.  
* **Agent Logic:** "IF failure\_probability \> 80% AND cause \== 'dust', THEN search manuals for 'cleaning protocol' AND propose 'Dust Mitigation Cycle'."

## **5\. Streamlit Application UX/UI**

* **Layout Strategy:**  
  * **Page 1 (The Pulse):** A "Mission Control" view. Top-level KPIs (OEE vs. OPE) visualized with a gauge chart. A sidebar Chat Interface ("VoltStream Co-Pilot") is persistent.  
  * **Page 2 (The Lab):** Embedded Snowpark Notebook view allowing technical drill-down into the ML model's logic, alongside a "Digital Twin" map of the AGV routes (Altair/PyDeck).  
* **Component Logic:**  
  * **Visualizations:** Time-series line chart showing Humidity (inverted) vs. AGV Failures to visually prove correlation.  
  * **Chat Integration:** The chat input uses a router (Agent) to decide whether to trigger SQL generation (Analyst) for numbers or RAG (Search) for explanations, seamlessly blending the response.

## **6\. Success Criteria**

* **Technical Validator:** The Cortex Agent successfully orchestrates a three-step reasoning chain (Query Metric \-\> Check Forecast \-\> Retrieve Manual \-\> Propose Action) in under 10 seconds.  
* **Business Validator:** The workflow reduces the "Time-to-Decision" for a production bottleneck from 4 hours (manual data gathering) to \< 5 minutes (AI-assisted diagnosis).

# **Data Requirements**

This architecture is designed to support the "Jidoka 2.0" narrative. It moves from messy, realistic source systems (RAW) to a clean integration layer (ATOMIC), and finally to a consumption-ready layer (EV\_OPE) that powers the demo's specific insights.

### **1\. Data Architecture Hierarchy**

We will use a standard **Bronze (RAW) \-\> Silver (ATOMIC) \-\> Gold (EV\_OPE)** medallion architecture.

#### **Layer 1: RAW (Source System Mirrors)**

* **Objective:** Capture data "as-is" from the wild. High fidelity to original formats (JSON, messy columns).  
* **Key Schemas:** `RAW_SAP_ERP`, `RAW_SIEMENS_MES`, `RAW_IOT_MQTT`.

#### **Layer 2: ATOMIC (Integrated & Cleaned)**

* **Objective:** Normalized, harmonized data. "One truth" for Products, Assets, and Time.  
* **Key Schema:** `ATOMIC_MFG`.

#### **Layer 3: EV\_OPE (Business Data Mart)**

* **Objective:** Star schemas optimized for Cortex Analyst (SQL generation) and Streamlit dashboards.  
* **Key Schema:** `EV_OPE_MART`.

---

### **2\. Entity Definition & Schema Specification**

#### **A. RAW Layer (The Sources)**

| Source System | Entity / Table Name | Columns (Representative) | Simulation Notes for Demo |
| :---- | :---- | :---- | :---- |
| **SAP ERP** | `MATERIAL_DOCUMENT` | `MAT_DOC_ID`, `POSTING_DATE`, `SKU`, `MVMT_TYPE` (e.g., 101, 321), `STOCK_TYPE` (Unrestricted, Quality Inspection), `BATCH_ID` | Represents the "financial" view of inventory. Crucial for showing material is "technically" on site but blocked. |
| **SAP ERP** | `PROD_ORDER_HEADER` | `ORDER_ID`, `TARGET_QTY`, `SCHED_START`, `SCHED_END`, `SKU` | The plan. Used to calculate the "Plan" part of OPE. |
| **Siemens MES** | `EQUIPMENT_STATE_LOG` | `EVENT_ID`, `ASSET_ID`, `TIMESTAMP`, `STATE_CODE` (1=Run, 2=Idle, 3=Fault), `REASON_CODE` (e.g., "Starvation") | The reality. "Starvation" states here drive the low OPE metric. |
| **Siemens MES** | `AGV_TELEMATICS_LOG` | `MSG_ID`, `AGV_ID`, `TIMESTAMP`, `X_COORD`, `Y_COORD`, `BATTERY_LVL`, `ERROR_CODE` (e.g., AGV-ERR-99) | The root cause. Needs to contain the specific error code that links to the PDF manual. |
| **IoT Historian** | `ENV_SENSOR_STREAM` | `READING_ID`, `SENSOR_ID`, `ZONE_ID`, `TIMESTAMP`, `METRIC` (Humidity, PM2.5, Temp), `VALUE` | The hidden variable. High frequency data showing the environmental conditions. |

#### **B. ATOMIC Layer (The Relationships)**

* **`DIM_ASSET`**: Unified list of all Machines, Lines, and AGVs. Maps `MES_ASSET_ID` to `ERP_WORK_CENTER`.  
    
* **`DIM_PRODUCT`**: Hierarchy of SKUs (Battery Pack \-\> Module \-\> Cell).  
    
* **`FCT_INVENTORY_JOURNEY`**: A longitudinal view of a Batch.  
    
* *Columns:* `BATCH_ID`, `TIME_IN_Transit`, `TIME_IN_Quality`, `TIME_IN_Production`.  
    
* *Purpose:* Calculates the "Wait Time" vs. "Value Added Time" for OPE.  
    
* **`FCT_PRODUCTION_EVENT`**: Harmonized event log combining MES Machine States with IoT Environmental context.  
    
* *Columns:* `EVENT_ID`, `ASSET_ID`, `START_TIME`, `END_TIME`, `DURATION_SEC`, `STATE_CATEGORY`, `AVG_HUMIDITY_DURING_EVENT`, `AVG_DUST_DURING_EVENT`.

#### **C. EV\_OPE Data Mart (The Demo Views)**

* **`OPE_DAILY_FACT`**: Pre-aggregated metrics for the Executive Dashboard.  
    
* *Columns:* `DATE`, `LINE_ID`, `OEE_PCT`, `OPE_PCT`, `TOTAL_YIELD`, `TOTAL_SCRAP`, `AVG_CYCLE_TIME`.  
    
* *Calculation:* . (Demo data must show OEE \> 90% but OPE \< 65%).  
    
* **`AGV_FAILURE_ANALYSIS`**: The training set for the ML model.  
    
* *Columns:* `SHIFT_ID`, `AVG_HUMIDITY`, `AVG_DUST_PM25`, `FAILURE_COUNT_AGV`, `TOTAL_AGV_OPS`.  
    
* *Purpose:* This is the exact table the Snowpark Notebook will query to find the correlation.

---

### **3\. Synthetic Data Generation Specification (The Recipe)**

To make the demo believable, we cannot generate random noise. We must generate **causal patterns**.

#### **Step 1: Define the "Normal" Baseline (Months 1-2)**

* **Production:** Steady rhythm. 1000 units/day.  
    
* **Environment:**  
    
* Humidity: Randomized Gaussian distribution (Mean=45%, SD=5%).  
    
* Dust (PM2.5): Low (Mean=10µg/m³, SD=2).  
    
* **AGVs:** Reliability \= 99.9%. `AGV-ERR-99` appears randomly once every 2 weeks (noise).  
    
* **Inventory:** `TIME_IN_Quality` averages 2 hours.

#### **Step 2: Define the "Hidden Crisis" (Month 3, Week 2 \- "The Demo Window")**

We inject a *correlated failure event* spanning 3 days.

* **Variable A (The Trigger):** Drop Humidity artificially.  
    
* *Logic:* For `Date` in \[Demo\_Day\_Minus\_3 to Demo\_Day\], Set Humidity \= `Mean 25%`.  
    
* **Variable B (The Reaction):** Spike Dust levels (simulating dry air kicking up particulate).  
    
* *Logic:* `Dust = (50 - Humidity) + Random_Noise`. (Result: Dust spikes to \~35µg/m³).  
    
* **Variable C (The Failure):** Spike AGV Error Codes.  
    
* *Logic:* IF `Dust > 30` THEN `AGV_Error_Probability = 15%`.  
    
* *Specifics:* Inject error code `AGV-ERR-99` ("Optical Sensor Obscured").  
    
* **Variable D (The Business Impact):** Starve the Line.  
    
* *Logic:* Every time `AGV_Error` occurs, insert a `STATE_CODE = 'STARVATION'` event in `EQUIPMENT_STATE_LOG` for 15 minutes.  
    
* *Logic:* Set associated Inventory Batches to `STOCK_TYPE = 'QUALITY_INSPECTION'` (simulating manual verification of the stuck AGV payload).

#### **Step 3: The Resulting "Data Story"**

When the user queries the data:

1. **Analyst** sees OPE drop from 85% to 60% on "Demo Day."  
2. **ML Model** sees a perfect correlation: Humidity   Dust   Failures .  
3. **Search** sees `AGV-ERR-99` and retrieves the manual explaining "Dust on Lidar lens."

### **4\. Implementation Note (Faker/Python)**

Use Python's `Faker` and `NumPy` for this.

* Generate the **Time Series** first (Humidity/Dust) at 5-minute intervals.  
* Generate the **Production Schedule**.  
* Simulate the **Execution**: Walk through the schedule. At each step, check the Time Series. If "Dusty", roll a die. If fail, log Error and log Starvation. If pass, log Production.

This ensures the data is mathematically consistent for the ML portion of the demo.  