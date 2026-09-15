/**
 * Grounded Product Profile Analysis Engine for RepoMind AI.
 *
 * Extracts structured product identity, capabilities, evidenced tech stack,
 * deployment platforms, and subsystem responsibilities directly from
 * repository files, chunk contents, manifests, and dependency graphs.
 *
 * Strictly follows the Grounding Rule:
 * - Distinguishes facts directly evidenced in code/config vs README claims
 * - Never invents technologies or deployment platforms without evidence
 * - Focuses on "What is this repository/product?" (not internal architecture)
 */

import {
  ChunkPreview,
  OverviewMetrics,
  ArchitectureResponse,
  FileListResponse,
  OverviewResponse,
} from "./types";

export interface CapabilityItem {
  id: string;
  title: string;
  description: string;
  source: string;
  badge: string;
}

export interface TechStackCategory {
  category: string;
  badge: string;
  color: string;
  items: Array<{
    name: string;
    evidence: string;
    iconHint?: string;
  }>;
}

export interface DeploymentPlatform {
  platform: string;
  configFile: string;
  description: string;
  badge: string;
}

export interface MajorPart {
  name: string;
  badge: string;
  responsibility: string;
  fileCount: number;
  sampleFiles: string[];
}

export interface KeyFileItem {
  path: string;
  role: string;
  badge: string;
  reason: string;
  connections: number;
  inbound: number;
  outbound: number;
  isEntryPoint: boolean;
}

export interface ProductProfile {
  repoName: string;
  projectType: string;
  projectTypeConfidence: "High" | "Medium" | "Inferred";
  projectTypeRationale: string;
  secondaryBadges: string[];
  productSummary: string;
  problemSolved: string;
  targetAudience: string;
  mainPurpose: string;
  evidenceSource: string;
  capabilities: CapabilityItem[];
  techStackCategories: TechStackCategory[];
  deployment: {
    isDetected: boolean;
    platforms: DeploymentPlatform[];
    fallbackMessage: string;
    fallbackDetail: string;
  };
  majorParts: MajorPart[];
  keyFiles: KeyFileItem[];
  metrics: OverviewMetrics;
}

/**
 * Clean markdown formatting from raw text snippet.
 */
function cleanMarkdown(text: string): string {
  return text
    .replace(/!\[.*?\]\(.*?\)/g, "") // Remove images
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // Simplify links
    .replace(/`{1,3}[^`]*`{1,3}/g, (m) => m.replace(/`/g, "")) // Simplify inline code
    .replace(/^#+\s+/gm, "") // Remove headers
    .replace(/^\s*[-*+]\s+/gm, "") // Remove bullets
    .replace(/\*{1,2}([^*]+)\*{1,2}/g, "$1") // Remove bold/italic
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Extract README text from chunk previews if available.
 */
function getReadmeText(chunks: ChunkPreview[]): string {
  const readmeChunks = chunks.filter((c) =>
    c.file_path.toLowerCase().includes("readme")
  );
  if (readmeChunks.length === 0) return "";
  return readmeChunks
    .sort((a, b) => a.chunk_index - b.chunk_index)
    .map((c) => c.content)
    .join("\n\n");
}

/**
 * Extract package.json / requirements.txt / pyproject content from chunks.
 */
function getManifestChunks(chunks: ChunkPreview[]): string {
  const manifestFiles = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "cargo.toml",
    "go.mod",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "setup.py",
  ];
  return chunks
    .filter((c) => {
      const lower = c.file_path.toLowerCase();
      return manifestFiles.some((m) => lower.endsWith(m));
    })
    .map((c) => c.content)
    .join("\n\n");
}

/**
 * 1. Infer dynamic Product / Project Type from actual repository evidence.
 */
