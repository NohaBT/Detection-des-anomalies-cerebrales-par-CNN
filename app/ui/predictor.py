"""
predictor.py  —  NeuroDetect AI Engine
Fash katkhdm: pip install tf-keras opencv-python
"""
import os, sys, pickle
import numpy as np

_APP_DIR  = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(_APP_DIR, "best_model.keras")
ENC_PATH   = os.path.join(_APP_DIR, "label_encoder.pkl")
IMG_SIZE   = 224

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

_model   = None
_encoder = None
_classes  = ["glioma", "meningioma", "notumor", "pituitary"]

CLASS_INFO = {
    "glioma":     {"label":"Gliome",             "type":"Gliome (Glioblastome/Astrocytome)", "localisation":"Tissu glial cérébral",          "grade":"Grade II–IV (OMS)", "gravite":"Élevée",   "color":"#ff4d6d", "detected":True,  "recommendation":"Consultation neurochirurgicale urgente. Biopsie stéréotaxique et IRM de perfusion à envisager. Protocole Stupp (Temozolomide + Radiothérapie) si GBM confirmé."},
    "meningioma": {"label":"Méningiome",          "type":"Méningiome",                        "localisation":"Méninges (enveloppes cérébrales)","grade":"Grade I–II (OMS)", "gravite":"Modérée",  "color":"#fbbf24", "detected":True,  "recommendation":"Surveillance IRM régulière (6–12 mois). Si croissance : résection chirurgicale ou radiochirurgie stéréotaxique."},
    "pituitary":  {"label":"Tumeur hypophysaire", "type":"Adénome hypophysaire",              "localisation":"Glande hypophysaire",            "grade":"Généralement bénin","gravite":"Modérée",  "color":"#a78bfa", "detected":True,  "recommendation":"Bilan hormonal complet. Consultation endocrinologique et ophtalmologique. Traitement médicamenteux ou chirurgie trans-sphénoïdale."},
    "notumor":    {"label":"Aucune tumeur",        "type":"—",                                 "localisation":"—",                              "grade":"—",                "gravite":"Aucune",   "color":"#34d399", "detected":False, "recommendation":"Aucune tumeur détectée. Continuer le suivi médical selon les symptômes. Nouvelle IRM si aggravation."},
}


def _load():
    global _model, _encoder, _classes
    if _model is not None:
        return True, ""

    # essayer keras standalone (Python 3.13 compatible)
    try:
        import keras
        _model = keras.saving.load_model(MODEL_PATH)
        print("[NeuroDetect AI] Modele charge via keras [OK]")
    except Exception as e1:
        # essayer tensorflow.keras
        try:
            import tensorflow as tf
            _model = tf.keras.models.load_model(MODEL_PATH)
            print("[NeuroDetect AI] Modele charge via tensorflow.keras [OK]")
        except Exception as e2:
            return False, (
                f"Impossible de charger le modèle.\n\n"
                f"Lance cette commande dans le terminal :\n"
                f"pip install tensorflow\n\n"
                f"Détail : {e2}"
            )

    try:
        with open(ENC_PATH, "rb") as f:
            enc = pickle.load(f)
        _classes = list(enc.classes_)
        _encoder = enc
    except Exception:
        pass  # fallback classes déjà définis

    return True, ""


def _preprocess(path):
    try:
        import cv2
        img = cv2.imread(path)
        if img is None: raise ValueError(f"Image illisible : {path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    except ImportError:
        from PIL import Image
        img = np.array(Image.open(path).convert("RGB").resize((IMG_SIZE, IMG_SIZE)))
    return np.expand_dims(img.astype("float32") / 255.0, axis=0)


def predict(image_path):
    ok, err = _load()
    if not ok:
        return {"success": False, "error": err}
    try:
        img  = _preprocess(image_path)
        pred = _model.predict(img, verbose=0)
        idx  = int(np.argmax(pred))
        conf = float(np.max(pred))
        cls  = _classes[idx] if idx < len(_classes) else "notumor"
        info = CLASS_INFO.get(cls, CLASS_INFO["notumor"])
        all_probs = {c: round(float(pred[0][i])*100, 1)
                     for i, c in enumerate(_classes) if i < pred.shape[1]}
        return {"success": True, "error": None, "class_name": cls,
                "confidence": round(conf*100), "all_probs": all_probs, **info}
    except Exception as e:
        return {"success": False, "error": str(e)}


def warmup():
    ok, err = _load()
    if not ok:
        print(f"[NeuroDetect AI] {err}")
    return ok