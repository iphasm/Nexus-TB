#!/usr/bin/env python3
"""
Análisis del rendimiento actual del modelo ML
"""

import joblib
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

def analyze_current_model():
    """Analizar el rendimiento actual del modelo ML"""
    print('=== ANÁLISIS DEL MODELO ML ACTUAL ===')

    try:
        # Cargar modelo actual
        model_data = joblib.load('nexus_system/memory_archives/ml_model.pkl')
        scaler = joblib.load('nexus_system/memory_archives/scaler.pkl')

        if isinstance(model_data, dict):
            model = model_data.get('model')
            metadata = model_data.get('metadata', {})

            print(f'Modelo: {metadata.get("version", "desconocido")}')
            accuracy = metadata.get("accuracy")
            cv_score = metadata.get("cv_score")
            if accuracy:
                print('.1%')
            else:
                print(f'Accuracy reportado: {accuracy}')

            if cv_score:
                print('.1%')
            else:
                print(f'CV Score: {cv_score}')
            print(f'Símbolos entrenados: {len(metadata.get("symbols", []))}')
            print(f'Muestras de entrenamiento: {metadata.get("total_samples", "N/A")}')

            # Verificar importancia de features
            if hasattr(model, 'feature_importances_'):
                print('\nTop 10 features más importantes:')
                features = model_data.get('feature_names', [])
                importances = model.feature_importances_
                if len(features) == len(importances):
                    sorted_idx = np.argsort(importances)[::-1]
                    for i, idx in enumerate(sorted_idx[:10]):
                        print(f'{i+1:2d}. {features[idx]:25} {importances[idx]:.4f}')

            print('\n=== CLASES DEL MODELO ===')
            label_encoder = model_data.get('label_encoder')
            if label_encoder and hasattr(label_encoder, 'classes_'):
                for i, class_name in enumerate(label_encoder.classes_):
                    print(f'{i}: {class_name}')

        else:
            print('Modelo en formato legacy')

    except Exception as e:
        print(f'Error analizando modelo: {e}')
        import traceback
        traceback.print_exc()

def propose_improvements():
    """Proponer mejoras específicas para aumentar accuracy"""
    print('\n' + '='*50)
    print('🚀 PROPUESTAS PARA MEJORAR ACCURACY DEL MODELO ML')
    print('='*50)

    print('\n1. 📊 EXPANSIÓN DE DATASET:')
    print('   • Más datos históricos (6-12 meses mínimo)')
    print('   • Condiciones de mercado variadas (bull, bear, sideways)')
    print('   • Diferentes pares de trading (más allá de USDT)')
    print('   • Datos de diferentes exchanges para robustez')

    print('\n2. 🛠️ FEATURES ENGINEERING AVANZADO:')
    print('   • Sentiment Analysis (News, Social Media)')
    print('   • Order Flow & Volume Analysis')
    print('   • Inter-market correlations (BTC vs Altcoins)')
    print('   • Economic indicators (interés, inflación)')
    print('   • Features temporales avanzados')

    print('\n3. 🎯 HIPERPARÁMETROS OPTIMIZADOS:')
    print('   • Grid Search con validación cruzada')
    print('   • Bayesian Optimization')
    print('   • Early stopping automático')

    print('\n4. 🔄 VALIDACIÓN TEMPORAL:')
    print('   • TimeSeriesSplit en lugar de KFold')
    print('   • Walk-forward validation')
    print('   • Out-of-sample testing robusto')

    print('\n5. 🎪 ENSEMBLE METHODS:')
    print('   • Random Forest + XGBoost + LightGBM')
    print('   • Voting Classifier')
    print('   • Stacking con meta-learner')

    print('\n6. 📈 FEATURE SELECTION:')
    print('   • Recursive Feature Elimination (RFE)')
    print('   • Feature importance analysis')
    print('   • Correlation-based selection')

    print('\n7. 🎨 DATA AUGMENTATION:')
    print('   • Synthetic data generation')
    print('   • Noise injection')
    print('   • Time series augmentation')

if __name__ == "__main__":
    analyze_current_model()
    propose_improvements()
