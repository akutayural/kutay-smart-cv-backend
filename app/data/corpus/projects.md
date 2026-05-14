---
document_type: projects

domain:
  - backend_engineering
  - fintech
  - ai_engineering
  - embedded_systems
  - crm_systems
  - hrtech

topics:
  - payment_systems
  - fraud_detection
  - e_wallets
  - crypto
  - rag
  - realtime_systems
  - semantic_retrieval
  - forecasting
  - websocket
  - payment_gateways
  - merchant_systems
  - kyc
  - embedded_systems
  - vanet
  - notification_systems
  - vector_search
  - conversational_ai
  - agentic_workflows
  - streaming_ai
  - transaction_processing
  - realtime_apis

primary_stack:
  - python
  - fastapi
  - java
  - spring_boot
  - redis
  - postgresql
  - mysql
  - kubernetes
  - docker

industries:
  - fintech
  - ai
  - crm
  - hrtech
  - intelligent_transportation

project_types:
  - saas_platforms
  - internal_platforms
  - open_source
  - ai_systems
  - realtime_systems

project_slugs:
  - evopayd-mongapay
  - hofi-e-wallet-platform
  - payment-gateway-merchant-routing-system
  - -fraud-detection-system
  - voucher-crypto-platform
  - smart-cv-ai-assistant
  - v2x-communication-predictive-analysis
  - evam-crm-customer-engagement-platform
  - part-time-jet-platform
  - apiexception


production_experience: true
opensource_projects: true

location:
  - united_kingdom
  - turkey

last_updated: 2026-04-15
---

# Projects

## EvoPayd / MongaPay

### Project Slug
evopayd-mongapay

### Type
FinTech SaaS Platform

### Status
Live Production System

### URL
https://evopayd.com/

### Description
Built and maintained backend infrastructure for crypto ↔ fiat transaction infrastructure used by merchants and financial partners.

The platform supported multiple configurable transaction workflows for buy/sell operations, merchant settlements, and customer fund transfers across different financial flows.

### Features
- Buy crypto workflows
- Sell crypto workflows
- Merchant transaction management
- Admin panel backend
- Merchant panel backend
- Multi-flow financial processing system

### Transaction Architecture
Implemented multiple configurable financial transaction flows depending on merchant settlement and operational requirements.

Supported different buy/sell, payout, and settlement scenarios across merchant configurations.

### Responsibilities
- Designed backend APIs
- Implemented transaction workflows
- Built merchant management infrastructure
- Developed admin panel backend services
- Developed merchant panel backend services
- Developed checkout and customer transaction APIs

### Integrations
- Integrated KYC workflows using Sumsub
- Worked with payment provider integrations supporting Credit/debit card, Apple Pay, and Google Pay payment flows
- Implemented IPN/webhook-based payment status handling and transaction updates

### Technologies
Python, FastAPI, MySQL, Redis, Docker, Kubernetes, ArgoCD, New Relic

---

## Hofi E-Wallet Platform

### Project Slug
hofi-e-wallet-platform

### Type
E-Wallet / FinTech Platform

### Status
Internal Product / Not Live

### Description
Built backend infrastructure for a digital e-wallet platform supporting mobile payment operations, wallet management, and card-based financial workflows.

The platform included customer wallet systems, payment operations, card management flows, and internal merchant/admin management infrastructure.

### Features
- Digital wallet infrastructure
- Card issuance and management support
- Money top-up operations
- Card payment workflows
- Wallet transaction processing
- Admin panel backend
- Merchant panel backend

### Responsibilities
- Developed mobile application backend APIs
- Implemented wallet transaction workflows
- Built admin panel backend services
- Built merchant management services
- Developed payment and card operation logic

### Integrations
- Integrated KYC workflows using Sumsub
- Worked with payment provider integrations supporting card payments, Apple Pay, and Google Pay flows
- Implemented IPN/webhook-based payment status handling and transaction updates

