# Autonomous Experimentation

$_{Yongtao}$ $_{Liu,}$
$_{liuy3@ornl.gov,}$ $_{youngtaoliu@gmail.com}$

$_{July}$ $_{2026}$

Autonomous experiments integrate artificial intelligence (AI) and machine learning (ML) for real-time data analysis, decision-making, optimization, and adaptation to enable experiments with minimal or no human intervention. Unlike automated experiments that follow a fixed script, autonomous experiments learn from each measurement and adjust subsequent steps accordingly.

In this chapter, we introduce ML-driven experiment workflows constructed with AEcroscopy for autonomous microscopy. The workflows in this chapter are grounded in the following papers:

1. **[Accelerating Structure-Property Relationship Discovery with Multimodal Machine Learning and Self-Driving Microscopy](https://arxiv.org/abs/2603.17028)**
   Gong, J. et al. *arXiv*, 2026.
   Combines autonomous microscopy with dual-novelty deep kernel learning and a dual variational autoencoder to uncover structure-property relationships in halide perovskite films via conductive AFM.

2. **[Beyond Optimization: Exploring Novelty Discovery in Autonomous Experiments](https://pubs.acs.org/doi/full/10.1021/acsnanoscienceau.5c00106)**
   *ACS Nanoscience Au*, 2025.
   Introduces INS2ANE, a framework that integrates novelty scoring with strategic sampling to discover unexpected phenomena in autonomous microscopy experiments, going beyond standard optimization targets.

3. **[Scientific Exploration with Expert Knowledge (SEEK) in Autonomous Scanning Probe Microscopy with Active Learning](https://pubs.rsc.org/en/content/articlehtml/2025/dd/d4dd00277f)**
   Pratiush, U. et al. *Digital Discovery*, 2025.
   Develops constrained active learning approaches that incorporate prior expert knowledge into deep kernel learning for more efficient and guided autonomous SPM exploration.

4. **[SANE: Strategic Autonomous Non-Smooth Exploration for Multiple Optima Discovery](https://pubs.rsc.org/en/content/articlehtml/2024/dd/d4dd00299g)**
   Biswas, A. et al. *Digital Discovery*, 2025.
   Presents a Bayesian optimization method with a cost-driven acquisition function and dynamic constraint gate for discovering multiple optimal regions in noisy, multimodal piezoresponse parameter spaces.

5. **[Curiosity Driven Exploration to Optimize Structure-Property Learning in Microscopy](https://pubs.rsc.org/en/content/articlehtml/2025/dd/d5dd00119f)**
   Vatsavai, A. et al. *Digital Discovery*, 2025.
   Introduces curiosity-driven algorithms with deep learning surrogate models to actively sample regions with unexplored structure-property correlations in ferroelectric materials.

6. **[Evolution of Ferroelectric Properties in SmxBi1–xFeO3 via Automated Piezoresponse Force Microscopy across Combinatorial Spread Libraries](https://pubs.acs.org/doi/abs/10.1021/acsnano.4c06380)**
   Raghavan, A. et al. *ACS Nano*, 2024.
   Applies automated PFM to combinatorial spread libraries, exploring the ferroelectric–antiferroelectric morphotropic phase boundary in SmxBi1–xFeO3 with quantitative, automated measurement protocols.

We also recommend visit **[DKGP](https://github.com/yongtaoliu/DKGP)** about deep kernel Gaussian Process, an open-source library combining deep neural networks with Gaussian Processes for uncertainty-aware regression and Bayesian optimization with active learning acquisition functions (Expected Improvement, UCB, Thompson Sampling).