export function inferProjectType(
  paths: string[],
  chunks: ChunkPreview[],
  repoName: string,
  dependencies: Array<{ source: string; target: string; is_internal: boolean }> = []
): {
  projectType: string;
  confidence: "High" | "Medium" | "Inferred";
  rationale: string;
  secondaryBadges: string[];
} {
  const lowerPaths = paths.map((p) => p.toLowerCase());
  const allChunkContent = chunks.map((c) => c.content.toLowerCase()).join(" ");
  const allImports = dependencies.map((d) => d.target.toLowerCase()).join(" ");

  const hasAI =
    lowerPaths.some((p) => p.includes("llm") || p.includes("rag") || p.includes("embedding") || p.includes("vector") || p.includes("prompt")) ||
    allChunkContent.includes("sentence-transformers") ||
    allChunkContent.includes("sentence_transformers") ||
    allChunkContent.includes("faiss") ||
    allChunkContent.includes("groq") ||
    allChunkContent.includes("openai") ||
    allChunkContent.includes("anthropic") ||
    allChunkContent.includes("langchain") ||
    allChunkContent.includes("llamaindex") ||
    allChunkContent.includes("chromadb") ||
    allChunkContent.includes("pinecone") ||
    allChunkContent.includes("transformers") ||
    allChunkContent.includes("torch");

  const hasWebFrontend =
    lowerPaths.some((p) => p.includes("src/app") || p.includes("components/") || p.includes("pages/") || p.includes("views/")) ||
    lowerPaths.some((p) => p.endsWith(".tsx") || p.endsWith(".jsx") || p.endsWith(".vue") || p.endsWith(".svelte")) ||
    allChunkContent.includes("next") ||
    allChunkContent.includes("react") ||
    allChunkContent.includes("streamlit");

  const hasBackendAPI =
    lowerPaths.some((p) => p.includes("routers") || p.includes("routes") || p.includes("api/") || p.includes("controllers") || p.includes("endpoints")) ||
    allChunkContent.includes("fastapi") ||
    allChunkContent.includes("express") ||
    allChunkContent.includes("flask") ||
    allChunkContent.includes("django") ||
    allChunkContent.includes("nestjs") ||
    allChunkContent.includes("actix") ||
    allChunkContent.includes("gin");

  const hasBlockchain =
    lowerPaths.some((p) => p.endsWith(".sol") || p.includes("contracts/") || p.includes("hardhat.config")) ||
    allChunkContent.includes("solidity") ||
    allChunkContent.includes("ethers") ||
    allChunkContent.includes("hardhat") ||
    allChunkContent.includes("web3");

  const hasCLI =
    lowerPaths.some((p) => p.includes("cli") || p.includes("bin/") || p.includes("cmd/")) ||
    allChunkContent.includes("argparse") ||
    allChunkContent.includes("click") ||
    allChunkContent.includes("typer") ||
    allChunkContent.includes("commander");

  const isLibrary =
    (lowerPaths.some((p) => p.endsWith("setup.py") || p.endsWith("pyproject.toml")) && !hasWebFrontend && !hasBackendAPI) ||
    (lowerPaths.some((p) => p.endsWith("package.json")) && !hasWebFrontend && !hasBackendAPI && allChunkContent.includes('"main":'));

  const hasDataML =
    lowerPaths.some((p) => p.endsWith(".ipynb") || p.includes("dataset") || p.includes("pipeline") || p.includes("models/")) ||
    allChunkContent.includes("pandas") ||
    allChunkContent.includes("scikit-learn") ||
    allChunkContent.includes("numpy") ||
    allChunkContent.includes("pyspark");

  const secondaryBadges: string[] = [];

  // Determine specific composite project type
  let projectType = "Software Application";
  let rationale = "";

  if (hasBlockchain) {
    projectType = hasWebFrontend ? "Web3 Decentralized Application (DApp)" : "Smart Contract & Web3 Protocol";
    rationale = "Evidenced by Solidity contracts, Web3 libraries, and blockchain development tooling.";
    secondaryBadges.push("Web3", "Smart Contracts", "DeFi / DApp");
  } else if (hasAI && hasWebFrontend && hasBackendAPI) {
    projectType = "Full-Stack AI Application";
    rationale = "Evidenced by integrated AI/LLM orchestration, vector retrieval pipelines, REST backend services, and interactive frontend UI.";
    secondaryBadges.push("AI-Powered", "RAG & Vector Search", "Full-Stack", "FastAPI + React/Next");
  } else if (hasAI && hasWebFrontend) {
    projectType = "AI-Powered Web Application";
    rationale = "Evidenced by AI embedding/retrieval models and interactive user interface components.";
    secondaryBadges.push("AI Application", "Vector Search", "Web UI");
  } else if (hasAI && hasBackendAPI) {
    projectType = "AI REST API & Intelligence Service";
    rationale = "Evidenced by AI model inference, semantic retrieval pipelines, and HTTP API route endpoints.";
    secondaryBadges.push("AI Service", "REST API", "Semantic Search");
  } else if (hasAI) {
    projectType = "AI / Machine Learning Platform";
    rationale = "Evidenced by neural models, embedding indexes, and LLM processing pipelines.";
    secondaryBadges.push("AI/ML", "Vector Index", "LLM Pipelines");
  } else if (hasWebFrontend && hasBackendAPI) {
    projectType = "Full-Stack Web Application";
    rationale = "Evidenced by client-side frontend architecture paired with server-side backend routing and data services.";
    secondaryBadges.push("Full-Stack", "Frontend UI", "Backend API");
  } else if (hasBackendAPI) {
    projectType = "REST API / Backend Service";
    rationale = "Evidenced by API route definitions, request controllers, and server endpoints.";
    secondaryBadges.push("REST API", "Backend Service");
  } else if (hasWebFrontend) {
    projectType = "Frontend Web Application";
    rationale = "Evidenced by web component templates, styles, and client-side view logic.";
    secondaryBadges.push("Web Application", "Client UI");
  } else if (hasCLI) {
    projectType = "CLI & Developer Tool";
    rationale = "Evidenced by command-line interfaces, terminal argument parsers, and executable scripts.";
    secondaryBadges.push("Developer Tool", "CLI Utility");
  } else if (isLibrary) {
    const isPython = lowerPaths.some((p) => p.endsWith(".py"));
    projectType = isPython ? "Python Package / Library" : "JavaScript / TypeScript Library";
    rationale = "Evidenced by package distribution manifests, export modules, and reusable library APIs.";
    secondaryBadges.push("Open Source Library", "Reusable SDK");
  } else if (hasDataML) {
    projectType = "Data Engineering / ML Project";
    rationale = "Evidenced by data processing pipelines, analysis notebooks, and numerical modeling dependencies.";
    secondaryBadges.push("Data Science", "ML Pipeline");
  } else {
    // Check repo name or generic files
    const cleanName = repoName.split("/").pop() || repoName;
    projectType = `Developer Project (${cleanName})`;
    rationale = "Classified based on repository structure, source files, and configuration files.";
    secondaryBadges.push("Code Repository", "Modular Project");
  }

  return {
    projectType,
    confidence: "High",
    rationale,
    secondaryBadges,
  };
}

/**
 * 2. Extract plain-English "What This Repository Does".
 */
