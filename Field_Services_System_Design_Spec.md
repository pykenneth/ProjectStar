# Field Services Management System - Design Specification

## 1. Introduction and Overall Architecture

**Purpose:**
This document outlines the design specification for an integrated Field Services Management System. The system aims to streamline project execution from sales order intake to final project accounting, incorporating critical path analysis for scheduling, efficient resource allocation, field technician mobility with GIS tracking, real-time progress monitoring, and robust financial controls including variation order management and budget monitoring.

**High-Level Workflow Diagram:**
```mermaid
graph TD
    A[External Server: Sales Order] -- Excel/JSON Upload --> B(Sales Order Integration Module);
    B -- Parsed SO Data --> C{Project Generation};
    C -- Project ID & Particulars --> D[Project Repository];

    D -- Project Data --> E(Critical Path Analysis Engine);
    E -- CPA Suggestions (Tasks, Deadlines) --> F[Work Order Management Module];
    F -- Manual WO Creation & Scheduling (Tasks, Dependencies, Billing Info) --> G[Work Order Repository];
    D -- Project Timelines & Dependencies --> F;

    H[Technician Repository (Availability, Rating, Skills, Cost Rate)] --> I[Resource Allocation Module];
    G -- Work Orders (Schedule, Skills Needed) --> I;
    I -- Assigned Technicians --> G;

    G -- Assigned Tasks --> J[Technician Mobile Interface (PWA)];
    K[Gaode Maps API] -- GIS Data --> J;
    J -- Task Status Updates, GIS Check-in/out, Notes, (Optional: Time/Material Logs) --> G_LOGS[TaskUpdate Log];
    G_LOGS --> L[Real-time Reporting & Collaboration Module];
    G_LOGS --> WO_COSTS[Work Order Costing];

    D -- Project Data (Budget, Deadlines) --> L;
    G -- WO Data & Status (Operational & Billing) --> L;
    L -- Real-time Dashboards, Notifications, Communication --> M(Users: PMs, Admins, Technicians);
    
    VO_REQ[Variation Order Request] --> VO_MOD(Variation Order Management Module);
    VO_MOD -- Approved VO Impacts --> F;
    VO_MOD -- Approved VO Impacts --> FIN_MOD[Budget & Financial Module];
    VO_MOD -- VO Status --> L;

    SO_FIN[SO Financials] --> FIN_MOD;
    WO_BILLING[WO Billing Data] --> FIN_MOD;
    WO_COSTS --> FIN_MOD;
    EXP_LOG[Project Expense Log] --> FIN_MOD;
    FIN_MOD -- Financial Reports, Final Account --> M;
    FIN_MOD -- Budget vs. Actual --> L;

    subgraph Backend Services
        direction LR
        B; C; E; F; I; VO_MOD; FIN_MOD;
    end

    subgraph Frontend Interfaces
        direction LR
        J;
        PM_UI((PM Web Interface));
        TECH_UI((Technician Mobile PWA));
    end
    
    F --> PM_UI;
    I --> PM_UI;
    L --> PM_UI;
    VO_MOD --> PM_UI;
    FIN_MOD --> PM_UI;
    J --> TECH_UI;
```

## 2. Core Modules & Functionality

### 2.1. Sales Order Integration & Project Generation
*   **Input Methods:**
    1.  **File-based Upload (Single or Mass):**
        *   Supports standardized Excel multi-sheet format or equivalent JSON for structured Sales Order data.
        *   This method can be used for uploading a single Sales Order document or a file containing multiple Sales Order records (mass upload).
        *   **Mass upload functionality (processing a single file with multiple SOs) is restricted to Admin users.**
        *   The file format covers:
            *   `Project_Overview`: Client details, project address, contract dates, total value, general description for each SO.
            *   `Scope_FitOutWorks`, `Scope_FurnitureSupply`, `Scope_BuildingServices`: Itemized descriptions of work, specifications, initial duration estimates per SO.
            *   `Payment_Milestones`: Client payment schedule tied to project stages per SO.
            *   `Contractual_Terms`: Textual clauses for legal, responsibilities, etc., per SO.
    2.  **Manual Form-based Input (Ad-hoc Contracts):**
        *   A system-provided template/form within the application for manual entry of individual Sales Order details.
        *   Suitable for ad-hoc contracts or when a structured file is not available.
        *   This form will capture the same essential information as the file-based upload (Project Overview, Scope, Payment Milestones, Terms).
