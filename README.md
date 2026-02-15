# MiniRAG

A fully local Retrieval-Augmented Generation (RAG) application for ingesting documents, generating embeddings, storing vectors, and querying them through a CLI, API, and optional frontend.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Modes](#modes)
- [Assumptions & Limitations](#assumptions-and-limitations)
- [Requests & Responses](#requests-and-responses)
- [Frontend](#frontend)
- [Testing](#testing)
- [Stack](#stack)
- [Project Walkthrough](#project-walkthrough)
---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/ntagky/mini-rag.git
cd mini-rag
```

---

### 2. Create `.env` File

Create the environment file **before starting Docker**.

**macOS / Linux**
```bash
touch .env
```

**Windows (PowerShell)**
```powershell
New-Item .env
```

Add the required variables:

```env
OPENAI_API_KEY=your_key
ELASTICSEARCH_URL=http://localhost:9200
OLLAMA_URL=http://localhost:11434
```

---

### 3. Run Docker Compose (Recommended)

Build and start all services:

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up -d --build
```

Stop services:

```bash
docker compose down
```

Remove volumes as well:

```bash
docker compose down -v
```

---

#### Services Started

Docker Compose will automatically start:

- FastAPI backend
- Next.js frontend (built during image creation)
- Elasticsearch
- Ollama (with model pull on startup)

---

### 4. Access the Application

**API:**
```
http://localhost:8000
```

**Elasticsearch:**
```
http://localhost:9200
```

---

### Optional: Run Locally Without Docker

Using **conda**:

```bash
conda create -n mini-rag python=3.12
conda activate mini-rag
pip install -r requirements.txt
python main.py cli
```

Using **venv**:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py cli
```

### Optional: Run Frontend Locally

Make sure you have **Bun** installed:

https://bun.sh

Then:

```bash
cd frontend
bun install
bun run dev
```

Frontend will be available at:

```
http://localhost:3000
```

## Modes

The application supports two execution modes:

- **cli** — local terminal interaction
- **api** — HTTP endpoints for programmatic access

---

### CLI Mode

Runs as an interactive loop in the terminal with four available commands for managing ingestion and querying.

![CLI Mode](.assets/screenshots/screenshot-cli-mode.png)

#### 1. ```doctor```
Performs a quick environment health check to ensure the system is ready to run.

Validates:

- `.env` file and required variables
- **OpenAI** connectivity
- **Elasticsearch** reachability
- **Ollama** availability

Returns a clear pass/fail status with diagnostics for any failing service.

#### 2. ```ingest [--reset]```
The system performs a full-scale ingestion of the local corpus by using Docling OCR and vision-capable GPT models to extract data, which is then deduplicated via an SQLite registry and chunked for processing. Finally, it creates a robust search layer by storing vector embeddings in Elasticsearch alongside a TF-IDF index for hybrid fallback retrieval.

#### 3. ```query <your question> [--top-k N] [--model openai|ollama]```
Retrieves the top N documents from Elasticsearch and uses the agent with the corresponding model to answer based strictly on the corpus.

#### 4. ```chat [--model openai|ollama]```
Starts a REPL session with short-term memory. The agent maintains context across multiple turns using the SQLite session store.

#### 5. ```exit```
Gracefully terminates the Python session.

![CLI Mode - 1](.assets/screenshots/screenshot-cli-1.png)
![CLI Mode - 2](.assets/screenshots/screenshot-cli-2.png)

### API Mode
The system exposes a RESTful interface for remote integration, allowing external clients to manage models and engage in stateful conversations.
![API Mode](.assets/screenshots/screenshot-api-mode.png)

#### 1. ```/health```
Verify that the API and its external dependencies are running.
#### 2. ```/api/v1/models```
Lists all available local (Ollama) and remote (OpenAI) models currently configured.
#### 3. ```/api/v1/chat```
Handles conversation logic by passing the message history directly in the request body for stateless execution.

## Assumptions and Limitations

First Run & VPN: The BAAI/bge-base-en-v1.5 model must be downloaded from HuggingFace on the first run; if the download fails due to VPN restrictions, disable the VPN briefly to allow the model to cache locally.

Performance & Metrics: Tests were conducted using OpenAI because Ollama ran slowly on the local machine.

## Requests and Responses

### CLI Mode
#### A.
```bash
$ python main.py cli
```
> **query** hello, how are you?

> *Hello! I am here to help you with any questions you have.*

```json
{
  "trace_id": "a2165674-2ac7-4d38-b910-dbb2481cbdec",
  "model": "openai",
  "question": "hello, how are you?",
  "response": "Hello! I'm here to help you with any questions you have.",
  "citations": [],
  "steps": [
    "plan",
    "answer"
  ],
  "plan": {
    "steps": [
      {
        "name": "answer",
        "response": "Hello! I'm here to help you with any questions you have."
      }
    ],
    "keywords": [
      "greeting"
    ]
  },
  "retrieval": [],
  "latency_ms": {
    "plan": 1566,
    "answer": 0,
    "total": 1566
  },
  "tokens": {
    "plan": {
      "prompt_tokens": 499,
      "response_tokens": 46,
      "total_tokens": 545
    }
  },
  "errors": []
}
```

#### B.
```bash
$ python main.py cli
```
> **query** What if an employer seeks to enroll employees in a clinical investigation sponsored or conducted by the employer? **--model openai**

> *If an employer seeks to enroll employees in a clinical investigation sponsored or conducted by the employer, the clinical investigator and IRB must carefully consider potential conflicts of interest and the voluntary nature of consent. According to FDA regulations and guidance, when financial relationships or interests exist—such as an employer sponsoring a study in which employees are subjects—special considerations should be made to mitigate potential undue influence or coercion. These considerations may include:\n\n- Disclosing the source of funding, financial arrangements, or interests related to the employer as sponsor in the informed consent process.\n- Using special measures to modify the informed consent process to ensure voluntariness, such as involving an independent individual without conflicts of interest to obtain consent.\n- Employing independent monitoring of the consent process to protect the rights and welfare of employee-subjects.\n\nThe IRB holds ultimate responsibility for determining if and how such information should be disclosed and whether additional protections are necessary (see 21 CFR 56.109, 56.111(a)(4)-(5)).\n\nIn summary, employer-sponsored clinical investigations involving employees require enhanced scrutiny regarding financial interests, disclosure, and consent to safeguard against conflicts and ensure voluntary participation.\n\ncite=[ICD - Document 1.pdf+42]*

```json
{
  "trace_id": "d3096fa6-9205-476f-b992-b8a31393f959",
  "model": "openai",
  "question": "What if an employer seeks to enroll employees in a clinical investigation sponsored or conducted by the employer?",
  "response": "If an employer seeks to enroll employees in a clinical investigation sponsored or conducted by the employer, the informed consent process should include safeguards to ensure that participation is voluntary and that the possibility of undue influence or coercion by supervisors, peers, or others is minimized. The consent process and form should emphasize that participation is truly voluntary. This is to avoid undue influence arising from the employer-employee relationship and to ensure that employees understand that their choice to participate or not will not result in any adverse consequences (21 CFR 50.25(a)(8)) [cite=ICD - Document 1.pdf+12].",
  "citations": [
    "cite=ICD - Document 1.pdf+12"
  ],
  "steps": [
    "plan",
    "retrieve",
    "draft"
  ],
  "plan": {
    "steps": [
      {
        "name": "retrieve",
        "strategy": "vector_only",
        "top_k": 5,
        "fallback_threshold": 0.25
      },
      {
        "name": "draft",
        "style": "detailed"
      }
    ],
    "keywords": [
      "employer",
      "clinical investigation",
      "enrollment"
    ]
  },
  "retrieval": [
    "document-id: ICD - Document 1.pdf, page: 50, chunk-id: 6dd92083-a621-4993-8c99-30319009a501, source:Elastic, score:0.83219194",
    "document-id: ICD - Document 1.pdf, page: 42, chunk-id: f8e3208c-58ac-4f23-9e1b-a3788cf01583, source:Elastic, score:0.82505643",
    "document-id: ICD - Document 1.pdf, page: 28, chunk-id: c04a92a3-a081-4df6-b406-0eec77132b6a, source:Elastic, score:0.82215124",
    "document-id: ICD - Document 1.pdf, page: 12, chunk-id: 1069e377-d379-462a-b733-5cb1e8f984d0, source:Elastic, score:0.821601",
    "document-id: ICD - Document 1.pdf, page: 59, chunk-id: 82bd5344-3e6e-4e0e-8e46-80bd55ece183, source:Elastic, score:0.81845814"
  ],
  "latency_ms": {
    "plan": 1467,
    "retrieve": 903,
    "draft": 2141,
    "total": 4511
  },
  "tokens": {
    "plan": {
      "prompt_tokens": 512,
      "response_tokens": 81,
      "total_tokens": 593
    },
    "draft": {
      "prompt_tokens": 1754,
      "response_tokens": 121,
      "total_tokens": 1875
    }
  },
  "errors": []
}
```

#### C.
```bash
$ python main.py cli
```
> **query** What information must consent forms provide regarding medical alternatives and the standard of care for prospective subjects? **--model openai**

> *Consent forms must disclose appropriate alternative procedures or courses of treatment that might be advantageous to the subject, including a description of the care the subject would likely receive if they do not participate in the research (21 CFR 50.25(a)(4)). This includes approved therapies for the patient's condition, other forms of therapy (e.g., surgical), diagnosis, and when appropriate, supportive care without disease-directed therapy.\n\nThe disclosure must include a description of the current medically recognized standard of care, especially in studies involving medical products intended to treat or diagnose serious diseases or conditions. The standard of care may include uses or treatment regimens of legally marketed drugs or devices that are not included in the product's approved uses. Information about unapproved uses that are part of the medically recognized standard of care can be provided factually but should not be promotional.\n\nIf there are multiple alternatives, the consent form may state that these will be discussed in more detail by the clinical investigator. Treatment options lacking evidence of therapeutic value should generally not be included. Disclosure should include reasonably foreseeable risks or discomforts and potential benefits associated with these alternatives during the informed consent process, although detailed risk/benefit explanation need not always be in the written consent form.\n\nIt may be appropriate to refer subjects to their primary care provider or another healthcare professional for more complete discussion of alternatives before signing the consent form.\n\nThe person obtaining consent must be able to discuss available alternatives and answer questions from prospective subjects, and consent documents and discussions may need updating if new alternative treatments become available during the trial cite=[ICD - Document 1.pdf+19,20].*

```json
{
  "trace_id": "01e0d3fe-910c-486c-884f-8763d704ef67",
  "model": "openai",
  "question": "What information must consent forms provide regarding medical alternatives and the standard of care for prospective subjects?",
  "response": "Consent forms must disclose appropriate alternative procedures or courses of treatment that might be advantageous to the subject, including a description of the care they would likely receive if they do not participate in the research. This includes approved therapies for the patient’s disease or condition, other forms of therapy or diagnosis, and supportive care without disease-directed therapy. The consent must describe the current medically recognized standard of care, particularly in studies of medical products for serious diseases or conditions. When describing unapproved uses of approved drugs or devices that are part of the standard of care, factual information may be provided but should not be promotional. Additionally, alternatives should include reasonably foreseeable risks, discomforts, and potential benefits, and discussion of alternatives should be available during the informed consent process, although not all details need to be in the written form. Subjects may be referred to healthcare professionals for more detailed discussions of alternatives before consent is given. (21 CFR 50.25(a)(4)) cite=[ICD - Document 1.pdf+19,20].",
  "citations": [
    "ICD - Document 1.pdf+19,20"
  ],
  "steps": [
    "plan",
    "retrieve",
    "draft"
  ],
  "plan": {
    "steps": [
      {
        "name": "retrieve",
        "strategy": "vector+tfidf_fallback",
        "top_k": 5,
        "fallback_threshold": 0.25
      },
      {
        "name": "draft",
        "style": "concise"
      }
    ],
    "keywords": [
      "consent forms",
      "medical alternatives",
      "standard of care"
    ]
  },
  "retrieval": [
    "document-id: ICD - Document 1.pdf, page: 19, chunk-id: f4fcfc08-fc79-4fea-b16c-1fc972ffec99, source:Elastic, score:0.8825378",
    "document-id: ICD - Document 1.pdf, page: 20, chunk-id: e2864964-3ecb-4459-93f6-f48a1c46be2c, source:Elastic, score:0.86513805",
    "document-id: ICD - Document 1.pdf, page: 17, chunk-id: 6fb24897-462a-47c3-82e8-b93ac61ed0aa, source:Elastic, score:0.84505796",
    "document-id: ICD - Document 1.pdf, page: 17, chunk-id: cbdc6317-bd80-4ddc-8df9-7072ae237183, source:Elastic, score:0.84445167",
    "document-id: ICD - Document 1.pdf, page: 22, chunk-id: f763a0bc-f6e4-4ddc-a5f5-1ef316b5a2a1, source:Elastic, score:0.8437898"
  ],
  "latency_ms": {
    "plan": 1520,
    "retrieve": 347,
    "draft": 3183,
    "total": 5051
  },
  "tokens": {
    "plan": {
      "prompt_tokens": 511,
      "response_tokens": 93,
      "total_tokens": 604
    },
    "draft": {
      "prompt_tokens": 2180,
      "response_tokens": 203,
      "total_tokens": 2383
    }
  },
  "errors": []
}
```

### API Mode
#### A.
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
    {
      "role": "user",
      "content": "Who must be listed as contacts in the consent document, and why does the FDA recommend a separate contact for questions regarding subjects'\'' rights?"
    }
  ],
  "model": "openai"
}'
```
```json
{
  "content": "The consent document must list contacts for:  \n1. Answers to pertinent questions about the research.  \n2. Questions about subjects' rights.  \n3. Contact in the event of a research-related injury.  \n\nThis information should include names (or offices), email addresses, and telephone numbers.\n\nThe FDA recommends a separate contact for questions regarding subjects' rights who is not part of the investigational team because subjects may hesitate to report concerns or problems to someone involved in the investigation. Such contacts can include the IRB Office, Patient Advocate Office, or other trained staff regarding subjects' rights.  \n\nAdditionally, the consent process should provide emergency contact information, including 24-hour contact if appropriate. If contact information changes during the study, updated contacts must be provided to subjects (21 CFR 50.25(a)(7)) [cite=ICD - Document 1.pdf+23].",
  "citations": [
    "cite=ICD - Document 1.pdf+23"
  ]
}
```

#### B.
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
      {
      "role": "user",
      "content": "Hello, I need your help."
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help you?"
    },
    {
      "role": "user",
      "content": "In what specific clinical scenarios is a randomized withdrawal study design most effective for determining long-term efficacy and treatment duration?"
    }
  ],
  "model": "openai"
}'
```
```json
{
  "content": "Randomized withdrawal study designs are most effective in the following clinical scenarios for determining long-term efficacy and treatment duration:\n\n1. **Relapse-Prevention in Recurring Illnesses:** For drugs that resolve episodes of recurring illnesses such as antidepressants, randomized withdrawal acts as a relapse-prevention study by comparing continued treatment to withdrawal to placebo.\n\n2. **Symptom or Sign Suppression:** For conditions where symptoms or signs (e.g., chronic pain, hypertension, angina) are suppressed by the drug, and where a long-term placebo-controlled trial is difficult or unethical, the design can establish long-term efficacy.\n\n3. **Determining Treatment Duration:** Particularly useful for therapies requiring guidance on length of treatment, such as post-infarction beta-blocker therapy, by randomizing responders to continued treatment or placebo to evaluate persistence of benefit.\n\nAdditionally, such trials can address dosing issues by randomizing responders to multiple doses or placebo after an initial fixed-dose phase to study dose-response and maintenance dose efficacy.\n\nThe design is especially beneficial when long-term placebo exposure is not ethical since the withdrawal phase can be short and incorporate early escape for patients who relapse or worsen.\n\nKey considerations include avoiding withdrawal phenomena through slow tapering and acknowledging that efficacy estimates may be higher due to enrichment with responders who tolerate the drug well.\n\ncite=[E10 - Document 3.pdf+22,23]",
  "citations": [
    "E10 - Document 3.pdf+22,23"
  ]
}
```

#### C.
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
      {
      "role": "user",
      "content": "Hello, I need your help."
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help you?"
    },
    {
      "role": "user",
      "content": "In what specific clinical scenarios is a randomized withdrawal study design most effective for determining long-term efficacy and treatment duration?"
    },
    {
      "role": "assistant",
      "content": "Randomized withdrawal study designs are most effective in the following clinical scenarios for determining long-term efficacy and treatment duration:\n\n1. **Relapse-Prevention in Recurring Illnesses:** For drugs that resolve episodes of recurring illnesses such as antidepressants, randomized withdrawal acts as a relapse-prevention study by comparing continued treatment to withdrawal to placebo.\n\n2. **Symptom or Sign Suppression:** For conditions where symptoms or signs (e.g., chronic pain, hypertension, angina) are suppressed by the drug, and where a long-term placebo-controlled trial is difficult or unethical, the design can establish long-term efficacy.\n\n3. **Determining Treatment Duration:** Particularly useful for therapies requiring guidance on length of treatment, such as post-infarction beta-blocker therapy, by randomizing responders to continued treatment or placebo to evaluate persistence of benefit.\n\nAdditionally, such trials can address dosing issues by randomizing responders to multiple doses or placebo after an initial fixed-dose phase to study dose-response and maintenance dose efficacy.\n\nThe design is especially beneficial when long-term placebo exposure is not ethical since the withdrawal phase can be short and incorporate early escape for patients who relapse or worsen.\n\nKey considerations include avoiding withdrawal phenomena through slow tapering and acknowledging that efficacy estimates may be higher due to enrichment with responders who tolerate the drug well.\n\ncite=[E10 - Document 3.pdf+22,23]"
    },
    {
      "role": "user",
      "content": "Okay, and how can sponsors distinguish between the data listings for '\''Deaths'\'' and '\''Other Serious Adverse Events'\'' to avoid the risk of double counting fatal outcomes?"
    }
  ],
  "model": "openai"
}'
```
```json
{
  "content": "Sponsors should include all deaths in the data listing under section 12.3.1.1 (Deaths), which captures all deaths during the study and post-treatment follow-up, including deaths resulting from processes that began during the study. The listing for section 12.3.1.2 (Other Serious Adverse Events) includes serious adverse events other than death but may include events temporally associated with or preceding deaths. While deaths may appear in both listings, this does not result in double counting or miscounting because any fatal event listed as an \"other serious adverse event\" would also be captured under the \"Deaths\" listing. Thus, deaths are explicitly recorded once in the Deaths section, and any associated serious adverse events with fatal outcomes can also appear in the Other Serious Adverse Events section without duplication of the death count. \n\ncite=[E3 Structure - Document 2.pdf+8]",
  "citations": [
    "E3 Structure - Document 2.pdf+8"
  ]
}
```

## Frontend

The frontend is a modern Next.js application that serves as the primary user interface for the RAG system. It features a responsive chat interface where users can interact with the agent in real-time. A key feature is the model switcher, allowing users to toggle between OpenAI (GPT-4o-mini) for high-level reasoning and Ollama (Llava:7b) for local or vision-based tasks.

### Non-docker Setup

#### 1. Enter Frontend
```bash
cd frontend
```

#### 2. Install Deps
```bash
bun install
```

#### 3. Spin Up:
```bash
bun --bun run dev
```

![Frontend Homepage](.assets/screenshots/screenshot-frontend-homepage.png)
![Frontend Chat](.assets/screenshots/screenshot-frontend-chat.png)
![Frontend CLI](.assets/screenshots/screenshot-frontend-cli.png)

## Testing
I have implemented an end-to-end testing suite that validates the entire pipeline. The codebase currently maintains a test coverage of >70%.

```bash
pytest --cov=app/ tests/
```

![Test](.assets/screenshots/screenshot-tests.png)

To maintain code integrity, I use pre-commit hooks that automatically run ruff for linting and formatting, mypy for static type checking, and standard safety checks for file structure and size.

```bash
pre-commit run --all-files
```

![Maintain](.assets/screenshots/screenshot-precommit.png)


## Stack

| Category               | Technology | Role                                                 |
|:-----------------------| :--- |:-----------------------------------------------------|
| **Orchestration**      | Docker Compose | Containerization & environment parity                |
| **Search Engine**      | Elasticsearch 9.2.4 | Vector Database & similarity retrieval               |
| **Database (Local)**   | SQLite | Lightweight relational storage for corpus management |
| **Inference (Local)**  | Ollama (Llava:7b) | Multi-modal (Vision + Text) reasoning                    |
| **Inference (Cloud)**  | OpenAI GPT-4o-mini | Multi-modal (Vision + Text) reasoning                   |
| **Data Ingestion**     | Docling (IBM) | Advanced document parsing (PDF/DOCX to Markdown/JSON) |
| **Embeddings (Local)** | BAAI/BGE-Base-En-v1.5 | High-performance local text vectorization via Sentence Transformers |
| **Embeddings (Cloud)**        | text-embedding-3-small | Generating high-dimensional vector representations   |
| **Backend**            | Python 3.11 | Agent logic, LangChain/LlamaIndex orchestration      |
| **Frontend**           | Next.js | Modern web interface for the agent chat              |
| **Legacy Search**      | TF-IDF | Basic keyword frequency analysis for comparison      |
| **Monitoring**         | Kibana 9.2.4 | Data visualization and index management              |


---

## Project Walkthrough
For a live demonstration of the system in action, check out the 3-minute video below:

**[Demo on YouTube](https://youtu.be/k2qB9IycLc8)**