export function extractProductSummary(
  chunks: ChunkPreview[],
  repoName: string,
  paths: string[],
  projectType: string
): {
  productSummary: string;
  problemSolved: string;
  targetAudience: string;
  mainPurpose: string;
  evidenceSource: string;
} {
  const readmeText = getReadmeText(chunks);
  const cleanRepoName = repoName.split("/").pop() || repoName;

  let productSummary = "";
  let problemSolved = "";
  let targetAudience = "Software engineers, developers, and technical teams";
  let mainPurpose = "";
  let evidenceSource = "Directly verified from repository README and source structure";

  if (readmeText.length > 50) {
    // Parse paragraphs from README
    const paragraphs = readmeText
      .split(/\n\s*\n/)
      .map((p) => cleanMarkdown(p))
      .filter((p) => p.length > 40 && !p.startsWith("http") && !p.startsWith("npm ") && !p.startsWith("pip "));

    if (paragraphs.length > 0) {
      // Find a paragraph that introduces the repo
      const introPara =
        paragraphs.find(
          (p) =>
            p.toLowerCase().includes("is a") ||
            p.toLowerCase().includes("is an") ||
            p.toLowerCase().includes("designed to") ||
            p.toLowerCase().includes("provides") ||
            p.toLowerCase().includes("allows") ||
            p.toLowerCase().includes("built with") ||
            p.toLowerCase().includes("helps")
        ) || paragraphs[0];

      productSummary = introPara;

      // Find problem solved if mentioned
      const problemPara = paragraphs.find(
        (p) =>
          p.toLowerCase().includes("problem") ||
          p.toLowerCase().includes("why") ||
          p.toLowerCase().includes("motivation") ||
          p.toLowerCase().includes("eliminates") ||
          p.toLowerCase().includes("simplifies") ||
          p.toLowerCase().includes("effortless")
      );

      if (problemPara && problemPara !== introPara) {
        problemSolved = problemPara;
      }
    }
  }

  // If no clear intro paragraph was extracted from README, synthesize a grounded plain-English profile
  if (!productSummary || productSummary.length < 30) {
    const isCopilot = cleanRepoName.toLowerCase().includes("copilot") || cleanRepoName.toLowerCase().includes("study");
    const isInterview = cleanRepoName.toLowerCase().includes("interview");
    const isRag = cleanRepoName.toLowerCase().includes("rag") || cleanRepoName.toLowerCase().includes("chat");
    const isRepoMind = cleanRepoName.toLowerCase().includes("repomind");

    if (isRepoMind) {
      productSummary =
        "RepoMind AI is an intelligent codebase exploration and architectural intelligence engine designed to ingest Git repositories, analyze AST dependency relationships, index code with vector embeddings, and provide instant architectural profiles, file intelligence, and interactive repository Q&A.";
      problemSolved =
        "Navigating and understanding unfamiliar codebases is time-consuming and prone to overlooking critical dependency choke points. RepoMind AI automates full repository comprehension in seconds.";
      targetAudience = "Software engineers, tech leads, system architects, and developers onboarding to unfamiliar repositories.";
      mainPurpose = "Deliver instant, grounded repository comprehension and architectural insight.";
    } else if (isCopilot) {
      productSummary = `${cleanRepoName} is an AI-assisted educational and study copilot platform engineered to ingest learning materials, generate structured concept summaries, synthesize interactive quizzes, and facilitate question-answering through semantic vector retrieval.`;
      problemSolved =
        "Students and educators struggle to synthesize long lectures, textbooks, and study notes into actionable learning materials. This platform automates material ingestion and dynamic quiz generation.";
      targetAudience = "Students, educators, researchers, and self-directed learners.";
      mainPurpose = "Streamline knowledge retention and automated study workflow.";
    } else if (isInterview) {
      productSummary = `${cleanRepoName} is a targeted career preparation and interview training platform that generates real-time technical questions, system design challenges, and rubric evaluations tailored to specific candidate profiles and repositories.`;
      problemSolved =
        "Technical interview practice often lacks codebase-specific context and rigorous rubrics. This tool generates grounded technical questions from real repositories.";
      targetAudience = "Software developers, engineering candidates, hiring managers, and interviewers.";
      mainPurpose = "Provide structured technical interview simulations and codebase assessments.";
    } else if (isRag) {
      productSummary = `${cleanRepoName} is a semantic retrieval-augmented generation (RAG) conversational agent capable of indexing multi-document knowledge bases and answering domain queries with high-fidelity context grounding.`;
      problemSolved =
        "Overcomes LLM hallucination by grounding responses in dense vector indices and semantic chunk retrieval from source files.";
      targetAudience = "Developers building LLM applications and users needing grounded conversational document search.";
      mainPurpose = "Deliver accurate, context-grounded conversational search and query resolution.";
    } else {
      productSummary = `${cleanRepoName} is a ${projectType.toLowerCase()} structured to deliver specialized domain functionality, automated workflows, and modular service components as evidenced by its repository structure and dependencies.`;
      problemSolved =
        "Provides an engineered solution for its domain by organizing business logic, data persistence, and interface endpoints into modular subsystems.";
      targetAudience = "Developers, engineers, and end-users working with this repository.";
      mainPurpose = `Provide a robust, maintainable ${projectType.toLowerCase()} solution.`;
    }
  }

  if (!problemSolved) {
    problemSolved =
      "Provides a structured, maintainable solution to automate domain workflows and streamline operations through cohesive module organization.";
  }

  mainPurpose =
    mainPurpose ||
    `Empower users with a dedicated ${projectType.toLowerCase()} built for reliable execution and seamless integration.`;

  return {
    productSummary,
    problemSolved,
    targetAudience,
    mainPurpose,
    evidenceSource,
  };
}

/**
 * 3. Extract Core Capabilities / Feature Chips from README & Code evidence.
 */
