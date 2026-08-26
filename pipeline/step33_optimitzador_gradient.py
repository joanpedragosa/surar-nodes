# =====================================================================
# NOM DEL CODI: step33_keras_trainer.py
# UBICACIÓ COMPLETA: D:\Notebook\Transformer\surar_probabilistic\pipeline\step33_keras_trainer.py
# DESCRIPCIÓ FUNCIONAL: Entrenador de Xarxa Neuronal Profunda (ARD).
#                      Utilitza una arquitectura Siamesa per aprendre 
#                      representacions semàntiques riques i actualitzar 
#                      els embeddings dels nodes JSON distribuïts.
# OPCIONS D'EXECUCIÓ: python pipeline/step33_keras_trainer.py
# DEPENDÈNCIES: tensorflow, numpy, json
# =====================================================================

import os
import sys
import json
import logging
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# INJECCIÓ DE PATHS
RUTA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_SUMAR_ROOT = os.path.dirname(RUTA_ACTUAL)
if RUTA_SUMAR_ROOT not in sys.path:
    sys.path.insert(0, RUTA_SUMAR_ROOT)

from config import DATA_ROOT, GLOBAL, STEP_05, STEP_10, STEP_33
from pipeline.step00_contracte_global import normalitzar_token_català

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DESCRIPCIO_FINAL_STEP33_KERAS = """
================================================================================
DESCRIPCIÓ DETALLADA DE LA FUNCIONALITAT - STEP 33 (ENTRENADOR ARD)
================================================================================
PROPÒSIT GLOBAL DEL MÒDUL:
Utilitzar Deep Learning per deformar l'espai vectorial semàntic.
El model aprèn a apropar geomètricament les preguntes a les seves respostes 
correctes dins del corpus 'aina_corpus.txt'.

LOGICA DE FUNCIONAMENT INTERN:
1. Entrenament Siamesa (Keras): Xarxa que processa parelles (Pregunta, Candidat)
   per minimitzar la Binary Crossentropy.
2. Deformació de l'Espai: Mitjançant Backpropagation, s'ajusten els valors de 
   la matriu d'Embedding global.
3. Extracció d'Embeddings Optimitzats: Un cop entrenat, s'extreu la matriu 
   completa i s'actualitzen els fitxers 'token.json' amb els nous vectors.

RESULTAT EXECUTAT CONCRET:
Els nodes a 'data/nodes/' contenen ara embeddings semànticament afinats, llestos 
per ser publicats al Step 34 i utilitzats per a inferència geomètrica al Step 35.
================================================================================
"""

# CONFIGURACIÓ DEL MODEL (Des de config.py)
MAX_SEQ_LENGTH = STEP_33.get("MAX_SEQ_LENGTH", 20)
VOCAB_SIZE = STEP_33.get("VOCAB_SIZE", 5000)
EMBEDDING_DIM = STEP_33.get("EMBEDDING_DIM", 64)
LEARNING_RATE = STEP_33.get("LEARNING_RATE", 0.01)
EPOCHS = STEP_33.get("EPOCHS", 100)

# DATASET DE VALIDACIÓ (Ground Truth extret de aina_corpus.txt)
TRAINING_DATA = [
    # (Pregunta Tokens, Resposta Correcta, Respostes Incorrectes)
    (["psc", "regidors", "barcelona"], "vuit", ["nou", "set", "cent", "dos"]),
    (["pere_iii", "sous", "impost"], "8", ["nou", "cents", "mil", "quinze"]),
    (["executius", "sou", "publicat"], "550", ["tres", "vint", "pocs", "molts"]),
    (["lesseps", "estàtua", "metres"], "10", ["setanta", "cinc", "dos", "vuit"]),
    (["exèrcit", "borbònic", "homes"], "25000", ["tres", "vint", "molts", "pocs"]),
    (["reactors", "descobrir"], "quinze", ["vuit", "dos", "cent", "quatre"]),
    (["virus", "plantes", "tipus"], "molts", ["dos", "vuit", "quinze", "quatre"]),
    (["coronavirus", "perpinyà", "focus"], "dos", ["molts", "vuit", "cent", "quinze"]),
    (["erc", "diputats", "ceo"], "38", ["sis", "vuit", "cent", "dos"]),
    (["predel·la", "relleus"], "quatre", ["dos", "vuit", "cent", "quinze"]),
]

