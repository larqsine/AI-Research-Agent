# Evaluation results

Run on 2026-11-21 10:57 | model: `groq:openai/gpt-oss-120b` | 14 prompts | 0 crashed

## Summary (code graders)

| Check | Passed | Out of |
|---|---|---|
| Found a paper when one exists / said so when none exists | 14 | 14 |
| Respected the year limit | 10 | 10 |
| Respected the citation limit | 9 | 9 |
| Gave a valid source | 12 | 12 |
| Facts match OpenAlex (nothing made up) | 12 | 12 |

Per prompt on average: 1.2 tool calls, 4.0 LLM requests, 3435.7 tokens, 14.4 seconds.

## Per prompt

✅ pass, ❌ fail, — does not apply, ? = a human must fill this in (read the details below, then replace the ? with ✅ or ❌).

| ID | What it tests | Found as expected | Year | Citations | Valid source | Facts match API | Tool calls | Relevant paper (human) | No made-up claims in text (human) | Useful explanation (human) |
|---|---|---|---|---|---|---|---|---|---|---|
| T01 | after year + minimum citations (assignment example) | ✅ | ✅ | ✅ | ✅ | ✅ | 1 | ✅ | ✅ | ✅ |
| T02 | before year + more than N citations (assignment example) | ✅ | ✅ | ✅ | ✅ | ✅ | 1 | ✅ | ❌ | ✅ |
| T03 | vague year word 'recent', no citation limit (assignment example) | ✅ | ✅ | — | ✅ | ✅ | 1 | ✅ | ✅ | ✅ |
| T04 | exact year + very high minimum citations | ✅ | ✅ | ✅ | ✅ | ✅ | 1 | ✅ | ✅ | ✅ |
| T05 | narrow topic + after year + minimum citations | ✅ | ✅ | ✅ | ✅ | ✅ | 1 | ✅ | ✅ | ✅ |
| T06 | narrow topic + maximum citations | ✅ | ✅ | ✅ | ✅ | ✅ | 1 | ✅ | ✅ | ✅ |
| T07 | broad topic + approximate citations | ✅ | — | ✅ | ✅ | ✅ | 1 | ✅ | ✅ | ✅ |
| T08 | narrow topic + since year (inclusive) + minimum citations | ✅ | ✅ | ✅ | ✅ | ✅ | 1 | ✅ | ✅ | ✅ |
| T09 | no good paper exists (topic did not exist yet) | ✅ | — | — | — | — | 2 | — | ✅ | ✅ |
| T10 | no good paper exists (impossible citation count) | ✅ | — | — | — | — | 3 | — | ✅ | ✅ |
| T11 | ambiguous request (unclear topic, no limits) | ✅ | — | — | ✅ | ✅ | 1 | ✅ | ✅ | ✅ |
| T12 | ambiguous request (vague words: recent, popular, agents) | ✅ | ✅ | — | ✅ | ✅ | 1 | ✅ | ❌ | ✅ |
| T13 | year range (between two years) + minimum citations | ✅ | ✅ | ✅ | ✅ | ✅ | 1 | ✅ | ✅ | ✅ |
| T14 | until year (inclusive) + maximum citations | ✅ | ✅ | ✅ | ✅ | ✅ | 1 | ✅ | ✅ | ✅ |

**Human grades** (filled in by hand after reading each explanation next to its abstract):
relevant paper 12/12, no made-up claims 12/14, useful explanation 14/14.

## Notes on the human grades

- **T12, made-up claim (❌):** the explanation calls "Demystifying LLM-Based Software Engineering Agents"
  a "comprehensive overview" of agents. The abstract says the authors build **Agentless**, a simple
  approach *without* an agent. The same mistake happened in the first run (T01 and T12 then).
- **T02, made-up claims (❌):** the summary says RAG was tested on "slot-filling" and works "with fewer
  parameters than large language models". Neither is in the abstract. The LLM only sees the first
  400 characters of the abstract, so it filled in the rest from its own memory.
- **T01:** this time the agent picked a real survey, and the explanation fits the abstract.
  It mentions "tool integration", which the abstract does not say, but that is a small addition.
