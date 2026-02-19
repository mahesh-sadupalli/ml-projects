# ML Projects

A collection of applied machine learning projects spanning healthcare, anomaly detection, and data analytics.

## Projects

### [Multimodal MedSat](multimodal-medsat/)
Multimodal deep learning model for predicting medical prescription prevalence across England. Proposes a two-branch architecture — CNN/ViT for Sentinel-2 satellite imagery (10 spectral bands) and MLP for sociodemographic + environmental tabular data — fused via cross-attention. Built on the MedSat dataset (NeurIPS 2023) covering 33,755 regions and 6 prescription types (diabetes, hypertension, asthma, depression, anxiety, opioids). Satellite image preprocessing pipeline completed.

### [Anomaly Detection](anomaly-detection/)
Unsupervised anomaly detection on the UCI Wholesale Customers dataset using two independent approaches developed at FU Berlin and BTU Cottbus-Senftenberg. Compares softmin scoring with bootstrapped gamma selection and LRP explainability (FU Berlin) against PCA + One-Class SVM (BTU), with a side-by-side analysis of both methodologies.

### [Automotive Dashboard](automotive-dashboard/)
Sales analytics dashboard for the automotive industry analyzing €7.67M in revenue across 6 months. Built with Power BI and Python, covering model performance, regional market share (Germany, USA, China, UK), sales channel effectiveness, lead conversion analysis, and customer segmentation with strategic recommendations.

## License

[MIT](LICENSE)