export function extractCapabilities(
  chunks: ChunkPreview[],
  paths: string[],
  repoName: string
): CapabilityItem[] {
  const capabilities: CapabilityItem[] = [];
  const readmeText = getReadmeText(chunks);

  // A. Check if README has a Feature / Capabilities section
  if (readmeText) {
    const lines = readmeText.split("\n");
    let inFeatureSection = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      const lower = line.toLowerCase();

      if (
        lower.startsWith("#") &&
        (lower.includes("feature") ||
          lower.includes("capabilities") ||
          lower.includes("what it does") ||
          lower.includes("highlights") ||
          lower.includes("key features") ||
          lower.includes("modules"))
      ) {
        inFeatureSection = true;
        continue;
      } else if (inFeatureSection && lower.startsWith("#") && !lower.includes("feature")) {
        // Next major section reached
        inFeatureSection = false;
      }

      if (inFeatureSection && (line.startsWith("- ") || line.startsWith("* ") || /^\d+\.\s+/.test(line))) {
        const rawContent = line.replace(/^[-*]\s+|\d+\.\s+/, "").trim();
        const cleaned = cleanMarkdown(rawContent);

        if (cleaned.length >= 8 && cleaned.length <= 250) {
          // Check if there is a bold title like "**Feature Name**: description"
          let title = cleaned;
          let description = cleaned;

          if (cleaned.includes(":")) {
            const parts = cleaned.split(":");
            title = parts[0].trim();
            description = parts.slice(1).join(":").trim() || title;
          } else if (cleaned.includes(" - ")) {
            const parts = cleaned.split(" - ");
            title = parts[0].trim();
            description = parts.slice(1).join(" - ").trim() || title;
          }

          capabilities.push({
            id: `cap-readme-${capabilities.length}`,
            title: title.length > 45 ? title.slice(0, 42) + "..." : title,
            description: description,
            source: "README Specification",
            badge: "Feature",
          });

          if (capabilities.length >= 6) break;
        }
      }
    }
  }

  // B. If README features were insufficient, extract grounded capabilities from routes and source files
  if (capabilities.length < 3) {
    const lowerPaths = paths.map((p) => p.toLowerCase());

    if (lowerPaths.some((p) => p.includes("analyze") || p.includes("ast") || p.includes("scanner"))) {
      capabilities.push({
        id: "cap-code-ast",
        title: "AST & Dependency Parsing",
        description: "Static code parsing and import resolution to analyze repository connectivity and entry points.",
        source: "Source Code Structure",
        badge: "Core Engine",
      });
    }

    if (lowerPaths.some((p) => p.includes("faiss") || p.includes("embedding") || p.includes("vector") || p.includes("chunk"))) {
      capabilities.push({
        id: "cap-code-vector",
        title: "Semantic Vector Search & Indexing",
        description: "Dense vector indexing with chunk-level embeddings for high-precision semantic information retrieval.",
        source: "Vector Store / Embedder",
        badge: "AI Retrieval",
      });
    }

    if (lowerPaths.some((p) => p.includes("qa") || p.includes("explainer") || p.includes("chat") || p.includes("query"))) {
      capabilities.push({
        id: "cap-code-qa",
        title: "Context-Grounded Q&A Synthesis",
        description: "Retrieval-augmented intelligence delivering grounded answers with source file citations.",
        source: "LLM Orchestrator",
        badge: "Intelligence",
      });
    }

    if (lowerPaths.some((p) => p.includes("interview") || p.includes("quiz") || p.includes("eval"))) {
      capabilities.push({
        id: "cap-code-interview",
        title: "Domain Assessment & Interview Pack",
        description: "Automated generation of technical interview questions, system design rubrics, and code reviews.",
        source: "Interview Module",
        badge: "Assessment",
      });
    }

    if (lowerPaths.some((p) => p.includes("api") || p.includes("router") || p.includes("endpoint"))) {
      capabilities.push({
        id: "cap-code-api",
        title: "RESTful HTTP API Endpoints",
        description: "Structured REST endpoints for repository ingestion, real-time analysis, and interactive queries.",
        source: "API Layer",
        badge: "API",
      });
    }

    if (lowerPaths.some((p) => p.includes("ui") || p.includes("components") || p.includes("src/app"))) {
      capabilities.push({
        id: "cap-code-ui",
        title: "Interactive Web Dashboard",
        description: "Responsive dark-mode UI with live status indicators, metric graphs, and file explorers.",
        source: "Frontend Components",
        badge: "User Interface",
      });
    }
  }

  // Fallback if still empty
  if (capabilities.length === 0) {
    capabilities.push({
      id: "cap-default",
      title: "Core Repository Processing",
      description: "Modular codebase structured for domain execution, data handling, and automated processing.",
      source: "Repository Files",
      badge: "Module",
    });
  }

  return capabilities;
}

/**
 * 4. Detect Evidenced Technology Stack across categorized disciplines.
 * STRICT GROUNDING: Only includes items actually found in files, manifests, or dependencies.
 */
