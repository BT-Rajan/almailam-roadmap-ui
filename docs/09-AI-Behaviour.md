# 09 - AI Behaviour

**Project:** ServiceOS  
**Client:** Almailam Engineering Consultants

**Version:** 1.0

---

# Purpose

This document defines how Artificial Intelligence is used throughout ServiceOS.

AI is an **assistant**, not the application itself.

Every business workflow must function normally even when AI is disabled.

---

# Design Philosophy

ServiceOS is an Engineering Consultancy Management System.

AI enhances productivity by reducing manual work.

It does **not** replace engineering judgement, approvals or business decisions.

The user is always responsible for the final outcome.

---

# AI Characteristics

The AI should behave like an experienced engineering consultant.

It should

- Explain
- Summarize
- Organize
- Suggest
- Draft
- Translate
- Extract
- Improve

It should never

- Automatically approve
- Modify project data
- Delete records
- Submit government forms
- Make business decisions
- Execute irreversible actions

---

# AI Providers

ServiceOS supports configurable AI providers.

Initially

- Claude API
- DeepSeek API

Future providers can be added without UI changes.

Examples

- OpenAI
- Gemini
- Azure OpenAI
- Local LLM

Provider selection is configurable by the administrator.

---

# AI Configuration

Located in

```
Administration

↓

AI Configuration
```

Configuration includes

- Enable / Disable AI
- Default Provider
- Provider Priority
- API Keys
- Default Model
- Timeout
- Maximum Tokens
- Temperature
- Cache Duration
- Prompt Templates

---

# AI Availability

AI is optional.

If AI is disabled

- All business modules continue functioning normally.
- AI buttons are hidden or disabled.
- No workflow should fail.

The application must never depend on AI availability.

---

# AI Usage Areas

## Projects

AI can

- Summarize project status
- Suggest next steps
- Highlight delays
- Identify missing documents
- Generate customer updates

---

## Documents

AI can

- Read uploaded documents
- Extract important fields
- Generate summaries
- Translate content
- Explain technical terms
- Identify missing information

---

## Contracts

AI can

- Generate draft contracts from templates
- Rewrite clauses
- Simplify legal language
- Summarize contracts

AI never produces the final legal document.

---

## Government Forms

AI can

- Explain purpose
- Explain fields
- Suggest required documents
- Highlight common mistakes
- Generate completion guidance

AI never submits forms.

---

## Customer Communication

AI can

Generate

- Project updates
- Progress summaries
- Delay explanations
- Completion notifications

---

## Reports

AI can

Generate executive summaries for reports.

---

# AI Interaction Pattern

Every AI interaction follows the same workflow.

```
User Action

↓

Prompt Generated

↓

Provider Selected

↓

AI Response

↓

User Review

↓

Accept / Ignore / Edit
```

Users always decide what to keep.

---

# Prompt Generation

Prompts should be generated automatically whenever possible.

Users should not need to write complex prompts.

Example

Instead of

```
Explain this contract.
```

The system sends

```
Summarize the attached engineering consultancy contract.

Highlight

- obligations
- payment terms
- liabilities
- risks
- missing clauses
```

---

# AI Response Structure

Every response contains

## Summary

Short explanation.

---

## Details

Complete explanation.

---

## Confidence

High

Medium

Low

---

## Suggested Actions

Examples

- Review manually
- Upload supporting document
- Contact customer

---

# Prompt Templates

Prompt templates are administrator configurable.

Examples

- Contract Summary
- Project Summary
- Government Form Explanation
- Technical Translation
- Customer Update

Templates can be edited without modifying code.

---

# AI Caching

AI responses should be cached.

Cache key includes

- Provider
- Model
- Prompt
- Context

Repeated requests should reuse cached responses whenever possible.

Cache expiry is configurable.

---

# AI History

Each AI interaction should be stored for reference.

History includes

- Date
- Provider
- Model
- Prompt
- Response
- User

History is read-only.

---

# Provider Selection

Administrators can choose

- Claude
- DeepSeek

Selection may be

- Global
- Per Module
- Per Prompt Template

Future providers should plug into the same interface.

---

# Failure Handling

If AI is unavailable

Display

```
AI service is currently unavailable.

Please try again later.
```

Offer

- Retry
- Cancel

The application continues functioning normally.

---

# Security

Never send

- Passwords
- API Keys
- Internal configuration
- User credentials

Only business content required for the request should be transmitted.

---

# Performance

AI requests should be asynchronous.

While waiting

Display

- Skeleton response
- Progress indicator

Users should continue using the application.

---

# UX Standards

AI should feel

- Helpful
- Professional
- Fast
- Predictable

Never

- Interrupt workflow
- Force users to use AI
- Automatically overwrite user input

---

# Administrative Controls

Administrators can

- Enable / Disable AI
- Configure providers
- Configure models
- Configure prompt templates
- Configure cache duration
- Test provider connection
- Set default provider
- Configure retry limits

No code changes should be required.

---

# Extensibility

AI providers should implement a common interface.

```
Generate Response

↓

Return Standard Response

↓

Display in UI
```

The frontend should not depend on provider-specific response formats.

---

# Future Integration

Current Prototype

```
Mock AI Response
```

Production

```
Vue

↓

Python API

↓

AI Provider

↓

Claude / DeepSeek

↓

Cached Response

↓

Vue
```

Replacing mock AI with live AI should require only backend changes.

---

# AI Boundaries

AI is a productivity tool.

It does not

- Approve projects
- Approve contracts
- Approve submissions
- Make engineering decisions
- Replace professional judgement

Final responsibility always remains with the user.

---

# Success Criteria

AI should feel like a knowledgeable assistant that saves time without taking control. Users should be able to complete every workflow with or without AI enabled. Switching between Claude and DeepSeek, or disabling AI entirely, must require only configuration changes and never affect the rest of the application.