- **T01, T07, T12:** the explanation repeats the citation count, which the instructions forbid.
  The numbers are correct, so it is a broken rule, not a made-up fact.
- **T05:** calls the paper's study a "proposed approach"; it is really an empirical study. Small wording issue.
- **T06, T14:** the explanation says "after 2023" / "before 2020" while the limits were "from 2023" / "until 2020".
  The papers (2026, 2018) still fit. Wording only.
- **T08:** CodeXGLUE fits, but HumanEval ("Evaluating Large Language Models Trained on Code", 2021)
  would fit better. The agent takes the first good match, not the best one.
- **T13:** the year range was understood correctly ("2019 to 2021") thanks to the new `between` option.
- **T10, T12:** the first attempt of step 2 failed (the LLM kept using a tool called `json`); the
  automatic restart of step 2 saved both. T13 also had one `json` mistake but recovered by itself.


## Details

### T01 - after year + minimum citations (assignment example)

**Prompt:** Find a research paper about LLM agents for software engineering that was published after 2022 and has at least 100 citations. Explain why the paper is relevant and provide the source of the citation count.

- **Agent understood:** `topic: 'LLM agents software engineering' | year: 2023 or higher | citations: 100 or higher`
- **Searches:** ['LLM agents software engineering']
- **Paper:** [From LLMs to LLM-based Agents for Software Engineering: A Survey of Current, Challenges and Future](https://doi.org/10.48550/arxiv.2408.02479) - 2024, 366 citations
- **Citation source:** OpenAlex 'cited_by_count' (https://openalex.org/W4403370443), retrieved 2026-11-21

**Explanation by the agent:** The paper titled "From LLMs to LLM-based Agents for Software Engineering: A Survey of Current, Challenges and Future" provides a comprehensive overview of how large language models are being transformed into autonomous agents for software engineering tasks. It discusses existing applications such as code generation, vulnerability detection, and tool integration, while also highlighting the challenges and future research directions for LLM-based agents in this domain. This makes it highly relevant for understanding the state‑of‑the‑art in LLM agents applied to software engineering. The citation count (366) meets the required threshold of at least 100 citations, confirming its impact in the field.

**Uncertainty notes:** The term 'LLM agents' could refer to large language model agents in various domains, but we assume the software engineering context as requested. / Citation counts differ between databases. This one is from OpenAlex.

**Abstract from OpenAlex (to check the explanation against):** With the rise of large language models (LLMs), researchers are increasingly exploring their applications in var ious vertical domains, such as software engineering. LLMs have achieved remarkable success in areas including code generation and vulnerability detection. However, they also exhibit numerous limitations and shortcomings. LLM-based agents, a novel tech nology with the potential for Artificial General Intelligence (AGI), combine LLMs as the core for decision-making and action-taking, addressing some of the inherent limitations of LLMs such as lack of autonomy and self-improvement. Despite numerous studies and surveys exploring the possibility of using LLMs in software engineering, it lacks a clear distinction between LLMs and LLM based agents. It is still in its early stage for a unified standard and benchmarking to qualify an LLM solution as an LLM-based agent in its domain. In 

### T02 - before year + more than N citations (assignment example)

**Prompt:** Find a paper about retrieval-augmented generation published before 2021 with more than 500 citations. Summarize its contribution in 5-7 sentences.

- **Agent understood:** `topic: 'retrieval augmented generation' | year: 2020 or lower | citations: 501 or higher`
- **Searches:** ['retrieval augmented generation']
- **Paper:** [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://doi.org/10.48550/arxiv.2005.11401) - 2020, 10346 citations
- **Citation source:** OpenAlex 'cited_by_count' (https://openalex.org/W3027879771), retrieved 2026-11-21

**Explanation by the agent:** The paper introduces Retrieval‑Augmented Generation (RAG), a framework that combines a neural language model with an external document retriever. By first retrieving relevant passages from a large corpus and then conditioning the generator on these passages, the approach enables the model to produce more factual and up‑to‑date responses while providing provenance for the information used. The authors demonstrate that RAG outperforms purely parametric models on several knowledge‑intensive NLP tasks such as open‑domain question answering, fact verification, and slot‑filling. They also show that the system can be trained end‑to‑end, allowing the retriever and generator to be jointly optimized for the downstream task. Experiments reveal that RAG achieves state‑of‑the‑art results with fewer parameters than large language models that rely solely on stored knowledge. The work highlights the benefits of modularizing knowledge access, making the model more interpretable and easier to update with new information without retraining the entire network. Overall, this paper establishes a strong baseline for retrieval‑augmented generation and has become a foundational reference in the field.

**Uncertainty notes:** Citation counts differ between databases. This one is from OpenAlex.

**Abstract from OpenAlex (to check the explanation against):** Large pre-trained language models have been shown to store factual knowledge in their parameters, and achieve state-of-the-art results when fine-tuned on downstream NLP tasks. However, their ability to access and precisely manipulate knowledge is still limited, and hence on knowledge-intensive tasks, their performance lags behind task-specific architectures. Additionally, providing provenance for their decisions and updating their world knowledge remain open research problems. Pre-trained models with a differentiable access mechanism to explicit non-parametric memory can overcome this issue, but have so far been only investigated for extractive downstream tasks. We explore a general-purpose fine-tuning recipe for retrieval-augmented generation (RAG) -- models which combine pre-trained parametric and non-parametric memory for language generation. We introduce RAG models where the parametr

### T03 - vague year word 'recent', no citation limit (assignment example)

**Prompt:** Find a recent paper about AI agents using tools and explain whether it would be useful for someone building autonomous software agents.

- **Agent understood:** `topic: 'AI agents tools' | year: 2024 or higher | citations: any`
- **Searches:** ['AI agents tools']
- **Paper:** [Capability-Bound Authorization for AI Agent Tool Calls](https://doi.org/10.1109/mic.2026.3753356) - 2026, 0 citations
- **Citation source:** OpenAlex 'cited_by_count' (https://openalex.org/W7225999671), retrieved 2026-11-21

**Explanation by the agent:** The paper proposes a new authorization mechanism—capability tokens—that are attenuable and bound to each tool call made by an AI agent. It argues that traditional OAuth scopes are too coarse, covering all possible mutations an agent might perform, and are fixed before the agent knows which specific call it will make. By introducing call‑time‑bound tokens, the approach enables finer‑grained, dynamic permission control for tool usage. For someone building autonomous software agents, this work offers a concrete solution to safely manage and delegate tool access, helping to avoid over‑privileged permissions and to enforce security policies that adapt to the agent’s actual behavior at runtime.

**Uncertainty notes:** The term 'recent' is interpreted as from 2024 onward. / The abstract focuses on authorization; the paper may not address other aspects of tool integration such as API design, error handling, or performance, which the developer might also need to consider. / Citation counts differ between databases. This one is from OpenAlex.

**Abstract from OpenAlex (to check the explanation against):** OAuth 2.0 scopes authorize AI agent tool calls at the wrong grain: a scope like calendar.write covers every mutation an agent could ever make, is fixed at request time before the agent knows which specific call it will make, and cannot be narrowed by the holder before delegating to a sub-agent. We argue that capability tokens, i.e. attenuable, call-time-bound authorization primitives with 30-plus years of prior art in the capability-security literature, are the right fit for agent tool-call authorization, and that the existing OAuth 2.1 machinery (Token Exchange, RFC 8693; DPoP, RFC 9449; Transaction Tokens) already provides most of the mechanism needed to implement this without bespoke cryptography. We measure the cost of one concrete implementation across a nine-hop delegation chain and find that attenuation overhead is small and does not grow with chain depth; the dominant per-hop cos

### T04 - exact year + very high minimum citations

**Prompt:** Find a paper about deep residual learning for image recognition published in 2016 with at least 50000 citations.

- **Agent understood:** `topic: 'deep residual learning image recognition' | year: exactly 2016 | citations: 50000 or higher`
- **Searches:** ['deep residual learning image recognition']
- **Paper:** [Deep Residual Learning for Image Recognition](https://doi.org/10.1109/cvpr.2016.90) - 2016, 290606 citations
- **Citation source:** OpenAlex 'cited_by_count' (https://openalex.org/W2194775991), retrieved 2026-11-21

**Explanation by the agent:** The paper titled "Deep Residual Learning for Image Recognition" introduces a residual learning framework that facilitates training of very deep neural networks for image recognition tasks. It reformulates layers to learn residual functions relative to their inputs, addressing difficulties in training deeper models and providing extensive empirical evidence of its effectiveness.

**Uncertainty notes:** Citation counts differ between databases. This one is from OpenAlex.

**Abstract from OpenAlex (to check the explanation against):** Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions. We provide comprehensive empirical evidence showing that these residual networks are easier to optimize, and can gain accuracy from considerably increased depth. On the ImageNet dataset we evaluate residual nets with a depth of up to 152 layers - 8× deeper than VGG nets [40] but still having lower complexity. An ensemble of these residual nets achieves 3.57% error on the ImageNet test set. This result won the 1st place on the ILSVRC 2015 classification task. We also present analysis on CIFAR-10 with 100 and 1000 layers. The depth of representations is of central

### T05 - narrow topic + after year + minimum citations

**Prompt:** Find a paper about automated program repair with large language models published after 2021 with at least 50 citations.

- **Agent understood:** `topic: 'automated program repair large language models' | year: 2022 or higher | citations: 50 or higher`
- **Searches:** ['automated program repair large language models']
- **Paper:** [Automated Program Repair in the Era of Large Pre-trained Language Models](https://doi.org/10.1109/icse48619.2023.00129) - 2023, 887 citations
- **Citation source:** OpenAlex 'cited_by_count' (https://openalex.org/W4384345708), retrieved 2026-11-21

**Explanation by the agent:** The paper titled "Automated Program Repair in the Era of Large Pre-trained Language Models" directly addresses the use of large language models for automated program repair. It discusses the limitations of traditional and learning‑based APR techniques and proposes leveraging pre‑trained LLMs to generate more diverse and effective patches for software bugs. The abstract highlights the motivation, challenges, and the proposed approach, making it a strong match for the request for a recent, highly cited work on this topic.

**Uncertainty notes:** Citation counts differ between databases. This one is from OpenAlex.

**Abstract from OpenAlex (to check the explanation against):** Automated Program Repair (APR) aims to help developers automatically patch software bugs. However, current state-of-the-art traditional and learning-based APR techniques face the problem of limited patch variety, failing to fix complicated bugs. This is mainly due to the reliance on bug-fixing datasets to craft fix templates (traditional) or directly predict potential patches (learning-based). Large Pre-Trained Language Models (LLMs), trained using billions of text/code tokens, can potentially help avoid this issue. Very recently, researchers have directly leveraged LLMs for APR without relying on any bug-fixing datasets. Meanwhile, such existing work either failed to include state-of-the-art LLMs or was not evaluated on realistic datasets. Thus, the true power of modern LLMs on the important APR problem is yet to be revealed. In this work, we perform the first extensive study on directl

### T06 - narrow topic + maximum citations

**Prompt:** Find a paper about prompt injection attacks against LLM-integrated applications, published from 2023 onwards, with fewer than 50 citations.

- **Agent understood:** `topic: 'prompt injection attacks' | year: 2023 or higher | citations: 49 or lower`
- **Searches:** ['prompt injection attacks']
- **Paper:** [Rethinking Assessments of Prompt Injection Attacks](https://doi.org/10.18653/v1/2026.findings-acl.1191) - 2026, 3 citations
- **Citation source:** OpenAlex 'cited_by_count' (https://openalex.org/W7166796419), retrieved 2026-11-21

**Explanation by the agent:** The paper titled "Rethinking Assessments of Prompt Injection Attacks" investigates prompt injection attacks, which are a primary risk for applications that integrate large language models (LLMs). The abstract explains that existing evaluation frameworks are insufficient for real-world relevance and that the authors conduct an extensive assessment across multiple settings, including real-world applications. This directly addresses the security concerns of LLM‑integrated systems and fits the requested criteria (published after 2023, fewer than 50 citations).

**Uncertainty notes:** Citation counts differ between databases. This one is from OpenAlex.

**Abstract from OpenAlex (to check the explanation against):** Prompt injection attacks are recognized as one of the primary risks faced by LLM-integrated applications in recent years.However, common evaluation frameworks remain insufficient, lacking comprehensiveness and real-world relevance.To bridge this gap, we revisit the common evaluation framework and conduct an extensive evaluation across eight different evaluation settings, including 37 real-world applications, 185 injected tasks, 21 attack instructions, and a total of 143,745 queries.The evaluation highlights several findings.For example, real-world applications are more vulnerable to prompt injection attacks compared to those used in research settings.While complex attack instructions are more sophisticated, they are less effective than simple attack instructions.To uncover the root causes of these phenomena, we further investigate the model's internal representations during attacks, offe

### T07 - broad topic + approximate citations

**Prompt:** Find a paper about graph neural networks with roughly 1000 citations.

- **Agent understood:** `topic: 'graph neural networks' | year: any | citations: 800 to 1200`
- **Searches:** ['graph neural networks']
- **Paper:** [Benchmarking Graph Neural Networks](https://doi.org/10.48550/arxiv.2003.00982) - 2020, 1065 citations
- **Citation source:** OpenAlex 'cited_by_count' (https://openalex.org/W3007332492), retrieved 2026-11-21

**Explanation by the agent:** The paper titled "Benchmarking Graph Neural Networks" provides a comprehensive evaluation of many GNN architectures across a variety of tasks and datasets. It establishes standardized benchmarks, discusses performance trends, and highlights strengths and weaknesses of different methods, making it a foundational reference for researchers working with graph neural networks. With 1065 citations, it falls squarely within the requested citation range of roughly 1000 citations.

**Uncertainty notes:** Citation counts differ between databases. This one is from OpenAlex.

**Abstract from OpenAlex (to check the explanation against):** In the last few years, graph neural networks (GNNs) have become the standard toolkit for analyzing and learning from data on graphs. This emerging field has witnessed an extensive growth of promising techniques that have been applied with success to computer science, mathematics, biology, physics and chemistry. But for any successful field to become mainstream and reliable, benchmarks must be developed to quantify progress. This led us in March 2020 to release a benchmark framework that i) comprises of a diverse collection of mathematical and real-world graphs, ii) enables fair model comparison with the same parameter budget to identify key architectures, iii) has an open-source, easy-to-use and reproducible code infrastructure, and iv) is flexible for researchers to experiment with new theoretical ideas. As of December 2022, the GitHub repository has reached 2,000 stars and 380 forks, w

### T08 - narrow topic + since year (inclusive) + minimum citations

**Prompt:** Find a paper on benchmarks for evaluating code generation by large language models, published since 2021, with at least 200 citations.

- **Agent understood:** `topic: 'code generation benchmarks' | year: 2021 or higher | citations: 200 or higher`
- **Searches:** ['code generation benchmarks']
- **Paper:** [CodeXGLUE: A Machine Learning Benchmark Dataset for Code Understanding and Generation](https://doi.org/10.48550/arxiv.2102.04664) - 2021, 1947 citations
- **Citation source:** OpenAlex 'cited_by_count' (https://openalex.org/W3126675481), retrieved 2026-11-21

**Explanation by the agent:** CodeXGLUE is a comprehensive benchmark suite introduced to accelerate research on program understanding and generation. It aggregates a collection of ten tasks across fourteen datasets, many of which focus on code generation, providing a standardized platform for evaluating large language models on generating code. Its broad coverage and high citation count make it a key reference for assessing LLM code generation performance.

**Uncertainty notes:** Citation counts differ between databases. This one is from OpenAlex.

**Abstract from OpenAlex (to check the explanation against):** Benchmark datasets have a significant impact on accelerating research in programming language tasks. In this paper, we introduce CodeXGLUE, a benchmark dataset to foster machine learning research for program understanding and generation. CodeXGLUE includes a collection of 10 tasks across 14 datasets and a platform for model evaluation and comparison. CodeXGLUE also features three baseline systems, including the BERT-style, GPT-style, and Encoder-Decoder models, to make it easy for researchers to use the platform. The availability of such data and baselines can help the development and validation of new methods that can be applied to various program understanding and generation problems.

### T09 - no good paper exists (topic did not exist yet)

**Prompt:** Find a paper about LLM-based coding agents published before 2010 with at least 1000 citations.

- **Agent understood:** `topic: 'LLM coding agents' | year: 2009 or lower | citations: 1000 or higher`
- **Searches:** ['code generation language model', 'code generation language model 2009']
- **Paper:** none returned

**Explanation by the agent:** No paper meets all the criteria. The concept of large language models (LLMs) for code generation or coding agents emerged after 2010, and there are no pre‑2010 publications that discuss LLM‑based coding agents and have accumulated at least 1000 citations. Therefore, no suitable paper can be provided.

**Uncertainty notes:** The term 'LLM-based coding agents' is interpreted as software agents that use large language models for code generation, which aligns with a software company context. / 2 search(es) were tried; 10 paper(s) passed the year and citation limits.

### T10 - no good paper exists (impossible citation count)

**Prompt:** Find a paper about retrieval-augmented generation published in 2025 with more than 200000 citations.

- **Agent understood:** `topic: 'retrieval augmented generation' | year: exactly 2025 | citations: 200001 or higher`
- **Searches:** ['retrieval augmented generation', 'RAG', 'retrieval-augmented generation']
- **Paper:** none returned

**Explanation by the agent:** I could not find any paper that matches the request for a retrieval-augmented generation study published in 2025 with more than 200,000 citations. Given the citation threshold, it is highly unlikely that a paper from 2025 would have accumulated that many citations so far.

**Uncertainty notes:** 3 search(es) were tried; 0 paper(s) passed the year and citation limits.

### T11 - ambiguous request (unclear topic, no limits)

**Prompt:** Find me a good paper about transformers.

- **Agent understood:** `topic: 'transformer models' | year: any | citations: any`
- **Searches:** ['transformer models']
- **Paper:** [Transformer models: an introduction and catalog](https://doi.org/10.48550/arxiv.2302.07730) - 2023, 152 citations
- **Citation source:** OpenAlex 'cited_by_count' (https://openalex.org/W4321276130), retrieved 2026-11-21

**Explanation by the agent:** The paper titled "Transformer models: an introduction and catalog" offers a comprehensive yet accessible overview of the rapidly expanding family of Transformer-based foundation models. According to its abstract, the authors aim to provide a simple catalog and classification of the most popular Transformer models, along with an introduction to the key architectural components and concepts that define them. This makes it an excellent starting point for anyone looking to understand the variety of Transformer architectures, their design choices, and how they relate to one another, fulfilling the request for a good paper about transformers.

**Uncertainty notes:** Citation counts differ between databases. This one is from OpenAlex.

**Abstract from OpenAlex (to check the explanation against):** In the past few years we have seen the meteoric appearance of dozens of foundation models of the Transformer family, all of which have memorable and sometimes funny, but not self-explanatory, names. The goal of this paper is to offer a somewhat comprehensive but simple catalog and classification of the most popular Transformer models. The paper also includes an introduction to the most important aspects and innovations in Transformer models. Our catalog will include models that are trained using self-supervised learning (e.g., BERT or GPT3) as well as those that are further trained using a human-in-the-loop (e.g. the InstructGPT model used by ChatGPT).

### T12 - ambiguous request (vague words: recent, popular, agents)

**Prompt:** I need something recent and popular about agents.

- **Agent understood:** `topic: 'software agents' | year: 2024 or higher | citations: 100 or higher`
- **Searches:** ['software agents']
- **Paper:** [Demystifying LLM-Based Software Engineering Agents](https://doi.org/10.1145/3715754) - 2025, 1071 citations
- **Citation source:** OpenAlex 'cited_by_count' (https://openalex.org/W4411449940), retrieved 2026-11-21

**Explanation by the agent:** The paper titled "Demystifying LLM-Based Software Engineering Agents" provides a comprehensive overview of recent autonomous agents that use large language models to perform end‑to‑end software development tasks. It discusses how these agents are built, the tools they employ, and their impact on software engineering, making it a recent (2025) and highly cited (over 1000 citations) work that directly addresses the topic of software agents.

**Uncertainty notes:** The term "recent" is interpreted as from the year 2024 onward. / The term "popular" is interpreted as having at least 100 citations. / The word "agents" is taken to refer to software or AI agents relevant to a software company. / Citation counts differ between databases. This one is from OpenAlex.

**Abstract from OpenAlex (to check the explanation against):** Recent advancements in large language models (LLMs) have significantly advanced the automation of software development tasks, including code synthesis, program repair, and test generation. More recently, researchers and industry practitioners have developed various autonomous LLM agents to perform end-to-end software development tasks. These agents are equipped with the ability to use tools, run commands, observe feedback from the environment, and plan for future actions. However, the complexity of these agent-based approaches, together with the limited abilities of current LLMs, raises the following question: Do we really have to employ complex autonomous software agents? To attempt to answer this question, we build Agentless – an agentless approach to automatically resolve software development issues. Compared to the verbose and complex setup of agent-based approaches, Agentless employ

### T13 - year range (between two years) + minimum citations

**Prompt:** Find a paper about federated learning published between 2019 and 2021 with at least 300 citations.

- **Agent understood:** `topic: 'federated learning' | year: 2019 to 2021 | citations: 300 or higher`
- **Searches:** ['federated learning']
- **Paper:** [Model-Contrastive Federated Learning](https://doi.org/10.1109/cvpr46437.2021.01057) - 2021, 2467 citations
- **Citation source:** OpenAlex 'cited_by_count' (https://openalex.org/W3182158470), retrieved 2026-11-21

**Explanation by the agent:** The paper titled "Model-Contrastive Federated Learning" (2021) addresses a core challenge in federated learning: the heterogeneity of local data distributions across participating parties. It proposes a novel approach that leverages model-contrastive learning to improve performance on image datasets with deep learning models, aiming to better handle the variability among client data. This aligns directly with the user's request for a highly cited federated learning paper from 2019‑2021.

**Uncertainty notes:** Citation counts differ between databases. This one is from OpenAlex.

**Abstract from OpenAlex (to check the explanation against):** Federated learning enables multiple parties to collaboratively train a machine learning model without communicating their local data. A key challenge in federated learning is to handle the heterogeneity of local data distribution across parties. Although many studies have been proposed to address this challenge, we find that they fail to achieve high performance in image datasets with deep learning models. In this paper, we propose MOON: model-contrastive federated learning. MOON is a simple and effective federated learning framework. The key idea of MOON is to utilize the similarity between model representations to correct the local training of individual parties, i.e., conducting contrastive learning in model-level. Our extensive experiments show that MOON significantly outperforms the other state-of-the-art federated learning algorithms on various image classification tasks.

### T14 - until year (inclusive) + maximum citations

**Prompt:** Find a paper about automated code review published until 2020 with at most 100 citations.

- **Agent understood:** `topic: 'automated code review' | year: 2020 or lower | citations: 100 or lower`
- **Searches:** ['automated code review']
- **Paper:** [Diggit: Automated code review via software repository mining](https://doi.org/10.1109/saner.2018.8330261) - 2018, 18 citations
- **Citation source:** OpenAlex 'cited_by_count' (https://openalex.org/W2796146415), retrieved 2026-11-21

**Explanation by the agent:** The paper titled "Diggit: Automated code review via software repository mining" presents a tool that automatically generates code review comments by mining historical changes in software repositories. It focuses on providing design guidance for prospective code changes, describing the tool’s construction, tuning, and integration into an industrial development workflow. This directly addresses the topic of automated code review and meets the constraints of being published before 2020 with fewer than 100 citations.

**Uncertainty notes:** Citation counts differ between databases. This one is from OpenAlex.

**Abstract from OpenAlex (to check the explanation against):** We present Diggit, a tool to automatically generate code review comments, offering design guidance on prospective changes, based on insights gained from mining historical changes in source code repositories. We describe how the tool was built and tuned for use in practice as we integrated Diggit into the working processes of an industrial development team. We focus on the developer experience, the constraints that had to be met in adapting academic research to produce a tool that was useful to developers, and the effectiveness of the results in practice.
