# TXT Records Management

<cite>
**Referenced Files in This Document**
- [states.py](file://app/modules/domains/states.py)
- [keyboards.py](file://app/modules/domains/keyboards.py)
- [router.py](file://app/modules/domains/router.py)
- [dns.py](file://app/services/beget/dns.py)
- [types.py](file://app/services/beget/types.py)
- [client.py](file://app/services/beget/client.py)
- [README.md](file://README.md)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)

## Introduction
This document provides comprehensive guidance for managing TXT DNS records within the Beget Manager Telegram bot. It covers the end-to-end workflow for viewing TXT records, adding new TXT records, and deleting existing TXT records. It explains the finite state machine (FSM) state management used to persist data across multi-step operations, the keyboard interfaces for record selection and deletion, text validation requirements, and the handling of long TXT record values with truncation for display purposes. Finally, it documents the integration with the DnsService.add_txt_record() and delete_txt_record() methods.

## Project Structure
The TXT records management functionality is implemented across several modules:
- Router handlers orchestrate user interactions and state transitions
- FSM states define the multi-step workflows
- Keyboard builders construct interactive menus for record selection and confirmation
- Service layer handles communication with the Beget DNS API
- Type definitions model DNS records and data structures

```mermaid
graph TB
subgraph "Telegram Bot UI"
Router["Router Handlers<br/>router.py"]
Keyboards["Keyboard Builders<br/>keyboards.py"]
States["FSM States<br/>states.py"]
end
subgraph "Business Logic"
DnsService["DNS Service<br/>dns.py"]
Types["Type Definitions<br/>types.py"]
end
subgraph "External API"
BegetClient["Beget API Client<br/>client.py"]
end
Router --> Keyboards
Router --> States
Router --> DnsService
DnsService --> BegetClient
DnsService --> Types
```

**Diagram sources**
- [router.py](file://app/modules/domains/router.py#L1-L718)
- [keyboards.py](file://app/modules/domains/keyboards.py#L1-L196)
- [states.py](file://app/modules/domains/states.py#L1-L21)
- [dns.py](file://app/services/beget/dns.py#L1-L152)
- [types.py](file://app/services/beget/types.py#L1-L59)
- [client.py](file://app/services/beget/client.py#L1-L135)

**Section sources**
- [router.py](file://app/modules/domains/router.py#L1-L718)
- [keyboards.py](file://app/modules/domains/keyboards.py#L1-L196)
- [states.py](file://app/modules/domains/states.py#L1-L21)
- [dns.py](file://app/services/beget/dns.py#L1-L152)
- [types.py](file://app/services/beget/types.py#L1-L59)
- [client.py](file://app/services/beget/client.py#L1-L135)

## Core Components
- FSM States for TXT operations:
  - waiting_txt_value: Captures the TXT record value during creation
  - confirm_delete_record: Confirms deletion of a selected TXT record
- Keyboard builders:
  - dns_menu_keyboard: Provides navigation to TXT records
  - txt_records_keyboard: Lists TXT records with truncated display
  - confirm_keyboard: Generic confirmation interface for destructive actions
- Router handlers:
  - show_txt_records: Loads TXT records and stores them in state
  - show_txt_record_detail: Displays a selected TXT record and deletion options
  - start_add_txt_record: Initiates TXT creation workflow
  - receive_txt_value: Validates and persists the new TXT record
  - do_delete_txt: Confirms and deletes the selected TXT record
- Service layer:
  - DnsService.add_txt_record(): Adds a TXT record via Beget API
  - DnsService.delete_txt_record(): Removes a TXT record via Beget API
- Type definitions:
  - DnsRecord: Represents a DNS record with value and priority
  - DnsData: Aggregates DNS records for a domain

**Section sources**
- [states.py](file://app/modules/domains/states.py#L14-L21)
- [keyboards.py](file://app/modules/domains/keyboards.py#L105-L196)
- [router.py](file://app/modules/domains/router.py#L589-L718)
- [dns.py](file://app/services/beget/dns.py#L134-L152)
- [types.py](file://app/services/beget/types.py#L28-L59)

## Architecture Overview
The TXT records workflow follows a clear sequence: user selects TXT management, the bot loads records and displays them, the user chooses an action (view or add), and the bot performs the operation using the service layer.

```mermaid
sequenceDiagram
participant User as "Telegram User"
participant Router as "Router Handler<br/>router.py"
participant State as "FSM State<br/>states.py"
participant Service as "DnsService<br/>dns.py"
participant API as "Beget API Client<br/>client.py"
User->>Router : "TXT Records" menu selection
Router->>Service : get_dns_data(fqdn)
Service->>API : request("dns/getData", params)
API-->>Service : DNS data (records)
Service-->>Router : DnsData with TXT records
Router->>State : Store TXT records in state
Router-->>User : Display TXT records with truncated values
User->>Router : "Add TXT Record"
Router->>State : Set waiting_txt_value
Router-->>User : Prompt for TXT value
User->>Router : TXT value
Router->>Service : add_txt_record(fqdn, value)
Service->>API : request("dns/changeRecords", params)
API-->>Service : Success
Service-->>Router : True
Router-->>User : Confirmation message
User->>Router : "Delete TXT Record"
Router->>State : Retrieve stored TXT records
Router-->>User : Confirmation prompt
User->>Router : Confirm deletion
Router->>Service : delete_txt_record(fqdn, value)
Service->>API : request("dns/changeRecords", params)
API-->>Service : Success
Service-->>Router : True
Router-->>User : Deletion confirmation
```

**Diagram sources**
- [router.py](file://app/modules/domains/router.py#L589-L718)
- [states.py](file://app/modules/domains/states.py#L14-L21)
- [dns.py](file://app/services/beget/dns.py#L134-L152)
- [client.py](file://app/services/beget/client.py#L70-L121)

## Detailed Component Analysis

### State Management for TXT Operations
- Purpose: Persist multi-step data across user interactions without requiring persistent storage.
- Key states:
  - waiting_txt_value: Captures the TXT value during creation.
  - confirm_delete_record: Used for confirming deletion actions.
- Persistence mechanism:
  - During TXT record listing, the router stores the current TXT record values in state for later reference during deletion.
  - During creation, the router sets the waiting_txt_value state and clears it upon completion.

```mermaid
stateDiagram-v2
[*] --> Idle
Idle --> WaitingTxtValue : "start_add_txt_record"
WaitingTxtValue --> Idle : "receive_txt_value success"
WaitingTxtValue --> Idle : "receive_txt_value error"
Idle --> ConfirmDeleteRecord : "show_txt_record_detail"
ConfirmDeleteRecord --> Idle : "do_delete_txt confirmed"
ConfirmDeleteRecord --> Idle : "do_delete_txt canceled"
```

**Diagram sources**
- [states.py](file://app/modules/domains/states.py#L14-L21)
- [router.py](file://app/modules/domains/router.py#L650-L718)

**Section sources**
- [states.py](file://app/modules/domains/states.py#L14-L21)
- [router.py](file://app/modules/domains/router.py#L603-L621)
- [router.py](file://app/modules/domains/router.py#L665-L686)
- [router.py](file://app/modules/domains/router.py#L688-L718)

### Keyboard Interfaces for TXT Records
- TXT records list:
  - Displays truncated TXT values (first 30 characters) to fit within Telegram button width.
  - Provides navigation to add new TXT records and back to DNS menu.
- Record detail and deletion:
  - Shows the full TXT value for confirmation.
  - Offers confirm/cancel options using a generic keyboard.

```mermaid
flowchart TD
Start(["TXT Records Menu"]) --> List["Display TXT Records<br/>with truncated values"]
List --> Add["+ Add TXT Record"]
List --> Detail["Select Record"]
Detail --> View["View Full Value"]
Detail --> Delete["Delete Confirmation"]
Add --> Input["Enter TXT Value"]
Input --> Submit["Submit to Service"]
Submit --> Done(["Done"])
View --> Back["Back to List"]
Delete --> Confirm["Confirm/Cancel"]
Confirm --> |Confirm| SubmitDel["Submit to Service"]
Confirm --> |Cancel| Back
SubmitDel --> Done
Back --> List
```

**Diagram sources**
- [keyboards.py](file://app/modules/domains/keyboards.py#L142-L162)
- [router.py](file://app/modules/domains/router.py#L624-L648)
- [router.py](file://app/modules/domains/router.py#L650-L686)
- [router.py](file://app/modules/domains/router.py#L688-L718)

**Section sources**
- [keyboards.py](file://app/modules/domains/keyboards.py#L142-L162)
- [router.py](file://app/modules/domains/router.py#L624-L648)
- [router.py](file://app/modules/domains/router.py#L650-L686)
- [router.py](file://app/modules/domains/router.py#L688-L718)

### Text Validation Requirements
- TXT value acceptance:
  - Non-empty values are required.
  - The handler rejects empty inputs and requests a retry.
- Long TXT value handling:
  - Display truncation: Buttons show the first 30 characters followed by an ellipsis.
  - Full value preservation: The service stores and operates on the complete value.
- Priority assignment:
  - TXT records are assigned ascending priorities (multiples of 10) during addition and updates.

```mermaid
flowchart TD
Start(["Receive TXT Value"]) --> Validate{"Non-empty?"}
Validate --> |No| Retry["Prompt for valid value"]
Validate --> |Yes| Store["Store in state and service"]
Store --> Done(["Complete"])
Retry --> Start
```

**Diagram sources**
- [router.py](file://app/modules/domains/router.py#L665-L686)
- [keyboards.py](file://app/modules/domains/keyboards.py#L146-L154)
- [dns.py](file://app/services/beget/dns.py#L134-L152)

**Section sources**
- [router.py](file://app/modules/domains/router.py#L665-L686)
- [keyboards.py](file://app/modules/domains/keyboards.py#L146-L154)
- [dns.py](file://app/services/beget/dns.py#L134-L152)

### Workflow: Viewing TXT Records
- Navigation: From the DNS menu, select "TXT Records".
- Loading: The router fetches DNS data and extracts TXT records.
- Display: The router builds a numbered list with truncated values and navigational buttons.
- State persistence: The router stores the current TXT record values in state for subsequent operations.

```mermaid
sequenceDiagram
participant User as "User"
participant Router as "show_txt_records"
participant Service as "DnsService"
participant State as "FSM State"
User->>Router : "dns_txt : fqdn"
Router->>Service : get_dns_data(fqdn)
Service-->>Router : DnsData with TXT records
Router->>State : Update txt_records and fqdn
Router-->>User : Display TXT records with truncated values
```

**Diagram sources**
- [router.py](file://app/modules/domains/router.py#L589-L622)
- [dns.py](file://app/services/beget/dns.py#L14-L77)

**Section sources**
- [router.py](file://app/modules/domains/router.py#L589-L622)

### Workflow: Adding a New TXT Record
- Initiation: Select "+ Add TXT Record" from the TXT records list.
- Capture: The router sets the waiting_txt_value state and prompts the user for the TXT value.
- Validation: The handler ensures the value is non-empty.
- Execution: The router calls DnsService.add_txt_record() with the FQDN and value.
- Completion: The router clears state and confirms success.

```mermaid
sequenceDiagram
participant User as "User"
participant Router as "start_add_txt_record/receive_txt_value"
participant Service as "DnsService.add_txt_record"
participant API as "Beget API"
User->>Router : "+ Add TXT Record"
Router->>Router : Set waiting_txt_value
Router-->>User : "Enter TXT record value"
User->>Router : "TXT value"
Router->>Service : add_txt_record(fqdn, value)
Service->>API : request("dns/changeRecords", params)
API-->>Service : Success
Service-->>Router : True
Router-->>User : "TXT record added!"
```

**Diagram sources**
- [router.py](file://app/modules/domains/router.py#L650-L686)
- [dns.py](file://app/services/beget/dns.py#L134-L140)
- [client.py](file://app/services/beget/client.py#L70-L121)

**Section sources**
- [router.py](file://app/modules/domains/router.py#L650-L686)
- [dns.py](file://app/services/beget/dns.py#L134-L140)

### Workflow: Deleting an Existing TXT Record
- Selection: Choose a TXT record from the list.
- Detail: The router retrieves the full value from state and displays it with confirmation options.
- Confirmation: The user confirms deletion.
- Execution: The router calls DnsService.delete_txt_record() with the FQDN and the exact value to remove.
- Completion: The router clears state and refreshes the TXT records list.

```mermaid
sequenceDiagram
participant User as "User"
participant Router as "show_txt_record_detail/do_delete_txt"
participant Service as "DnsService.delete_txt_record"
participant API as "Beget API"
User->>Router : "txt_record : fqdn : index"
Router->>Router : Load full value from state
Router-->>User : "TXT Record : value"
User->>Router : "Confirm"
Router->>Service : delete_txt_record(fqdn, value)
Service->>API : request("dns/changeRecords", params)
API-->>Service : Success
Service-->>Router : True
Router-->>User : "TXT record deleted!"
```

**Diagram sources**
- [router.py](file://app/modules/domains/router.py#L624-L648)
- [router.py](file://app/modules/domains/router.py#L688-L718)
- [dns.py](file://app/services/beget/dns.py#L142-L152)
- [client.py](file://app/services/beget/client.py#L70-L121)

**Section sources**
- [router.py](file://app/modules/domains/router.py#L624-L648)
- [router.py](file://app/modules/domains/router.py#L688-L718)
- [dns.py](file://app/services/beget/dns.py#L142-L152)

### Integration with DnsService Methods
- add_txt_record():
  - Retrieves current TXT records
  - Assigns ascending priorities
  - Calls change_records() to apply the update
- delete_txt_record():
  - Retrieves current TXT records
  - Excludes the target value
  - Calls change_records() to apply the update

```mermaid
classDiagram
class DnsService {
+get_dns_data(fqdn) DnsData
+change_records(fqdn, records) bool
+add_txt_record(fqdn, value) bool
+delete_txt_record(fqdn, value) bool
}
class DnsData {
+string fqdn
+DnsRecord[] txt
}
class DnsRecord {
+string value
+int priority
}
DnsService --> DnsData : "returns"
DnsData --> DnsRecord : "contains"
```

**Diagram sources**
- [dns.py](file://app/services/beget/dns.py#L8-L152)
- [types.py](file://app/services/beget/types.py#L35-L59)

**Section sources**
- [dns.py](file://app/services/beget/dns.py#L134-L152)
- [types.py](file://app/services/beget/types.py#L28-L59)

## Dependency Analysis
The TXT records management depends on:
- Router handlers for user interaction and state orchestration
- FSM states for multi-step persistence
- Keyboard builders for UI construction
- Service layer for API integration
- Type definitions for data modeling

```mermaid
graph TB
Router["router.py"] --> States["states.py"]
Router --> Keyboards["keyboards.py"]
Router --> DnsService["dns.py"]
DnsService --> Types["types.py"]
DnsService --> Client["client.py"]
```

**Diagram sources**
- [router.py](file://app/modules/domains/router.py#L1-L718)
- [states.py](file://app/modules/domains/states.py#L1-L21)
- [keyboards.py](file://app/modules/domains/keyboards.py#L1-L196)
- [dns.py](file://app/services/beget/dns.py#L1-L152)
- [types.py](file://app/services/beget/types.py#L1-L59)
- [client.py](file://app/services/beget/client.py#L1-L135)

**Section sources**
- [router.py](file://app/modules/domains/router.py#L1-L718)
- [states.py](file://app/modules/domains/states.py#L1-L21)
- [keyboards.py](file://app/modules/domains/keyboards.py#L1-L196)
- [dns.py](file://app/services/beget/dns.py#L1-L152)
- [types.py](file://app/services/beget/types.py#L1-L59)
- [client.py](file://app/services/beget/client.py#L1-L135)

## Performance Considerations
- Display truncation: Limiting TXT display to 30 characters reduces button width and improves readability.
- State usage: Storing TXT values in state avoids repeated API calls for selection and deletion.
- Priority assignment: Sequential priority assignment simplifies ordering and avoids conflicts.
- API round-trips: The router minimizes redundant calls by fetching DNS data once per session and reusing state.

## Troubleshooting Guide
- Empty TXT value:
  - Symptom: User input rejected with a retry prompt.
  - Resolution: Ensure the TXT value is non-empty before submission.
- Record not found during deletion:
  - Symptom: Alert indicating the record was not found.
  - Resolution: Verify the index is valid and the state contains the current TXT records.
- API errors:
  - Symptom: Errors raised by the Beget API client.
  - Resolution: Check credentials, network connectivity, and API limits; review logs for detailed error messages.
- Timeout errors:
  - Symptom: Request timeout while communicating with the API.
  - Resolution: Increase timeout settings if necessary and retry the operation.

**Section sources**
- [router.py](file://app/modules/domains/router.py#L665-L686)
- [router.py](file://app/modules/domains/router.py#L688-L718)
- [client.py](file://app/services/beget/client.py#L118-L121)

## Conclusion
The TXT records management feature provides a robust, user-friendly workflow for viewing, adding, and deleting TXT DNS records. It leverages FSM states for reliable multi-step operations, keyboard builders for intuitive navigation, and a service layer that integrates seamlessly with the Beget DNS API. Display truncation ensures usability, while strict validation and state persistence improve reliability. The documented workflows and integration points enable maintainability and future enhancements.