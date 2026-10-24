# Original demonstration notes: machine learning

These short original notes exist to test the pipeline without distributing copyrighted books. They are not a replacement for the assignment's primary textbook. Upload a provided textbook before recording the final RAG demonstration.

## Generalization and overfitting
A learner fits patterns on training examples, but its goal is performance on previously unseen examples. Overfitting occurs when a flexible hypothesis captures training noise. A widening gap between training and validation error can indicate overfitting. Regularization penalizes complexity, while collecting representative data can reduce variance. Increasing model complexity can lower bias while increasing variance. Learning curves help distinguish insufficient capacity from insufficient data. Evaluate the final model on a held-out test set that was not used to select hyperparameters.

## Training, validation and data leakage
Separate training, validation and testing responsibilities. Fit preprocessing, feature selection and normalization on the training split only. When multiple records refer to one patient or user, group-based splitting prevents information crossing partitions. Time series require chronological splits. Using future observations to engineer features creates leakage. Cross-validation estimates variation across splits, but repeatedly selecting configurations against a test set makes that test set part of training decisions. Pipelines help enforce consistent fit and transform behavior.

## Classification and evaluation
Precision measures the fraction of predicted positives that are correct; recall measures the fraction of actual positives detected. A fraud detector can miss costly fraud when recall is low, while excessive false alarms burden reviewers when precision is low. Threshold selection changes their tradeoff. Accuracy can be misleading when classes are imbalanced. Compare a model to a simple baseline, inspect the confusion matrix and use a metric appropriate to the cost of errors. Calibration concerns whether predicted probabilities match observed frequencies.

## Feature engineering and regularization
Features encode relevant information for a model. Categorical values can use one-hot encoding, while numerical features may require scaling for distance-based or penalized models. Missing-value imputation must be learned from training data. L1 penalties encourage sparse coefficients, while L2 penalties shrink coefficients smoothly. Tune regularization strength using validation performance. Correlated features can destabilize interpretation. Feature importance alone does not establish a causal relationship, and unstable features can fail under distribution shifts.

## Deployment and monitoring
Offline evaluation should reflect how the model is used. Monitor input drift, delayed labels, prediction distributions and service latency. Compare a new model against the baseline before rolling it out. Record model versions and preprocessing artifacts together to avoid training-serving skew. A rollback plan and representative test data make model deployment easier to debug. Logging only aggregate metrics can hide subgroup failures. Evaluate known operational segments while avoiding unsupported assumptions about individual candidates or users.