### Technologies
Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, ArgoCD, New Relic

---

## Payment Gateway & Merchant Routing System

### Project Slug
payment-gateway-merchant-routing-system

### Type
Payment Infrastructure Platform

### Status
Live Production System

### Description
Built backend infrastructure for a payment gateway and merchant routing platform handling deposit and withdrawal operations across different merchants and payment providers.

The system included realtime payment status tracking, merchant-based routing logic, operational monitoring, and financial distribution workflows.

### Features
- Deposit and withdrawal processing
- Merchant-based transaction routing
- Payment provider integrations
- Merchant admin panel
- Realtime payment status tracking
- WebSocket-based event communication
- Operational alerting and monitoring systems

### Responsibilities
- Developed backend APIs and payment workflows
- Implemented merchant routing and distribution logic
- Built realtime transaction communication systems using WebSockets
- Integrated operational Telegram notification systems
- Developed financial forecasting infrastructure for operational planning
- Integrated Telegram Bot API for operational alerts and realtime notifications

### Forecasting & Analytics
Implemented daily financial deposit forecasting systems using Facebook Prophet to estimate transaction volume and operational liquidity requirements based on historical payment behaviour.

### Technologies
Python, FastAPI, PostgreSQL, Redis, WebSockets, Telegram APIs, Facebook Prophet, Docker, Kubernetes

---

## Fraud Detection System

### Project Slug
fraud-detection-system

### Type
Internal Fraud Detection Platform

### Status
Live Production System

### Description
Internal real-time fraud detection and transaction risk management platform rebuilt from legacy Kotlin infrastructure into a modern Python FastAPI architecture.

The system was used across financial products to evaluate transactions, apply dynamic fraud rules, and automatically block suspicious activities in realtime.

### Features
- Rule-based fraud engine
- Realtime transaction risk analysis
- Automatic transaction blocking
- IP-based restrictions
- Customer-based restrictions
- Dynamic project-level fraud rules
- Centralised fraud management system
- PM-controlled banning and rule configuration

### Responsibilities
- Re-architected legacy Kotlin infrastructure
- Migrated backend systems to FastAPI
- Developed dynamic fraud rule engine
- Implemented realtime transaction blocking logic
- Built reusable fraud management infrastructure across projects

### Technologies
Python, FastAPI, Redis, Docker, Kubernetes, ArgoCD, New Relic

---

## Voucher & Crypto Platform

### Project Slug
voucher-crypto-platform

### Type
Internal Financial Platform

### Status
Live Production System

### Description
Internal Flask-based platform used for voucher and cryptocurrency-related operations.

Although not originally developed by him, actively maintained and supported the platform as part of the backend engineering team.

### Responsibilities
- Platform maintenance
- Backend support
- Operational improvements
- Bug fixing and monitoring

### Technologies
Python, Flask

---

## Smart CV AI Assistant

### Project Slug
smart-cv-ai-assistant

### Type
AI Engineering / RAG System

### Status
Live Production System

### Description
Production-style AI assistant and recruiter-facing digital twin designed to answer conversational questions about technical background, project experience, role fit, and work eligibility using retrieval-augmented generation (RAG).
Built using FastAPI, LangGraph, OpenAI APIs, semantic retrieval pipelines, vector search infrastructure, streaming AI architectures, and conversational memory systems.

### Features
- Streaming AI responses with Server-Sent Events (SSE)
- RAG pipeline using semantic retrieval
- Conversation state management with Redis
- Request tracing and structured logging
- Guardrails and scope validation
- Rate limiting and API protection
- LangGraph orchestration workflows
- Vector search with Qdrant
- Conversational memory handling
- AI-powered recruiter interaction flows
- Semantic retrieval and reranking
- Streaming LLM responses

### Technologies
Python, FastAPI, LangGraph, OpenAI, Qdrant, Redis


## V2X Communication & Predictive Analysis

