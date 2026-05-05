import pandas as pd
import numpy as np
import tensorflow as tf
import pickle
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# =========================
# LOAD DATASET
# =========================

DATA_PATH = "../../data/static_data/static_data.csv"
df = pd.read_csv(DATA_PATH, header=None)

X = df.iloc[:, :-1].values    # 63 features (21 keypoints × 3)
y = df.iloc[:, -1].values    # labels

print("Dataset shape:", X.shape)

# =========================
# ENCODE LABELS
# =========================

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

num_classes = len(np.unique(y_encoded))
labels = label_encoder.classes_

print("Classes:", labels)

# =========================
# TRAIN / VALIDATION SPLIT
# =========================

X_train, X_val, y_train, y_val = train_test_split(
    X,
    y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded
)

# =========================
# BUILD ANN MODEL
# =========================

model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(64, activation="relu", input_shape=(63,)),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dense(num_classes, activation="softmax")
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# =========================
# EARLY STOPPING
# =========================

early_stop = tf.keras.callbacks.EarlyStopping(
    monitor="val_loss",
    patience=7,
    restore_best_weights=True
)

# =========================
# TRAIN MODEL
# =========================

history = model.fit(
    X_train,
    y_train,
    epochs=70,
    batch_size=32,
    validation_data=(X_val, y_val),
    callbacks=[early_stop]
)

# =========================
# MODEL EVALUATION
# =========================

y_pred_prob = model.predict(X_val)
y_pred = np.argmax(y_pred_prob, axis=1)

acc = accuracy_score(y_val, y_pred)
prec = precision_score(y_val, y_pred, average="weighted")
rec = recall_score(y_val, y_pred, average="weighted")
f1 = f1_score(y_val, y_pred, average="weighted")

cm = confusion_matrix(y_val, y_pred)

print("\nConfusion Matrix:\n")
print(cm)

print("\n===== MODEL PERFORMANCE =====")
print(f"Accuracy  : {acc:.4f}")
print(f"Precision : {prec:.4f}")
print(f"Recall    : {rec:.4f}")
print(f"F1-score  : {f1:.4f}")

print("\nClassification Report:\n")
print(classification_report(y_val, y_pred, target_names=labels))

# =========================
# CONFUSION MATRIX (CLEAN VIEW)
# =========================

cm = confusion_matrix(y_val, y_pred)

# Normalize
cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]

plt.figure(figsize=(9, 6))   # 🔥 bigger figure

ax = sns.heatmap(
    cm_norm,
    cmap="Greens",
    xticklabels=labels,
    yticklabels=labels,
    annot=False,
    cbar=True
)

ax.set_title("Normalized Confusion Matrix", fontsize=16, pad=20)
ax.set_xlabel("Predicted Label", fontsize=14, labelpad=20)
ax.set_ylabel("True Label", fontsize=14, labelpad=20)

# 🔥 Fix label visibility
ax.set_xticklabels(labels, rotation=90, fontsize=9)
ax.set_yticklabels(labels, rotation=0, fontsize=7.8)

# plt.subplots_adjust(top=0.25)  # 🔥 IMPORTANT: space for x labels
plt.tight_layout()
plt.show()

# =========================
# SAVE MODEL & LABEL ENCODER
# =========================

MODEL_PATH = "../../models/static_model.h5"
LABEL_PATH = "../../models/static_labels.pkl"

model.save(MODEL_PATH)
pickle.dump(label_encoder, open(LABEL_PATH, "wb"))

print("\n✅ Static gesture model trained & saved successfully")