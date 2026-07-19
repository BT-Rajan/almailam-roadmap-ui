# 06 - Mock Data Dictionary

**Project:** ServiceOS  
**Client:** Almailam Engineering Consultants

---

# Purpose

This document defines the mock data used throughout the Vue frontend prototype.

The objective is consistency.

Every screen, component and workflow must use these entities.

When the backend is developed, these entities become the database models and API contracts.

---

# Design Principles

The mock data should be:

- Small
- Realistic
- Consistent
- Reusable
- Relational

Avoid creating duplicate or isolated data.

---

# Entity Relationships

```
Client
   │
   ├── Projects
   │      │
   │      ├── Documents
   │      ├── Tasks
   │      ├── Quotations
   │      ├── Contracts
   │      ├── Government Submissions
   │      └── Activities
   │
   └── Contacts

Government Submission
        │
        ├── Government Forms
        └── Authorities

Project
        │
        ├── Assigned Users
        ├── AI Reviews
        ├── Notifications
        └── Timeline
```

---

# Client

Represents the customer.

## Fields

| Field | Type |
|--------|------|
| id | String |
| code | String |
| companyName | String |
| contactPerson | String |
| mobile | String |
| email | String |
| city | String |
| status | Active / Inactive |

Sample Records

5

---

# Project

Represents one consulting engagement.

## Fields

| Field | Type |
|--------|------|
| id | String |
| projectNo | String |
| projectName | String |
| clientId | String |
| service | String |
| engineer | String |
| currentStage | String |
| progress | Number |
| priority | String |
| startDate | Date |
| targetDate | Date |
| status | String |

Stages

- Enquiry
- Quotation
- Contract
- Design
- Government Submission
- Correction
- Approval
- Completed

Sample Records

5

---

# User

Application user.

## Fields

| Field | Type |
|--------|------|
| id | String |
| name | String |
| designation | String |
| email | String |
| mobile | String |
| role | String |
| avatar | String |
| status | Active / Inactive |

Roles

- Administrator
- Project Manager
- Engineer
- Document Controller
- Viewer

Sample Records

5

---

# Document

Project document.

## Fields

| Field | Type |
|--------|------|
| id | String |
| projectId | String |
| title | String |
| type | String |
| revision | String |
| uploadedBy | String |
| uploadDate | Date |
| status | String |

Document Types

- Drawing
- Report
- Contract
- Quotation
- Municipality Form
- Calculation Sheet

Sample Records

10

---

# Government Authority

Government department.

## Fields

| Field | Type |
|--------|------|
| id | String |
| name | String |
| category | String |
| website | String |
| description | String |

Sample Records

5

Examples

- Municipality
- Fire Department
- Electricity
- Water
- Environment

---

# Government Form

Official submission form.

## Fields

| Field | Type |
|--------|------|
| id | String |
| authorityId | String |
| formCode | String |
| title | String |
| version | String |
| language | String |
| category | String |
| description | String |
| requiredDocuments | Array |

Sample Records

8

---

# Government Submission

Tracks authority submissions.

## Fields

| Field | Type |
|--------|------|
| id | String |
| projectId | String |
| authorityId | String |
| submittedDate | Date |
| currentStatus | String |
| assignedOfficer | String |
| remarks | String |

Status

- Draft
- Submitted
- Under Review
- Correction Required
- Approved
- Rejected

Sample Records

5

---

# Task

Project work item.

## Fields

| Field | Type |
|--------|------|
| id | String |
| projectId | String |
| title | String |
| assignedTo | String |
| priority | String |
| dueDate | Date |
| status | String |

Priority

- High
- Medium
- Low

Status

- Pending
- In Progress
- Completed

Sample Records

10

---

# Quotation

Commercial proposal.

## Fields

| Field | Type |
|--------|------|
| id | String |
| projectId | String |
| quotationNo | String |
| amount | Number |
| issueDate | Date |
| validity | Date |
| status | String |

Sample Records

3

---

# Contract

Customer agreement.

## Fields

| Field | Type |
|--------|------|
| id | String |
| projectId | String |
| contractNo | String |
| signedDate | Date |
| expiryDate | Date |
| status | String |

Sample Records

3

---

# Workflow Template

Defines project stages.

## Fields

| Field | Type |
|--------|------|
| id | String |
| name | String |
| stages | Array |

Sample Records

3

---

# Activity

Audit timeline entry.

## Fields

| Field | Type |
|--------|------|
| id | String |
| projectId | String |
| date | Date |
| user | String |
| activity | String |

Sample Records

20

---

# Notification

Application notification.

## Fields

| Field | Type |
|--------|------|
| id | String |
| title | String |
| message | String |
| category | String |
| date | Date |
| read | Boolean |

Categories

- Project
- Task
- Government
- AI
- System

Sample Records

8

---

# AI Prompt

User request to AI.

## Fields

| Field | Type |
|--------|------|
| id | String |
| module | String |
| prompt | String |
| response | String |
| confidence | Number |

Modules

- Project
- Document
- Contract
- Government Form
- Customer Update

Sample Records

5

---

# Report

Dashboard report.

## Fields

| Field | Type |
|--------|------|
| id | String |
| title | String |
| category | String |
| description | String |

Sample Records

3

---

# Customer Status Record

Public project tracking.

## Fields

| Field | Type |
|--------|------|
| mobile | String |
| projectId | String |
| projectName | String |
| currentStage | String |
| progress | Number |
| latestUpdate | String |
| pendingAction | String |

Sample Records

3

---

# Lookup Values

These should be maintained as reusable constants.

## Project Status

- Active
- On Hold
- Completed
- Cancelled

---

## Workflow Stage

- Enquiry
- Quotation
- Contract
- Design
- Government Submission
- Review
- Correction
- Approval
- Completed

---

## Priority

- High
- Medium
- Low

---

## Task Status

- Pending
- In Progress
- Completed

---

## Submission Status

- Draft
- Submitted
- Under Review
- Correction Required
- Approved
- Rejected

---

## Roles

- Administrator
- Project Manager
- Engineer
- Document Controller
- Viewer

---

## Document Types

- Drawing
- Report
- Contract
- Quotation
- Form
- Letter
- Calculation Sheet

---

# Mock Data Rules

- Keep the dataset intentionally small.
- Every Project belongs to one Client.
- Every Document belongs to one Project.
- Every Task belongs to one Project.
- Every Submission belongs to one Project.
- Every Government Form belongs to one Authority.
- Every Quotation and Contract belong to one Project.
- IDs must remain stable across all mock files.
- All pages should reuse the same mock data source.

---

# Success Criteria

The mock dataset should:

- Demonstrate every screen and workflow.
- Maintain realistic relationships between entities.
- Avoid duplicated or conflicting records.
- Be easily replaceable by REST API responses without changing the frontend components.