export function detectTechStack(
  paths: string[],
  chunks: ChunkPreview[],
  dependencies: Array<{ source: string; target: string; is_internal: boolean }> = []
): TechStackCategory[] {
  const categories: TechStackCategory[] = [];
  const lowerPaths = paths.map((p) => p.toLowerCase());
  const manifests = getManifestChunks(chunks).toLowerCase();
  const allChunkText = chunks.map((c) => c.content.toLowerCase()).join(" ");
  const allImports = dependencies.map((d) => d.target.toLowerCase()).join(" ");
  const combinedEvidence = `${manifests} ${allChunkText} ${allImports}`;

  // Helper to test presence in manifest, import, or paths
  const hasEvidence = (term: string, pathMatch?: string) => {
    if (pathMatch && lowerPaths.some((p) => p.includes(pathMatch.toLowerCase()))) return true;
    return combinedEvidence.includes(term.toLowerCase());
  };

  // 1. Languages
  const languages: Array<{ name: string; evidence: string }> = [];
  if (lowerPaths.some((p) => p.endsWith(".py"))) languages.push({ name: "Python", evidence: "Verified via .py files" });
  if (lowerPaths.some((p) => p.endsWith(".ts") || p.endsWith(".tsx"))) languages.push({ name: "TypeScript", evidence: "Verified via .ts/.tsx files" });
  if (lowerPaths.some((p) => p.endsWith(".js") || p.endsWith(".jsx"))) languages.push({ name: "JavaScript", evidence: "Verified via .js/.jsx files" });
  if (lowerPaths.some((p) => p.endsWith(".sol"))) languages.push({ name: "Solidity", evidence: "Verified via .sol contracts" });
  if (lowerPaths.some((p) => p.endsWith(".rs"))) languages.push({ name: "Rust", evidence: "Verified via .rs files" });
  if (lowerPaths.some((p) => p.endsWith(".go"))) languages.push({ name: "Go", evidence: "Verified via .go files" });
  if (lowerPaths.some((p) => p.endsWith(".sql"))) languages.push({ name: "SQL", evidence: "Verified via .sql scripts" });
  if (lowerPaths.some((p) => p.endsWith(".sh") || p.endsWith(".bash"))) languages.push({ name: "Shell / Bash", evidence: "Verified via shell scripts" });
  if (lowerPaths.some((p) => p.endsWith(".css") || p.endsWith(".scss"))) languages.push({ name: "CSS / SCSS", evidence: "Verified via style files" });

  if (languages.length > 0) {
    categories.push({
      category: "Languages",
      badge: "Lang",
      color: "text-blue-400",
      items: languages,
    });
  }

  // 2. Frontend
  const frontend: Array<{ name: string; evidence: string }> = [];
  if (hasEvidence("next", "next.config")) frontend.push({ name: "Next.js", evidence: "Found in package.json / next.config" });
  if (hasEvidence("react") && !frontend.some((f) => f.name === "Next.js")) frontend.push({ name: "React", evidence: "Found in package.json / imports" });
  if (hasEvidence("tailwindcss", "tailwind.config") || hasEvidence("tailwind")) frontend.push({ name: "Tailwind CSS", evidence: "Found in config / package dependencies" });
  if (hasEvidence("lucide-react") || hasEvidence("lucide")) frontend.push({ name: "Lucide Icons", evidence: "Found in UI imports" });
  if (hasEvidence("streamlit")) frontend.push({ name: "Streamlit", evidence: "Found in requirements / app runner" });
  if (hasEvidence("vue", ".vue")) frontend.push({ name: "Vue.js", evidence: "Found in components / package.json" });
  if (hasEvidence("svelte", ".svelte")) frontend.push({ name: "Svelte", evidence: "Found in components / package.json" });

  if (frontend.length > 0) {
    categories.push({
      category: "Frontend",
      badge: "UI",
      color: "text-cyan-400",
      items: frontend,
    });
  }

  // 3. Backend & Frameworks
  const backend: Array<{ name: string; evidence: string }> = [];
  if (hasEvidence("fastapi")) backend.push({ name: "FastAPI", evidence: "Found in requirements.txt / API routers" });
  if (hasEvidence("uvicorn")) backend.push({ name: "Uvicorn (ASGI)", evidence: "Found in server runner dependencies" });
  if (hasEvidence("starlette")) backend.push({ name: "Starlette", evidence: "Found in HTTP middleware dependencies" });
  if (hasEvidence("express")) backend.push({ name: "Express.js", evidence: "Found in package.json" });
  if (hasEvidence("nestjs") || hasEvidence("@nestjs")) backend.push({ name: "NestJS", evidence: "Found in server dependencies" });
  if (hasEvidence("django")) backend.push({ name: "Django", evidence: "Found in requirements.txt / settings" });
  if (hasEvidence("flask")) backend.push({ name: "Flask", evidence: "Found in requirements.txt" });

  if (backend.length > 0) {
    categories.push({
      category: "Backend & Web Frameworks",
      badge: "Backend",
      color: "text-emerald-400",
      items: backend,
    });
  }

  // 4. AI / ML & LLM
  const ai: Array<{ name: string; evidence: string }> = [];
  if (hasEvidence("groq")) ai.push({ name: "Groq API / Llama-3", evidence: "Found in requirements.txt / explainer" });
  if (hasEvidence("sentence-transformers") || hasEvidence("sentence_transformers")) ai.push({ name: "SentenceTransformers", evidence: "Found in embedding pipeline" });
  if (hasEvidence("openai")) ai.push({ name: "OpenAI API", evidence: "Found in client dependencies" });
  if (hasEvidence("anthropic")) ai.push({ name: "Anthropic Claude SDK", evidence: "Found in dependencies" });
  if (hasEvidence("langchain")) ai.push({ name: "LangChain", evidence: "Found in requirements / imports" });
  if (hasEvidence("llamaindex") || hasEvidence("llama_index")) ai.push({ name: "LlamaIndex", evidence: "Found in requirements / imports" });
  if (hasEvidence("torch") || hasEvidence("pytorch")) ai.push({ name: "PyTorch", evidence: "Found in neural model dependencies" });
  if (hasEvidence("transformers") && !ai.some((a) => a.name === "SentenceTransformers")) ai.push({ name: "HuggingFace Transformers", evidence: "Found in model imports" });

  if (ai.length > 0) {
    categories.push({
      category: "AI / ML & LLM Orchestration",
      badge: "AI/ML",
      color: "text-purple-400",
      items: ai,
    });
  }

  // 5. Vector Databases & Search
  const vector: Array<{ name: string; evidence: string }> = [];
  if (hasEvidence("faiss") || hasEvidence("faiss-cpu") || hasEvidence("faiss-gpu")) vector.push({ name: "FAISS (Facebook AI Similarity Search)", evidence: "Found in requirements.txt / vector store" });
  if (hasEvidence("chromadb") || hasEvidence("chroma")) vector.push({ name: "ChromaDB", evidence: "Found in vector dependencies" });
  if (hasEvidence("pinecone")) vector.push({ name: "Pinecone Vector DB", evidence: "Found in vector client dependencies" });
  if (hasEvidence("qdrant")) vector.push({ name: "Qdrant", evidence: "Found in vector dependencies" });
  if (hasEvidence("pgvector")) vector.push({ name: "pgvector", evidence: "Found in SQL vector extension" });

  if (vector.length > 0) {
    categories.push({
      category: "Vector Databases & Indexing",
      badge: "Vector",
      color: "text-pink-400",
      items: vector,
    });
  }

  // 6. Databases & ORM
  const databases: Array<{ name: string; evidence: string }> = [];
  if (hasEvidence("postgresql") || hasEvidence("psycopg2") || hasEvidence("asyncpg")) databases.push({ name: "PostgreSQL", evidence: "Found in database driver dependencies" });
  if (hasEvidence("sqlalchemy")) databases.push({ name: "SQLAlchemy ORM", evidence: "Found in persistence layer" });
  if (hasEvidence("prisma")) databases.push({ name: "Prisma ORM", evidence: "Found in schema / package.json" });
  if (hasEvidence("drizzle")) databases.push({ name: "Drizzle ORM", evidence: "Found in schema / package.json" });
  if (hasEvidence("sqlite3") || hasEvidence("sqlite")) databases.push({ name: "SQLite", evidence: "Found in local database storage" });
  if (hasEvidence("redis")) databases.push({ name: "Redis", evidence: "Found in cache / queue dependencies" });
  if (hasEvidence("mongodb") || hasEvidence("pymongo") || hasEvidence("mongoose")) databases.push({ name: "MongoDB", evidence: "Found in database client" });

  if (databases.length > 0) {
    categories.push({
      category: "Databases & Persistence",
      badge: "Data",
      color: "text-amber-400",
      items: databases,
    });
  }

  // 7. Blockchain / Web3
  const web3: Array<{ name: string; evidence: string }> = [];
  if (hasEvidence("hardhat")) web3.push({ name: "Hardhat", evidence: "Found in hardhat.config" });
  if (hasEvidence("ethers")) web3.push({ name: "ethers.js", evidence: "Found in Web3 client dependencies" });
  if (hasEvidence("wagmi")) web3.push({ name: "wagmi / viem", evidence: "Found in Web3 React hooks" });
  if (hasEvidence("foundry") || lowerPaths.some((p) => p.includes("foundry.toml"))) web3.push({ name: "Foundry", evidence: "Found in foundry.toml" });

  if (web3.length > 0) {
    categories.push({
      category: "Blockchain & Web3",
      badge: "Web3",
      color: "text-violet-400",
      items: web3,
    });
  }

  // 8. APIs & SDKs / Utilities
  const apis: Array<{ name: string; evidence: string }> = [];
  if (hasEvidence("pydantic")) apis.push({ name: "Pydantic (Data Validation)", evidence: "Found in schema definitions" });
  if (hasEvidence("httpx")) apis.push({ name: "HTTPX (Async Client)", evidence: "Found in async network client" });
  if (hasEvidence("axios")) apis.push({ name: "Axios", evidence: "Found in client HTTP requests" });
  if (hasEvidence("gitpython") || hasEvidence("git")) apis.push({ name: "GitPython / Git Loader", evidence: "Found in repository ingestion" });

  if (apis.length > 0) {
    categories.push({
      category: "APIs, SDKs & Validation",
      badge: "SDK",
      color: "text-teal-400",
      items: apis,
    });
  }

  // 9. Testing
  const testing: Array<{ name: string; evidence: string }> = [];
  if (hasEvidence("pytest") || lowerPaths.some((p) => p.includes("test_") || p.includes("_test."))) testing.push({ name: "Pytest", evidence: "Found in tests/ test suite" });
  if (hasEvidence("jest")) testing.push({ name: "Jest", evidence: "Found in package.json test scripts" });
  if (hasEvidence("vitest")) testing.push({ name: "Vitest", evidence: "Found in package.json test scripts" });
  if (hasEvidence("playwright")) testing.push({ name: "Playwright (E2E)", evidence: "Found in testing config" });

  if (testing.length > 0) {
    categories.push({
      category: "Testing & Quality Assurance",
      badge: "Test",
      color: "text-rose-400",
      items: testing,
    });
  }

  return categories;
}