*   **Data Mapping & Project Generation:**
    *   A backend service (`SalesOrderService`) processes input from **either** file uploads (single or mass) or manual form submissions.
    *   For file uploads, the service parses the document. For manual input, it receives structured data directly from the form.
    *   A new `Project` entity is created, populated with overview data. A unique project ID is generated.
    *   `ProjectPaymentMilestone` records are created based on the input.
    *   Contractual terms and initial scope items (from `Scope_*` sections or form fields) are stored with the `Project` for reference by the PM.
*   **Key Data Models:**
    *   `SalesOrder`: Stores reference to original SO document (if applicable), parsed/inputted SO data, and a link to the generated `Project`.
    *   `Project`: Core entity holding client information, project deadlines, contract value, parsed contractual terms, and an initial scope summary.
    *   `ProjectPaymentMilestone`: Tracks the client payment schedule as defined in the Sales Order.
*   **Reasoning for Metadata:**
    *   To accurately capture all contractual obligations and foundational project details from client agreements, whether received as files or entered manually.
    *   To provide a structured and consistent starting point for detailed internal project planning by the Project Manager.
    *   Ensures critical financial parameters (contract value, payment terms) and initial scope are recorded upfront for every project.

### 2.2. Work Order Management & Task Definition
*   **PM's Role:** The PM reviews the `initial_scope_summary` (from SO) and creates a detailed Work Breakdown Structure (WBS) by defining granular `Task` (Work Order) entities.
*   **Detailed Task Creation:** For each `Task`, the PM defines: name, detailed description, estimated duration, and (later) assigns resources and billing info.
*   **Dependency Management:** Crucially, the PM establishes dependencies between `Task`s (e.g., Finish-to-Start, Start-to-Start, with lag/lead times).
*   **Key Data Models:**
    *   `Task` (Work Order): Operational fields like `name`, `description`, `status`, `duration_estimate`, `project_id`, CPA-calculated schedule fields (`earliest_start`, `latest_start`, etc.), `is_critical`.
    *   `TaskDependency`: Links `predecessor_task_id` to `successor_task_id`, specifying `dependency_type` and `lag_hours`.
*   **Reasoning for Metadata:**
    *   To enable detailed, actionable project planning beyond the high-level scope in the SO.
    *   Precise task definitions and dependencies are essential inputs for accurate Critical Path Analysis.

### 2.3. Critical Path Analysis (CPA) Engine
*   **Core Logic:** A backend service (`CPAService`) performs:
    1.  **Forward Pass:** Calculates Earliest Start (ES) and Earliest Finish (EF) for all tasks.
    2.  **Backward Pass:** Calculates Latest Start (LS) and Latest Finish (LF) for all tasks, constrained by the `Project.order_deadline`.
    3.  **Slack Calculation:** Determines float (`LS - ES`) for each task.
    4.  **Critical Path Identification:** Tasks with zero (or minimal) slack form the critical path(s).
*   **Inputs:** Project's `Task` list with durations and `TaskDependency` network.
*   **Outputs:** Updates `Task` records with ES, EF, LS, LF, slack, and `is_critical` flag.
*   **Triggers:** Invoked by PM after defining/modifying tasks/dependencies, or when significant project changes occur (e.g., approved VO).
*   **Reasoning for Metadata:**
    *   Provides essential scheduling intelligence, highlighting tasks that directly impact the project deadline.
    *   Guides PMs in prioritizing work and managing resources effectively.
    *   Helps in proactive risk management by identifying tasks with no room for delay.

### 2.4. Work Order Billing Management
*   **Integration:** PMs manage billing aspects when creating/editing `Task` (Work Orders).
*   **Key Data Models:**
    *   `Task` (Extended): Includes `billable_type` ("Fixed Price", "Time & Materials"), `fixed_price_amount`, `hourly_rate`, `estimated_billable_hours`, `actual_billable_hours`, `materials_cost`, `total_billable_amount` (calculated), `billing_status` ("Ready for Invoice", "Invoiced", "Paid"), `invoice_reference`.
*   **PM's Workflow:** Define billing parameters per WO, track billable hours/costs, update billing status.
*   **Reasoning for Metadata:**
    *   Enables granular tracking of revenue generated by each work unit.
    *   Facilitates accurate invoicing and financial reporting at the WO level.
    *   Supports linking work done to client billing.

