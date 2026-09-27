import sys
import os
from src import config
from model_loader import ModelLoader

def test_all_models():
    loader = ModelLoader()
    print(f"Registry: {loader.registry}")

    trained_models = loader.registry.get('trained_models', {})

    for model_name, status in trained_models.items():
        if status == "ACTIVE":
            print(f"\n--- Testing ACTIVE model: {model_name} ---")
            try:
                model = loader.load_model(model_name)
                if model is not None:
                    print(f"SUCCESS: Successfully loaded {model_name}")
                else:
                    print(f"FAILED: Failed to load {model_name}: load_model returned None (missing files?)")
            except Exception as e:
                print(f"FAILED: Failed to load {model_name} with Exception: {e}")
        else:
            print(f"\n--- Skipping {status} model: {model_name} ---")

if __name__ == '__main__':
    test_all_models()