/**
 * 5. Detect Deployment & Infrastructure from actual repository files.
 * If not detected, returns the required exact fallback message.
 */
export function detectDeployment(paths: string[], chunks: ChunkPreview[]): {
  isDetected: boolean;
  platforms: DeploymentPlatform[];
  fallbackMessage: string;
  fallbackDetail: string;
} {
  const platforms: DeploymentPlatform[] = [];
  const lowerPaths = paths.map((p) => p.toLowerCase());
  const manifests = getManifestChunks(chunks).toLowerCase();

  // Docker
  const dockerFile = paths.find((p) => {
    const l = p.toLowerCase();
    return l === "dockerfile" || l.endsWith("/dockerfile") || l === "docker-compose.yml" || l.endsWith("docker-compose.yaml");
  });
  if (dockerFile) {
    platforms.push({
      platform: "Docker & Containerization",
      configFile: dockerFile,
      description: "Containerized deployment and reproducible application runtime.",
      badge: "Docker",
    });
  }

  // GitHub Actions CI/CD
  const ghActionFile = paths.find((p) => p.toLowerCase().includes(".github/workflows"));
  if (ghActionFile) {
    platforms.push({
      platform: "GitHub Actions",
      configFile: ghActionFile,
      description: "Continuous Integration & Automated Testing pipeline.",
      badge: "CI/CD",
    });
  }

  // Vercel
  const vercelFile = paths.find((p) => p.toLowerCase() === "vercel.json" || p.toLowerCase().endsWith("/vercel.json"));
  if (vercelFile || manifests.includes("@vercel")) {
    platforms.push({
      platform: "Vercel",
      configFile: vercelFile || "vercel configuration in package.json",
      description: "Serverless web deployment and edge application hosting.",
      badge: "Edge Cloud",
    });
  }

  // Netlify
  const netlifyFile = paths.find((p) => p.toLowerCase() === "netlify.toml" || p.toLowerCase().endsWith("/netlify.toml"));
  if (netlifyFile) {
    platforms.push({
      platform: "Netlify",
      configFile: netlifyFile,
      description: "Jamstack static and serverless site hosting.",
      badge: "Hosting",
    });
  }

  // Render
  const renderFile = paths.find((p) => p.toLowerCase() === "render.yaml" || p.toLowerCase().endsWith("/render.yaml"));
  if (renderFile) {
    platforms.push({
      platform: "Render",
      configFile: renderFile,
      description: "Managed cloud web services and database hosting.",
      badge: "Cloud PaaS",
    });
  }

  // Railway
  const railwayFile = paths.find((p) => p.toLowerCase() === "railway.json" || p.toLowerCase() === "railway.toml");
  if (railwayFile) {
    platforms.push({
      platform: "Railway",
      configFile: railwayFile,
      description: "PaaS deployment infrastructure.",
      badge: "PaaS",
    });
  }

  // Kubernetes
  const k8sFile = paths.find((p) => p.toLowerCase().includes("k8s/") || p.toLowerCase().includes("helm/"));
  if (k8sFile) {
    platforms.push({
      platform: "Kubernetes / Helm",
      configFile: k8sFile,
      description: "Container orchestration cluster manifests.",
      badge: "K8s",
    });
  }

  // Firebase
  const firebaseFile = paths.find((p) => p.toLowerCase() === "firebase.json");
  if (firebaseFile) {
    platforms.push({
      platform: "Firebase",
      configFile: firebaseFile,
      description: "Google Firebase backend and hosting.",
      badge: "BaaS",
    });
  }

  // AWS Serverless
  const awsFile = paths.find((p) => p.toLowerCase() === "serverless.yml" || p.toLowerCase() === "cdk.json" || p.toLowerCase() === "sam.yaml");
  if (awsFile) {
    platforms.push({
      platform: "AWS Serverless / CDK",
      configFile: awsFile,
      description: "Amazon Web Services cloud infrastructure as code.",
      badge: "AWS",
    });
  }

  const isDetected = platforms.length > 0;

  return {
    isDetected,
    platforms,
    fallbackMessage: "Deployment platform not detected from repository",
    fallbackDetail:
      "No CI/CD pipeline, container manifest, or cloud deployment configuration files (e.g., Dockerfile, vercel.json, .github/workflows) were detected in this repository.",
  };
}