### 2.5. Variation Order (VO) Management
*   **VO Application:** PMs or authorized users can initiate VOs during project execution, detailing scope changes, reasons, and estimated impacts.
*   **Approval Workflow:** Configurable approval process (internal and/or client) with status tracking ("Draft", "Pending Approval", "Approved", "Rejected").
*   **Document Management:** Upload and associate supporting documents (sketches, quotes, client requests) with each VO.
*   **Impact Integration:** Approved VOs trigger PM actions:
    *   Update `Task` durations, add/remove tasks, adjust dependencies. **CPA must be re-run.**
    *   Adjust `Task` billing details and potentially `Project` contract value.
*   **Key Data Models:**
    *   `VariationOrder`: Stores VO details, status, impacts, approval history.
    *   `VariationOrderDocument`: Links documents to VOs.
*   **Reasoning for Metadata:**
    *   Provides a formal, auditable process for managing scope changes.
    *   Ensures impacts of changes on schedule and budget are assessed and approved.
    *   Maintains a clear record of all variations for contractual and historical purposes.

### 2.6. Resource (Technician) Allocation
*   **Technician Profiling:** Manage technician details including `skills`, `rating`, `availability_status`, and detailed availability slots in `TechnicianAvailabilityLog`.
*   **Matching Logic (`ResourceAllocationService`):**
    *   Filters technicians by `required_skills` for a `Task`.
    *   Checks availability against the task's CPA-derived feasible window (ES-LF).
    *   Ranks suitable technicians (e.g., by rating, availability proximity to ES).
*   **Assignment:** PM assigns a technician and confirms `scheduled_start_datetime` (respecting CPA). System updates task and technician availability.
*   **Key Data Models:**
    *   `Technician`: Profile, skills, rating, overall availability, `internal_cost_rate_per_hour`.
    *   `TechnicianAvailabilityLog`: Granular calendar of available, booked, leave slots.
    *   `Task`: `assigned_technician_id`, `required_skills`, `scheduled_start_datetime`, `scheduled_end_datetime`.
*   **Reasoning for Metadata:**
    *   To ensure the right technician with the right skills is assigned to tasks.
    *   To optimize resource utilization by considering availability and CPA schedule constraints.
    *   To provide PMs with tools for effective team scheduling and workload management.

### 2.7. Budget Monitoring & Final Account Statement
*   **Project Budget Setup:** PM defines `Project.estimated_total_cost_budget`.
*   **Expense Tracking:**
    *   **Labor Costs:** Calculated from `Task.actual_billable_hours` (or logged time) and `Technician.internal_cost_rate_per_hour`, stored in `Task.actual_internal_cost`.
    *   **Material/Subcontractor Costs:** Logged against `Task`s or as general `ProjectExpense`s.
    *   **General Expenses:** Logged via `ProjectExpense` model with categorization.
*   **Cost Aggregation:** `Project.actual_total_cost` is a sum of all task costs and general project expenses.
*   **Final Account Statement:** Report summarizing:
    *   **Revenue:** Contract value + billable VOs.
    *   **Expenses:** Detailed breakdown of `actual_total_cost` by category.
    *   **Profitability:** Revenue vs. Expenses, profit margin %.
    *   **Budget vs. Actual:** Comparison and variance.
*   **PM Performance KPI Link:** While PMs are evaluated on project profitability and budget adherence, these feed into broader business intelligence. The system will track data to support these evaluations.
*   **Key Data Models:**
    *   `Project`: `total_contract_value`, `estimated_total_cost_budget`, `actual_total_cost`, profitability fields.
    *   `Task`: `estimated_internal_cost`, `actual_internal_cost` (broken down if needed).
    *   `ProjectExpense`: For categorized, non-WO specific, or detailed expenses.
*   **Reasoning for Metadata:**
    *   Provides comprehensive financial control over projects.
    *   Enables real-time tracking of expenditure against budget.
    *   Generates essential financial reports for project review and PM performance evaluation.

### 2.8. Technician Mobile Interface & GIS Integration
*   **Approach:** Progressive Web App (PWA) using React for mobile accessibility.
*   **Key Features:**
    *   View assigned tasks and details.
    *   Update task status (e.g., "In Progress", "Completed").
    *   GIS-based site check-in/check-out using device GPS (Gaode Maps for context/validation).
    *   Add notes, optionally upload photos related to tasks.
    *   Offline data caching and update syncing.
