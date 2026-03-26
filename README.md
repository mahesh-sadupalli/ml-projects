<div align="center">

# ML Projects

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c?logo=pytorch&logoColor=white)](https://pytorch.org)

**A collection of applied machine learning projects spanning scientific computing, healthcare, anomaly detection, data analytics, and AI systems.**

</div>

---

## Projects

### [Fourier Neural Operator for Dynamical Systems](fno-dynamical-system/)

<table>
<tr>
<td width="55%">

Training a **Fourier Neural Operator (FNO)** to approximate an unknown 1D dynamical system purely from snapshot data. Demonstrates resolution-invariant operator learning, time-conditioned prediction, and transfer learning across distribution shifts.

**Highlights:**
- Resolution invariance: same weights work on 32 to 128 point grids
- Time-conditioned all-to-all prediction across full temporal horizon
- Transfer learning with only 32 trajectories reduces error by 44%

`PyTorch` `Neural Operators` `Scientific ML` `ETH Zurich`

</td>
<td width="45%">

<img src="fno-dynamical-system/figures/08_ground_truth_3d_sample1.png" width="100%" alt="FNO 3D surface"/>

</td>
</tr>
</table>

<details>
<summary>Results Summary</summary>
<br/>

| Task | Description | Relative L² Error |
|:---|:---|:---:|
| One-to-One | u₀ → u(t=1.0) | 0.1203 |
| Multi-Resolution | Same weights, 32→128 grids | 0.12 — 0.15 |
| All-to-All | Time-conditioned, t=0.25→1.0 | 0.05 — 0.16 |
| Fine-Tuning | 32 trajectories, unknown dist. | 0.2255 |

<img src="fno-dynamical-system/figures/07_summary_dashboard.png" width="90%" alt="FNO results dashboard"/>

</details>

---

### [Enterprise Document Intelligence](enterprise-doc-intel/)

Intelligent document platform combining RAG pipelines, Knowledge Graphs, and Agentic Workflows — built from scratch without LangChain. Ingests enterprise documents (policies, technical docs, reports), builds structured knowledge in Neo4j, and answers complex multi-step questions via a ReAct agent with hybrid vector + graph retrieval. Powered by Ollama (local LLMs), ChromaDB, Neo4j, and FastAPI.

`RAG` `Knowledge Graphs` `Neo4j` `ReAct Agent`

---

### [Multimodal MedSat](multimodal-medsat/)

Multimodal deep learning model for predicting medical prescription prevalence across England. Proposes a two-branch architecture — CNN/ViT for Sentinel-2 satellite imagery (10 spectral bands) and MLP for sociodemographic + environmental tabular data — fused via cross-attention. Built on the MedSat dataset (NeurIPS 2023) covering 33,755 regions and 6 prescription types.

`Multimodal Learning` `Satellite Imagery` `Healthcare` `Cross-Attention`

---

### [Anomaly Detection](anomaly-detection/)

Unsupervised anomaly detection on the UCI Wholesale Customers dataset using two independent approaches developed at FU Berlin and BTU Cottbus-Senftenberg. Compares softmin scoring with bootstrapped gamma selection and LRP explainability (FU Berlin) against PCA + One-Class SVM (BTU), with a side-by-side analysis of both methodologies.

`Unsupervised Learning` `PCA` `One-Class SVM` `LRP Explainability`

---

### [Automotive Dashboard](automotive-dashboard/)

Sales analytics dashboard for the automotive industry analyzing €7.67M in revenue across 6 months. Built with Power BI and Python, covering model performance, regional market share (Germany, USA, China, UK), sales channel effectiveness, lead conversion analysis, and customer segmentation with strategic recommendations.

`Power BI` `Data Analytics` `Business Intelligence`

---

## License

[MIT](LICENSE)