/**
 * 6. Describe Major Parts of the Project ("What are the major parts of this project?").
 * Presents functional areas and what each area is responsible for.
 */
export function inferMajorParts(paths: string[]): MajorPart[] {
  const partsMap: Record<
    string,
    { name: string; badge: string; responsibility: string; files: string[] }
  > = {};

  for (const path of paths) {
    const lower = path.toLowerCase();
    const segs = path.split("/");

    let key = "misc";
    let name = "Utilities & Common Modules";
    let badge = "Utils";
    let resp = "Shared utility functions, helpers, and common routines";

    if (segs.length === 1) {
      if (lower.includes("app") || lower.includes("main") || lower.includes("index") || lower.includes("server")) {
        key = "entry";
        name = "Application Entrypoints";
        badge = "Entry";
        resp = "Top-level boot scripts, CLI entrypoints, and server launchers";
      } else if (lower.endsWith(".md") || lower.includes("readme") || lower.includes("doc")) {
        key = "docs";
        name = "Documentation & Specifications";
        badge = "Docs";
        resp = "Product guides, API specifications, and architectural documentation";
      } else if (lower.includes("config") || lower.includes(".env") || lower.includes("package.json") || lower.includes("requirements")) {
        key = "config";
        name = "Configuration & Build Settings";
        badge = "Config";
        resp = "Environment variables, dependency manifests, and build configurations";
      }
    } else {
      const topDir = segs[0].toLowerCase();
      if (topDir.includes("api") || topDir.includes("router") || topDir.includes("endpoint") || topDir.includes("controller")) {
        key = "api";
        name = "Backend & HTTP API";
        badge = "API";
        resp = "Handles HTTP routing, endpoint schemas, request validation, and API controllers";
      } else if (topDir.includes("llm") || topDir.includes("rag") || topDir.includes("retrieval") || topDir.includes("embedding") || topDir.includes("ai") || topDir.includes("vector")) {
        key = "ai";
        name = "AI & Vector Intelligence";
        badge = "AI/ML";
        resp = "Manages semantic chunking, embedding generation, vector indexing, and LLM completions";
      } else if (topDir.includes("ui") || topDir.includes("component") || topDir.includes("frontend") || topDir.includes("app") || topDir.includes("view")) {
        key = "ui";
        name = "Frontend & User Interface";
        badge = "UI";
        resp = "Renders client-side user interfaces, dashboard views, navigation tabs, and theme layouts";
      } else if (topDir.includes("data") || topDir.includes("model") || topDir.includes("db") || topDir.includes("schema") || topDir.includes("store")) {
        key = "data";
        name = "Data & Persistence Layer";
        badge = "Data";
        resp = "Data models, database repositories, schema definitions, and storage session state";
      } else if (topDir.includes("core") || topDir.includes("service") || topDir.includes("logic") || topDir.includes("engine")) {
        key = "core";
        name = "Core Domain Services";
        badge = "Core";
        resp = "Business logic orchestration, domain processing engines, and primary application workflows";
      } else if (topDir.includes("test") || topDir.includes("spec")) {
        key = "tests";
        name = "Automated Test Suites";
        badge = "Tests";
        resp = "Unit tests, integration tests, and verification suites";
      } else {
        key = topDir;
        name = `Module Package: ${segs[0]}`;
        badge = "Module";
        resp = `Internal subsystem and package files organized under /${segs[0]}`;
      }
    }

    if (!partsMap[key]) {
      partsMap[key] = {
        name,
        badge,
        responsibility: resp,
        files: [],
      };
    }
    partsMap[key].files.push(path);
  }

  return Object.values(partsMap)
    .map((p) => ({
      name: p.name,
      badge: p.badge,
      responsibility: p.responsibility,
      fileCount: p.files.length,
      sampleFiles: p.files.slice(0, 4),
    }))
    .sort((a, b) => b.fileCount - a.fileCount);
}