### Project Slug
v2x-communication-predictive-analysis

### Type
MSc Research & Real-World Implementation Project

### Collaboration
Middlesex University × Tata Consultancy Services (TCS)

### Description
Worked on real-time Vehicle-to-Vehicle (V2X) communication systems as part of a smart transportation research initiative focused on future smart city infrastructure.

The project involved actual realtime communication between vehicles using VANET infrastructure and embedded networking systems, not only simulation-based research.

### Features
- Real-time inter-vehicle communication
- VANET (Vehicle Ad Hoc Network) scenarios
- Embedded software development
- Predictive analysis using realtime vehicle data
- Physical roadside testbed deployment
- CAN Bus and OBD-II integration
- Socket-based realtime communication

### Responsibilities
- Developed embedded C software on Cohda Wireless OBU devices
- Implemented realtime data transfer between vehicles
- Worked on low-level communication and networking scenarios
- Contributed to predictive analysis models using realtime telemetry data
- Participated in live roadside deployment and field testing

### Technologies
Embedded C, Python, Socket Programming, VANET, CAN Bus, OBD-II, Cohda Wireless OBU

---

## EVAM CRM & Customer Engagement Platform

### Project Slug
evam-crm-customer-engagement-platform

### Company
Evam

### Status
Live Production System

### URL
https://evam.com/

### Type
Enterprise CRM & Customer Engagement Platform

### Description
Worked on enterprise-scale CRM and customer engagement systems used for SMS, push notification, and in-app communication workflows across different enterprise customers.

The platform supported both desktop and web-based operational environments depending on customer infrastructure and deployment preferences.

Developed backend services and customer-specific functionality within high-volume event processing systems.

### Responsibilities
- Developed customer-specific backend features
- Implemented custom enterprise workflows
- Built backend services for notification and communication systems
- Worked on high-volume event processing infrastructure
- Improved backend system performance

### Technologies
Java, Spring Boot, PostgreSQL, Kafka, Redis, Elasticsearch, Docker

---

## Part-Time Jet Platform

### Project Slug
part-time-jet-platform

### Company
Han Group

### Type
HRTech / Job & Payment Platform

### Status
Production Platform

### URL
https://parttimejet.com/

### Description
Built backend infrastructure for a LinkedIn-style part-time job and recruitment platform focused on automating HR and hiring workflows.

The platform included job applications, recruitment process management, payment operations, and digital card/wallet-related financial flows for users.

### Features
- Job listing and application workflows
- Automated HR process management
- Payment infrastructure
- Digital card and wallet operations
- User and employer management systems

### Responsibilities
- Developed backend APIs
- Implemented HR workflow automation
- Built payment-related backend services
- Developed user and employer management infrastructure

### Technologies
Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes

---

## APIException

### Project Slug
apiexception

### Description
Open-source FastAPI exception handling library.

GitHub: https://github.com/akutayural/APIException
Documentation: https://akutayural.github.io/APIException/

### Type
Open Source Developer Tooling Library

### Status
Public Open Source Project

### Links
https://github.com/akutayural/APIException
https://akutayural.github.io/APIException/

### Description
Open-source FastAPI exception handling and standardized API response library designed to simplify error management and reduce backend boilerplate in Python API projects.

The library provides structured exception handling patterns, reusable response models, and cleaner API error architecture for FastAPI applications.

### Features
- Standardised API error responses
- Reusable exception handling architecture
- Reduced backend boilerplate
- FastAPI integration support
- Structured error modelling

### Recognition
- Featured by Python Weekly
- Featured by PythonHub
- Selected by Tryolabs among notable Python/AI-related libraries
- Shared by large developer and engineering communities
- Among the most recognised FastAPI exception handling libraries in its category
- Indexed by Context7 for AI-assisted developer tooling

### Adoption
- 250+ GitHub stars
- 60K+ package downloads

### Technologies
Python, FastAPI, Pydantic