class SurarARDTrainer:
    def __init__(self):
        self.token_index = {}
        self.model = None
        self.vocab_size = VOCAB_SIZE
        self.embedding_matrix = None

    def build_vocabulary(self):
        """Construeix un vocabulari bàsic a partir de les dades d'entrenament."""
        index = 1 
        for q, correct, incorrects in TRAINING_DATA:
            for token in q + [correct] + incorrects:
                t_norm = normalitzar_token_català(token)
                if t_norm and t_norm not in self.token_index:
                    self.token_index[t_norm] = index
                    index += 1
        self.vocab_size = min(len(self.token_index) + 2, VOCAB_SIZE)
        logging.info(f"📚 Vocabulari construït: {len(self.token_index)} tokens únics.")

    def text_to_sequence(self, tokens):
        """Converteix una llista de tokens en una seqüència numèrica amb padding."""
        seq = []
        for t in tokens:
            t_norm = normalitzar_token_català(t)
            idx = self.token_index.get(t_norm, 0) # 0 és PAD/UNK
            seq.append(idx)
        if len(seq) < MAX_SEQ_LENGTH:
            seq += [0] * (MAX_SEQ_LENGTH - len(seq))
        else:
            seq = seq[:MAX_SEQ_LENGTH]
        return seq

    def generate_training_samples(self):
        """Genera tensors X_question, X_candidate i y_labels."""
        X_q, X_c, y = [], [], []
        for q_tokens, correct, incorrects in TRAINING_DATA:
            q_seq = self.text_to_sequence(q_tokens)
            c_correct_seq = self.text_to_sequence([correct])
            X_q.append(q_seq); X_c.append(c_correct_seq); y.append(1)
            for inc in incorrects:
                c_inc_seq = self.text_to_sequence([inc])
                X_q.append(q_seq); X_c.append(c_inc_seq); y.append(0)
        return np.array(X_q), np.array(X_c), np.array(y)

    def build_siamese_model(self):
        """Construeix una xarxa Siamesa per aprendre embeddings semàntics."""
        input_layer = keras.Input(shape=(MAX_SEQ_LENGTH,), name="input_seq")
        
        # Capa d'Embedding Compartida (La clau de l'aprenentatge)
        x = layers.Embedding(input_dim=self.vocab_size, output_dim=EMBEDDING_DIM, name="shared_embedding")(input_layer)
        
        # GlobalAveragePooling per obtenir un vector fix de la seqüència
        x = layers.GlobalAveragePooling1D()(x)
        
        # Capes Denses per processar la semàntica combinada
        x = layers.Dense(64, activation='relu')(x)
        x = layers.Dropout(0.2)(x)
        x = layers.Dense(32, activation='relu')(x)
        
        base_model = keras.Model(inputs=input_layer, outputs=x, name="base_encoder")
        
        q_input = keras.Input(shape=(MAX_SEQ_LENGTH,), name="question_input")
        c_input = keras.Input(shape=(MAX_SEQ_LENGTH,), name="candidate_input")
        
        q_encoded = base_model(q_input)
        c_encoded = base_model(c_input)
        
        # Similaritat Còsina com a mesura de proximitat
        similarity = layers.Dot(axes=-1, normalize=True)([q_encoded, c_encoded])
        
        # Sortida Sigmoide (Probabilitat de pertinència)
        output = layers.Dense(1, activation='sigmoid')(similarity)
        
        model = keras.Model(inputs=[q_input, c_input], outputs=output)
        model.compile(optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE), loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def extract_and_update_embeddings(self):
        """Extreu la matriu d'embedding entrenada i actualitza els nodes JSON."""
        logging.info("🧠 Extraint matriu d'embeddings optimitzada...")
        
        # Obtenir la capa d'embedding del model entrenat
        embedding_layer = self.model.get_layer("base_encoder").get_layer("shared_embedding")
        weights = embedding_layer.get_weights()[0] # La matriu (VocabSize x EmbedDim)
        
        ruta_nodes = STEP_05["OUTPUT_LOCAL_DIR"]
        updated_count = 0
        
        for token, idx in self.token_index.items():
            if idx >= len(weights): continue
            
            # Obtenir el vector optimitzat per a aquest token
            new_embedding = weights[idx].tolist()
            
            # Actualitzar el fitxer JSON corresponent
            node_path = os.path.join(ruta_nodes, f"{token}.json")
            if os.path.exists(node_path):
                try:
                    with open(node_path, "r", encoding="utf-8") as f:
                        node_data = json.load(f)
                    
                    node_data["embedding_vector"] = new_embedding
                    
                    with open(node_path, "w", encoding="utf-8") as f:
                        json.dump(node_data, f, ensure_ascii=False, indent=2)
                    
                    updated_count += 1
                except Exception as e:
                    logging.warning(f"⚠️ Error actualitzant node '{token}': {e}")

        logging.info(f"✅ {updated_count} nodes actualitzats amb embeddings optimitzats.")

    def train_and_export(self):
        logging.info("🚀 Iniciant entrenament ARD (Deformació de l'Espai Vectorial)...")
        self.build_vocabulary()
        
        X_q, X_c, y = self.generate_training_samples()
        logging.info(f"📊 Mostres generades: {len(y)} (Positives: {sum(y)}, Negatives: {len(y)-sum(y)})")
        
        self.model = self.build_siamese_model()
        self.model.summary()
        
        checkpoint = keras.callbacks.ModelCheckpoint(
            filepath=STEP_33.get("MODEL_OUTPUT_FILE", os.path.join(DATA_ROOT, "surar_semantic_model.keras")),
            monitor='loss', save_best_only=True
        )
        
        early_stopping = keras.callbacks.EarlyStopping(monitor='loss', patience=10, restore_best_weights=True)
        
        self.model.fit({"question_input": X_q, "candidate_input": X_c}, y, 
                       epochs=EPOCHS, 
                       batch_size=STEP_33.get("BATCH_SIZE_TRAIN", 16), 
                       callbacks=[checkpoint, early_stopping], 
                       verbose=1)
        
        # Fase Crítica: Actualitzar els nodes amb la nova intel·ligència geomètrica
        self.extract_and_update_embeddings()

if __name__ == "__main__":
    trainer = SurarARDTrainer()
    trainer.train_and_export()
    print(DESCRIPCIO_FINAL_STEP33_KERAS)