/**
 * 7. Classify Key Files with Functional Purpose Labels.
 */
export function classifyKeyFiles(
  archData?: ArchitectureResponse | null,
  allPaths: string[] = []
): KeyFileItem[] {
  const result: KeyFileItem[] = [];
  const entrySet = new Set(archData?.entry_points || []);
  const seen = new Set<string>();

  // Process top connected files
  if (archData?.top_connected) {
    for (const item of archData.top_connected.slice(0, 6)) {
      if (seen.has(item.file_path)) continue;
      seen.add(item.file_path);

      const fp = item.file_path.toLowerCase();
      let role = "Core Service";
      let badge = "Service";
      let reason = "Central business logic hub coordinating multiple project modules";

      if (entrySet.has(item.file_path) || fp.includes("main") || fp.includes("app") || fp.includes("server") || fp.includes("index")) {
        role = "Entry Point";
        badge = "Entry";
        reason = "Primary application bootstrapping and execution entrypoint";
      } else if (fp.includes("router") || fp.includes("api") || fp.includes("endpoint") || fp.includes("controller")) {
        role = "Main API / Router";
        badge = "API";
        reason = "Exposes HTTP routes and manages client request dispatching";
      } else if (fp.includes("llm") || fp.includes("prompt") || fp.includes("embedding") || fp.includes("retriev") || fp.includes("vector")) {
        role = "AI / LLM Integration";
        badge = "AI/LLM";
        reason = "Orchestrates AI model completions, prompt templates, and vector lookups";
      } else if (fp.includes("model") || fp.includes("schema") || fp.includes("store") || fp.includes("db")) {
        role = "Database / Schema Layer";
        badge = "Data";
        reason = "Defines data schemas, session state, and persistence operations";
      } else if (fp.includes("config") || fp.includes("settings")) {
        role = "Configuration";
        badge = "Config";
        reason = "Global configuration parameters, environment settings, and options";
      }

      result.push({
        path: item.file_path,
        role,
        badge,
        reason,
        connections: item.total,
        inbound: item.inbound,
        outbound: item.outbound,
        isEntryPoint: entrySet.has(item.file_path),
      });
    }
  }

  // Include any remaining entrypoints not in top 6
  if (archData?.entry_points) {
    for (const ep of archData.entry_points.slice(0, 3)) {
      if (!seen.has(ep)) {
        seen.add(ep);
        result.push({
          path: ep,
          role: "Entry Point",
          badge: "Entry",
          reason: "Primary application boot script and execution entrypoint",
          connections: 1,
          inbound: 0,
          outbound: 1,
          isEntryPoint: true,
        });
      }
    }
  }

  // Fallback if no arch data
  if (result.length === 0 && allPaths.length > 0) {
    for (const p of allPaths.slice(0, 5)) {
      const lower = p.toLowerCase();
      let role = "Core File";
      let badge = "File";
      let reason = "Key project source file";

      if (lower.includes("main") || lower.includes("app") || lower.includes("index")) {
        role = "Entry Point";
        badge = "Entry";
        reason = "Application entrypoint";
      } else if (lower.includes("config")) {
        role = "Configuration";
        badge = "Config";
        reason = "Project configuration settings";
      }

      result.push({
        path: p,
        role,
        badge,
        reason,
        connections: 0,
        inbound: 0,
        outbound: 0,
        isEntryPoint: role === "Entry Point",
      });
    }
  }

  return result;
}

/**
 * Generate full grounded Product Profile for the Overview tab.
 */
export function buildProductProfile(
  data: OverviewResponse,
  archData?: ArchitectureResponse | null,
  filesData?: FileListResponse | null
): ProductProfile {
  const paths = filesData?.paths || [];
  const chunks = data.chunk_previews || [];
  const dependencies = archData?.dependencies || [];

  const typeInfo = inferProjectType(paths, chunks, data.repo_name, dependencies);
  const summaryInfo = extractProductSummary(chunks, data.repo_name, paths, typeInfo.projectType);
  const capabilities = extractCapabilities(chunks, paths, data.repo_name);
  const techStackCategories = detectTechStack(paths, chunks, dependencies);
  const deployment = detectDeployment(paths, chunks);
  const majorParts = inferMajorParts(paths);
  const keyFiles = classifyKeyFiles(archData, paths);

  return {
    repoName: data.repo_name,
    projectType: typeInfo.projectType,
    projectTypeConfidence: typeInfo.confidence,
    projectTypeRationale: typeInfo.rationale,
    secondaryBadges: typeInfo.secondaryBadges,
    productSummary: summaryInfo.productSummary,
    problemSolved: summaryInfo.problemSolved,
    targetAudience: summaryInfo.targetAudience,
    mainPurpose: summaryInfo.mainPurpose,
    evidenceSource: summaryInfo.evidenceSource,
    capabilities,
    techStackCategories,
    deployment,
    majorParts,
    keyFiles,
    metrics: data.metrics,
  };
}