*   **Backend API Support:** Secure endpoints for all technician actions.
*   **Key Data Models:**
    *   `TaskUpdate`: Central log for all technician field interactions (status changes, check-ins/outs, notes, GIS coordinates, timestamps).
    *   `Technician`: Stores `current_latitude`, `current_longitude`, `last_location_update`.
*   **Reasoning for Metadata:**
    *   Empowers field technicians with necessary information and tools.
    *   Captures accurate, real-time data directly from the field, including location verification.
    *   Improves data accuracy for progress tracking and reduces manual reporting.

### 2.9. Real-time Reporting & Collaboration
*   **Technology:** Django Channels (WebSockets) for backend-to-frontend real-time communication.
*   **Live Dashboards:** PMs view real-time updates on project health, task statuses, technician locations (optional map), budget consumption.
*   **Project Activity Feeds:** Chronological log of important project events (task updates, VOs, check-ins).
*   **Notification System:** In-app (and optional email) alerts for critical events (assignments, issues, approvals needed).
*   **Collaboration:** Notes/comments on tasks facilitate communication between PMs and technicians.
*   **Reasoning for Metadata:**
    *   Enhances situational awareness for all stakeholders.
    *   Facilitates proactive decision-making by providing immediate insights into project progress and issues.
    *   Improves team communication and coordination.

## 3. Summary of Key Data Models and Rationale

*   **`Project`**: Central entity; holds contractual data, overall budget, deadlines, links to all other project-specific data. *Rationale: Foundation for all project activities.*
*   **`SalesOrder`**: Captures initial client agreement details and links to the generated `Project`. *Rationale: Audit trail and source of initial project parameters.*
*   **`ProjectPaymentMilestone`**: Tracks client payment schedule as per contract. *Rationale: Manages project cash inflow expectations.*
*   **`Task` (Work Order)**: Granular unit of work; contains operational details, CPA schedule, resource assignment, billing information, and cost tracking. *Rationale: Core for planning, execution, scheduling, billing, and costing.*
*   **`TaskDependency`**: Defines relationships between tasks. *Rationale: Essential for CPA calculation and realistic scheduling.*
*   **`Technician`**: Stores technician profiles, skills, availability, ratings, and cost rates. *Rationale: Enables effective resource management and costing.*
*   **`TechnicianAvailabilityLog`**: Detailed calendar for technician availability. *Rationale: Accurate resource scheduling.*
*   **`VariationOrder`**: Manages scope changes, approvals, and impacts. *Rationale: Formalizes change control.*
*   **`VariationOrderDocument`**: Stores documents supporting VOs. *Rationale: Auditability and record-keeping for changes.*
*   **`ProjectExpense`**: Logs general or detailed project costs not tied to specific WO internal costs. *Rationale: Comprehensive expense tracking for accurate final accounting.*
*   **`TaskUpdate`**: Audit trail for all technician field activities, notes, and GIS data. *Rationale: Real-time field data capture, progress tracking, and accountability.*

## 4. Next Steps
This design specification provides a comprehensive blueprint for the Field Services Management System. The next step would be to prioritize modules for phased development and begin the implementation process, starting with core models and foundational functionalities.

---

## 5. Ultimate Business Intelligence KPIs

Beyond individual PM performance metrics, the system is designed to provide data for the following ultimate Key Performance Indicators (KPIs) for overall business intelligence:

1.  **On-Time Project Completion:**
    *   **Metric:** Percentage of projects completed by their `order_deadline` (or adjusted deadline after approved VOs).
    *   **Data Points:** `Project.order_deadline`, `Project.actual_end_date` (derived from last task completion), status of VOs impacting schedule.
    *   **Rationale:** Measures operational efficiency and ability to meet client commitments.

2.  **Within-Budget Project Completion:**
    *   **Metric:** Percentage of projects completed where `Project.actual_total_cost` is less than or equal to `Project.estimated_total_cost_budget` (adjusted for cost impacts of approved VOs).
    *   **Data Points:** `Project.estimated_total_cost_budget`, `Project.actual_total_cost`, cost implications from `VariationOrder`s.
    *   **Rationale:** Measures financial control, cost management effectiveness, and overall project profitability.

These two overarching KPIs will be critical outputs of the system's reporting and analytics capabilities, allowing the business to assess overall performance and identify areas for strategic improvement.
